#!/usr/bin/env python3
"""
招商银行信用卡每日交易解析工具 v1.0
解析"每日信用管家"邮件，生成每日账单分析报告到 Obsidian
支持：
- 单日/多日交易汇总
- 外币自动转 CNY
- 智能消费分类
- Dataview 动态计算
"""

import json
import subprocess
import base64
import re
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# 导入公共模块
import sys
sys.path.insert(0, str(Path(__file__).parent))

# 使用 importlib 导入带连字符的模块
import importlib.util
spec = importlib.util.spec_from_file_location("cmb_common", Path(__file__).parent / "cmb_common.py")
cmb_common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmb_common)

CATEGORY_KEYWORDS = cmb_common.CATEGORY_KEYWORDS
identify_refund_status = cmb_common.identify_refund_status
categorize_transaction = cmb_common.categorize_transaction
convert_to_cny = cmb_common.convert_to_cny
format_currency = cmb_common.format_currency

# ============ 配置 ============
DEFAULT_CONFIG = {
    "gmail_query": "(from:招商银行 OR from:cmbchina.com) subject:每日信用管家 newer_than:{days}d",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",
}


def run_gws(api_path: str, params: Dict) -> Dict:
    """调用 gws 命令"""
    cmd = ["gws"] + api_path.split() + ["--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"gws 命令失败：{result.stderr}")
    return json.loads(result.stdout)


def extract_email_body(payload: Dict) -> Optional[str]:
    """递归提取邮件 HTML 正文"""
    def find_html_parts(part, results=None):
        if results is None:
            results = []

        if 'parts' in part:
            for p in part['parts']:
                find_html_parts(p, results)

        if part.get('mimeType') == 'text/html':
            body = part.get('body', {})
            if body.get('data'):
                html = base64.urlsafe_b64decode(body['data']).decode('utf-8', errors='ignore')
                results.append(html)

        return results

    html_parts = find_html_parts(payload)
    return html_parts[0] if html_parts else None


def parse_daily_email(html: str) -> Dict:
    """
    解析每日信用管家邮件
    提取：日期、交易列表（时间、卡号、金额、币种、类型、商户）
    """
    data = {
        "date": None,
        "transactions": []
    }

    # 1. 提取账单日期：2026/03/14 您的消费明细如下
    date_match = re.search(r'(\d{4}/\d{2}/\d{2}).*?消费明细', html)
    if date_match:
        data["date"] = date_match.group(1).replace('/', '-')

    # 2. 清理 HTML，提取文字内容
    # 先替换 &nbsp; 为空格
    html = html.replace('&nbsp;', ' ')
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)

    # 3. 提取交易记录
    # 格式：HH:MM:SS CNY 3.00 尾号 2693 消费 支付宝 - 北京鸿易博科技有限公司
    # 正则表达式：时间 + 币种 + 金额 + 尾号 + 类型 + 商户
    pattern = r'(\d{2}:\d{2}:\d{2})\s*(CNY|USD|HKD)\s*([\d,]+\.\d{2})\s*尾号\s*(\d+)\s*(消费 | 邮购 | 退款 | 退货)\s*(.+?)(?=\d{2}:\d{2}:\d{2}|$)'

    matches = re.findall(pattern, text, re.IGNORECASE)

    for m in matches:
        time_str = m[0]
        currency = m[1].upper()
        amount_str = m[2].replace(',', '')
        card = m[3]
        trans_type = m[4]
        merchant = m[5].strip()

        amount = float(amount_str)

        # 如果是退款/退货，金额为负
        if trans_type in ["退款", "退货"]:
            amount = -amount

        # 转换为 CNY
        amount_cny = convert_to_cny(amount, currency)

        data["transactions"].append({
            "time": time_str,
            "card": card,
            "amount": amount,
            "currency": currency,
            "amount_cny": amount_cny,
            "type": trans_type,
            "description": merchant,
            "merchant": merchant
        })

    return data


def generate_report(data: Dict, days: int, source_info: str) -> str:
    """生成 Markdown 分析报告"""
    report = f"# 招商银行信用卡日账单\n\n"
    report += f"**账单日期**: {data['date'] or 'N/A'}\n"
    report += f"**统计周期**: 最近 {days} 天\n"
    report += f"**数据来源**: {source_info}\n"
    report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**币种说明**: 外币交易已按汇率转换为 CNY\n\n"

    report += "---\n\n"

    # 交易汇总
    report += "## 📊 交易汇总\n\n"

    # 按卡号统计
    card_stats = defaultdict(lambda: {"count": 0, "spending": 0, "refund": 0, "net": 0})

    for trans in data["transactions"]:
        card = trans["card"]
        amount = trans.get("amount_cny", trans["amount"])
        card_stats[card]["count"] += 1
        if amount > 0:
            card_stats[card]["spending"] += amount
        else:
            card_stats[card]["refund"] += amount
        card_stats[card]["net"] += amount

    report += "| 卡号 | 交易笔数 | 消费金额 | 退款金额 | 净消费 |\n"
    report += "|------|---------|---------|---------|--------|\n"

    for card in sorted(card_stats.keys()):
        stats = card_stats[card]
        report += f"| {card} | {stats['count']} | ¥ {stats['spending']:,.2f} | ¥ {stats['refund']:,.2f} | ¥ {stats['net']:,.2f} |\n"

    total_spending = sum(s["spending"] for s in card_stats.values())
    total_refund = sum(s["refund"] for s in card_stats.values())
    total_net = sum(s["net"] for s in card_stats.values())
    total_count = sum(s["count"] for s in card_stats.values())

    report += f"\n**合计**: 总交易 {total_count} 笔 | 总消费 ¥ {total_spending:,.2f} | 总退款 ¥ {total_refund:,.2f} | 净消费 ¥ {total_net:,.2f}\n\n"

    # 消费分类统计
    report += "## 💰 消费分类统计\n\n"

    # 对交易进行分类
    categorized = defaultdict(list)
    for trans in data["transactions"]:
        desc = trans.get("description", trans.get("merchant", ""))
        amount = trans.get("amount_cny", trans["amount"])
        # 只统计正向消费
        if amount > 0:
            category = categorize_transaction(desc, amount)
            categorized[category].append(trans)

    # 按金额倒序排序，"其他" 放最后
    sorted_categories = sorted(
        [(cat, trans_list) for cat, trans_list in categorized.items() if trans_list and cat != "其他"],
        key=lambda x: sum(t.get("amount_cny", t["amount"]) for t in x[1]),
        reverse=True
    )
    if categorized.get("其他"):
        sorted_categories.append(("其他", categorized["其他"]))

    report += "| 分类 | 笔数 | 金额 | 占比 |\n"
    report += "|------|------|------|------|\n"

    for category, trans_list in sorted_categories:
        count = len(trans_list)
        amount = sum(t.get("amount_cny", t["amount"]) for t in trans_list)
        percentage = (amount / total_spending * 100) if total_spending > 0 else 0
        report += f"| {category} | {count} | ¥ {amount:,.2f} | {percentage:.1f}% |\n"

    report += "\n---\n\n"

    # 交易明细
    report += "## 📝 交易明细\n\n"

    # 按卡号分组显示
    transactions_by_card = defaultdict(list)
    for trans in data["transactions"]:
        transactions_by_card[trans["card"]].append(trans)

    for card in sorted(transactions_by_card.keys()):
        report += f"### 卡号 {card}\n\n"
        report += "| 时间 | 商户 | 金额 (原币) | 金额 (CNY) | 类型 | 分类 |\n"
        report += "|------|------|------------|-----------|------|------|\n"

        for trans in sorted(transactions_by_card[card], key=lambda x: x["time"]):
            desc = trans.get("description", trans.get("merchant", ""))
            amount_cny = trans.get("amount_cny", trans["amount"])
            category = categorize_transaction(desc, amount_cny) if amount_cny > 0 else "-"

            report += f"| {trans['time']} | {desc} | {format_currency(trans['amount'], trans['currency'])} | ¥ {amount_cny:,.2f} | {trans['type']} | {category} |\n"

        report += "\n"

    # 消费建议
    report += "## 💡 消费建议\n\n"

    if categorized:
        max_category = max(categorized.items(), key=lambda x: sum(t.get("amount_cny", t["amount"]) for t in x[1]) if x[1] else 0)
        if max_category[1]:
            cat_name = max_category[0]
            cat_amount = sum(t.get("amount_cny", t["amount"]) for t in max_category[1])
            report += f"📊 本期 **{cat_name}** 消费最多，共 ¥ {cat_amount:,.2f}"
            if total_spending > 0:
                report += f"，占总消费的 {(cat_amount/total_spending*100):.1f}%"
            report += "\n\n"

    report += "*本报告由自动化工具生成 | 数据来源：招商银行每日信用管家邮件*\n"

    return report


def save_to_obsidian(report: str, date_str: str, output_dir: Path) -> Path:
    """保存报告到 Obsidian"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 文件格式：YYYYMMDD-信用卡日账单.md
    filename = f"{date_str.replace('-', '')}-信用卡日账单.md"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 报告已保存：{output_path}")
    return output_path


def main():
    """主流程"""
    parser = argparse.ArgumentParser(description="招商银行信用卡每日交易解析工具")
    parser.add_argument("--days", "-d", type=int, default=1, help="拉取最近 N 天的交易 (默认：1)")
    parser.add_argument("--date", type=str, help="指定日期 (格式：YYYY-MM-DD，与 days 互斥)")
    parser.add_argument("--output-dir", "-o", type=str, help="自定义输出目录")
    parser.add_argument("--query", "-q", type=str, help="自定义 Gmail 查询条件")

    args = parser.parse_args()

    # 验证参数
    if args.date and args.days != 1:
        print("❌ --date 和 --days 不能同时使用")
        return

    # 计算天数
    if args.date:
        # 指定日期：计算从该日期到现在的天数
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d")
            days_diff = (datetime.now() - target_date).days + 1
            days = max(1, min(days_diff, 30))  # 最多 30 天
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
            return
    else:
        days = args.days

    # 配置
    obsidian_dir = Path(args.output_dir) if args.output_dir else DEFAULT_CONFIG["obsidian_dir"]
    gmail_query = args.query if args.query else DEFAULT_CONFIG["gmail_query"].format(days=days)

    try:
        # 1. 从 Gmail 获取邮件
        print(f"🔍 查询 Gmail 中的每日信用管家邮件（最近{days}天）...")

        result = run_gws("gmail users messages list", {
            "userId": "me",
            "q": gmail_query,
            "maxResults": days * 2  # 每天可能有多封，适当多拉一些
        })

        messages = result.get("messages", [])
        if not messages:
            print("❌ 未找到每日信用管家邮件")
            return

        print(f"✅ 找到 {len(messages)} 封邮件")

        # 2. 解析所有邮件
        all_data = {
            "date": None,
            "transactions": []
        }

        for msg in messages:
            msg_id = msg["id"]

            # 获取邮件详情
            msg_data = run_gws("gmail users messages get", {
                "userId": "me",
                "id": msg_id
            })

            # 提取 HTML 正文
            html_body = extract_email_body(msg_data['payload'])
            if not html_body:
                print(f"⚠️  无法提取邮件 {msg_id} 正文，跳过")
                continue

            # 解析邮件
            data = parse_daily_email(html_body)
            if data["date"]:
                if all_data["date"] is None or data["date"] > all_data["date"]:
                    all_data["date"] = data["date"]
            all_data["transactions"].extend(data["transactions"])

        if not all_data["transactions"]:
            print("⚠️  未找到交易记录")
            return

        print(f"✅ 解析完成：共 {len(all_data['transactions'])} 笔交易")

        # 3. 生成报告
        source_info = f"每日信用管家邮件（最近{days}天）"
        report = generate_report(all_data, days, source_info)

        # 4. 确定输出日期
        if args.date:
            output_date = args.date
        else:
            output_date = all_data["date"] or datetime.now().strftime("%Y-%m-%d")

        # 5. 保存到 Obsidian
        output_path = save_to_obsidian(report, output_date, obsidian_dir)

        # 6. 统计信息
        total_spending = sum(t.get("amount_cny", t["amount"]) for t in all_data["transactions"] if t.get("amount_cny", t["amount"]) > 0)
        refund_count = sum(1 for t in all_data["transactions"] if t.get("amount_cny", t["amount"]) < 0)
        unique_cards = len(set(t["card"] for t in all_data["transactions"]))

        print("\n" + "="*60)
        print("✅ 每日账单分析完成！")
        print(f"📊 报告位置：{output_path}")
        print(f"📈 交易笔数：{len(all_data['transactions'])}")
        print(f"💰 总消费：¥ {total_spending:,.2f}")
        print(f"💳 涉及卡号：{unique_cards}个")
        if refund_count > 0:
            print(f"🔄 退款交易：{refund_count}笔")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
