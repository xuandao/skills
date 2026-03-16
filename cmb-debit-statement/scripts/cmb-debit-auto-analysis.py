#!/usr/bin/env python3
"""
招商银行一卡通账户变动通知解析工具 v1.3
解析 Gmail 中的一卡通账户变动通知邮件，生成交易账单到 Obsidian

支持格式：
1. 快捷支付（完整格式）：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元，余额 XX.XX
2. 快捷支付（无余额格式）：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元
3. 定投扣款（标准）：您尾号 XXXX 的账户于 MM 月 DD 日执行「XXXX」的定投计划，扣款 XX 元，活期余额 XX.XX 元
4. 定投扣款（简化）：您尾号为 XXXX 的账户于 MM 月 DD 日定投「XXXX」XX 元，活期余额 XX.XX 元

v1.3 更新：
- 自动读取已有账单文件，合并交易记录（去重）
- 重新生成完整报告，而非追加模式
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
from dataclasses import dataclass

# ============ 配置 ============
CONFIG = {
    # Gmail 查询条件（days 会被动态替换）
    "gmail_query_template": "一卡通账户变动通知 newer_than:{days}d",

    # Obsidian 保存路径
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",

    # 账户过滤（可选）：只处理特定尾号的账户
    "account_filter": [],  # 例如：["9583", "0707"]，空数组表示不过滤
}

# 交易类型
TRANSACTION_TYPE_PAYMENT = "快捷支付"
TRANSACTION_TYPE_INVESTMENT = "定投扣款"


@dataclass
class Transaction:
    """交易记录"""
    account: str  # 账户尾号
    date: str  # 交易日期 MM/DD
    time: Optional[str]  # 交易时间 HH:mm（快捷支付有，定投扣款可能没有）
    transaction_type: str  # 交易类型
    description: str  # 交易描述
    amount: float  # 金额（正数）
    balance: float  # 余额
    raw_content: str  # 原始邮件内容


def run_gws(api_path: str, params: Dict) -> Dict:
    """调用 gws 命令"""
    cmd = ["gws"] + api_path.split() + ["--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"gws 命令失败：{result.stderr}")
    return json.loads(result.stdout)


def extract_email_content(payload: Dict) -> Optional[str]:
    """递归提取邮件 HTML 正文"""
    if 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        # Gmail 使用 URL-safe base64
        standard_b64 = data.replace('-', '+').replace('_', '/')
        padding = 4 - len(standard_b64) % 4
        if padding != 4:
            standard_b64 += '=' * padding
        return base64.b64decode(standard_b64).decode('utf-8', errors='ignore')

    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html' and 'body' in part and 'data' in part['body']:
                data = part['body']['data']
                standard_b64 = data.replace('-', '+').replace('_', '/')
                padding = 4 - len(standard_b64) % 4
                if padding != 4:
                    standard_b64 += '=' * padding
                return base64.b64decode(standard_b64).decode('utf-8', errors='ignore')

            if 'parts' in part:
                result = extract_email_content(part)
                if result:
                    return result

    return None


def parse_quick_payment(content: str) -> Optional[Transaction]:
    """
    解析快捷支付格式邮件
    支持两种格式：
    1. 完整格式：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元，余额 XX.XX
    2. 无余额格式：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元（无余额字段）
    """
    # 先尝试完整格式（带余额）
    pattern = r'账户.*?(\d{4}).*?(\d{2})\s*月\s*(\d{2})\s*日\s*(\d{2}):(\d{2}).*?在\s*(.+?)\s*快捷支付\s*([\d.]+)\s*元.*?余额\s*([\d.]+)'

    match = re.search(pattern, content)
    if match:
        account = match.group(1)
        month = match.group(2)
        day = match.group(3)
        time = f"{match.group(4)}:{match.group(5)}"
        merchant = match.group(6).strip()
        amount = float(match.group(7))
        balance = float(match.group(8))

        return Transaction(
            account=account,
            date=f"{month}/{day}",
            time=time,
            transaction_type=TRANSACTION_TYPE_PAYMENT,
            description=merchant,
            amount=amount,
            balance=balance,
            raw_content=content
        )

    # 尝试无余额格式
    pattern_no_balance = r'账户.*?(\d{4}).*?(\d{2})\s*月\s*(\d{2})\s*日\s*(\d{2}):(\d{2}).*?在\s*(.+?)\s*快捷支付\s*([\d.]+)\s*元'

    match = re.search(pattern_no_balance, content)
    if match:
        account = match.group(1)
        month = match.group(2)
        day = match.group(3)
        time = f"{match.group(4)}:{match.group(5)}"
        merchant = match.group(6).strip()
        amount = float(match.group(7))

        return Transaction(
            account=account,
            date=f"{month}/{day}",
            time=time,
            transaction_type=TRANSACTION_TYPE_PAYMENT,
            description=merchant,
            amount=amount,
            balance=0.0,  # 无余额字段时设为 0
            raw_content=content
        )

    return None


def parse_investment_deduction(content: str) -> Optional[Transaction]:
    """
    解析定投扣款格式邮件
    支持两种格式：
    1. 标准格式：您尾号 XXXX 的账户于 MM 月 DD 日执行「XXXX」的定投计划，扣款 XX 元，活期余额 XX.XX 元
    2. 简化格式：您尾号为 XXXX 的账户于 MM 月 DD 日定投「XXXX」XX 元，活期余额 XX.XX 元
    """
    # 标准格式
    pattern = r'尾号\s*(\d{4}).*?的账户于\s*(\d{2})\s*月\s*(\d{2})\s*日\s*执行「(.+?)」的定投计划.*?扣款\s*([\d.]+)\s*元.*?活期余额\s*([\d.]+)\s*元'
    match = re.search(pattern, content)

    if not match:
        # 尝试简化格式（支持"尾号为 XXXX"和"尾号 XXXX"两种形式）
        # 先尝试"尾号为 XXXX"
        pattern_simple = r'尾号为\s*(\d{4})\s*的账户于\s*(\d{2})\s*月\s*(\d{2})\s*日定投「(.+?)」\s*([\d.]+)\s*元.*?活期余额\s*([\d.]+)\s*元'
        match = re.search(pattern_simple, content)

    if not match:
        # 尝试"尾号 XXXX"（没有"为"字）
        pattern_simple2 = r'尾号\s*(\d{4})\s*的账户于\s*(\d{2})\s*月\s*(\d{2})\s*日定投「(.+?)」\s*([\d.]+)\s*元.*?活期余额\s*([\d.]+)\s*元'
        match = re.search(pattern_simple2, content)

    if not match:
        return None

    account = match.group(1)
    month = match.group(2)
    day = match.group(3)
    product = match.group(4).strip()
    amount = float(match.group(5))
    balance = float(match.group(6))

    return Transaction(
        account=account,
        date=f"{month}/{day}",
        time=None,  # 定投扣款没有时间
        transaction_type=TRANSACTION_TYPE_INVESTMENT,
        description=product,
        amount=amount,
        balance=balance,
        raw_content=content
    )


def parse_transaction(content: str) -> Optional[Transaction]:
    """解析邮件内容，返回交易记录"""
    # 尝试快捷支付格式
    trans = parse_quick_payment(content)
    if trans:
        return trans

    # 尝试定投扣款格式
    trans = parse_investment_deduction(content)
    if trans:
        return trans

    return None


def fetch_emails(days: int) -> List[Dict]:
    """从 Gmail 获取邮件列表"""
    query = CONFIG["gmail_query_template"].format(days=days)

    result = run_gws("gmail users messages list", {
        "userId": "me",
        "q": query,
        "maxResults": 100  # 最多获取 100 封
    })

    return result.get("messages", [])


def get_email_content(msg_id: str) -> Tuple[Optional[str], Optional[str]]:
    """获取邮件内容和日期"""
    msg_data = run_gws("gmail users messages get", {
        "userId": "me",
        "id": msg_id,
        "format": "full"
    })

    # 提取日期
    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
    date_str = headers.get('Date', '')

    # 提取正文内容
    content = extract_email_content(msg_data['payload'])

    return content, date_str


def filter_accounts(transactions: List[Transaction]) -> List[Transaction]:
    """根据账户过滤配置过滤交易"""
    if not CONFIG["account_filter"]:
        return transactions

    return [t for t in transactions if t.account in CONFIG["account_filter"]]


def parse_all_emails(messages: List[Dict], days: int) -> List[Transaction]:
    """解析所有邮件，返回交易列表"""
    transactions = []
    parsed_count = 0
    failed_count = 0

    print(f"📧 开始解析 {len(messages)} 封邮件...")

    for msg in messages:
        content, date_str = get_email_content(msg['id'])

        if not content:
            failed_count += 1
            continue

        trans = parse_transaction(content)
        if trans:
            transactions.append(trans)
            parsed_count += 1
        else:
            failed_count += 1
            print(f"  ⚠️  无法解析：{content[:50]}...")

    print(f"✅ 解析完成：成功 {parsed_count} 封，失败 {failed_count} 封")

    # 账户过滤
    transactions = filter_accounts(transactions)

    # 按日期和时间排序
    transactions.sort(key=lambda t: (t.date, t.time or "00:00"))

    return transactions


def generate_report(transactions: List[Transaction]) -> str:
    """生成 Markdown 报告"""
    now = datetime.now()
    current_month = now.strftime("%Y 年%m 月")

    report = f"# 招商银行一卡通账单 - {current_month}\n\n"
    report += f"**更新时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    report += "---\n\n"

    # 账单概况
    report += "## 📊 账单概况\n\n"

    # 按账户统计
    account_stats = defaultdict(lambda: {
        "payment_count": 0,
        "payment_amount": 0,
        "investment_count": 0,
        "investment_amount": 0,
        "last_balance": 0
    })

    for trans in transactions:
        if trans.transaction_type == TRANSACTION_TYPE_PAYMENT:
            account_stats[trans.account]["payment_count"] += 1
            account_stats[trans.account]["payment_amount"] += trans.amount
        else:
            account_stats[trans.account]["investment_count"] += 1
            account_stats[trans.account]["investment_amount"] += trans.amount
        account_stats[trans.account]["last_balance"] = trans.balance

    report += "### 💳 账户统计\n\n"
    report += "| 账户 | 快捷支付笔数 | 快捷支付金额 | 定投扣款笔数 | 定投扣款金额 | 最后余额 |\n"
    report += "|------|-------------|-------------|-------------|-------------|----------|\n"

    for account in sorted(account_stats.keys()):
        stats = account_stats[account]
        report += f"| {account} | {stats['payment_count']} | ¥ {stats['payment_amount']:,.2f} | {stats['investment_count']} | ¥ {stats['investment_amount']:,.2f} | ¥ {stats['last_balance']:,.2f} |\n"

    # 总计
    total_payment = sum(1 for t in transactions if t.transaction_type == TRANSACTION_TYPE_PAYMENT)
    total_payment_amount = sum(t.amount for t in transactions if t.transaction_type == TRANSACTION_TYPE_PAYMENT)
    total_investment = sum(1 for t in transactions if t.transaction_type == TRANSACTION_TYPE_INVESTMENT)
    total_investment_amount = sum(t.amount for t in transactions if t.transaction_type == TRANSACTION_TYPE_INVESTMENT)

    report += f"\n**汇总**: 快捷支付 {total_payment} 笔 ¥{total_payment_amount:,.2f} | 定投扣款 {total_investment} 笔 ¥{total_investment_amount:,.2f}\n\n"

    # 分类统计（快捷支付按商户分类）
    if any(t.transaction_type == TRANSACTION_TYPE_PAYMENT for t in transactions):
        report += "## 📈 消费分类统计\n\n"

        # 按商户分组
        merchant_stats = defaultdict(lambda: {"count": 0, "amount": 0})
        for trans in transactions:
            if trans.transaction_type == TRANSACTION_TYPE_PAYMENT:
                # 简化商户名称（只取主要部分）
                merchant = trans.description.split(" ")[0] if " " in trans.description else trans.description
                if len(merchant) > 20:
                    merchant = merchant[:18] + "..."
                merchant_stats[merchant]["count"] += 1
                merchant_stats[merchant]["amount"] += trans.amount

        report += "| 商户 | 笔数 | 金额 | 占比 |\n"
        report += "|------|------|------|------|\n"

        for merchant in sorted(merchant_stats.keys(), key=lambda m: merchant_stats[m]["amount"], reverse=True):
            stats = merchant_stats[merchant]
            percentage = (stats["amount"] / total_payment_amount * 100) if total_payment_amount > 0 else 0
            report += f"| {merchant} | {stats['count']} | ¥ {stats['amount']:,.2f} | {percentage:.1f}% |\n"

        report += "\n"

    # 定投产品统计
    if any(t.transaction_type == TRANSACTION_TYPE_INVESTMENT for t in transactions):
        report += "## 💰 定投产品统计\n\n"

        product_stats = defaultdict(lambda: {"count": 0, "amount": 0, "accounts": set()})
        for trans in transactions:
            if trans.transaction_type == TRANSACTION_TYPE_INVESTMENT:
                product = trans.description
                if len(product) > 30:
                    product = product[:28] + "..."
                product_stats[product]["count"] += 1
                product_stats[product]["amount"] += trans.amount
                product_stats[product]["accounts"].add(trans.account)

        report += "| 产品 | 账户 | 扣款次数 | 总金额 |\n"
        report += "|------|------|---------|--------|\n"

        for product in sorted(product_stats.keys()):
            stats = product_stats[product]
            accounts = ", ".join(sorted(stats["accounts"]))
            report += f"| {product} | {accounts} | {stats['count']} | ¥ {stats['amount']:,.2f} |\n"

        report += "\n"

    # 详细交易记录
    report += "## 📝 详细交易记录\n\n"
    report += "| 日期 | 时间 | 账户 | 类型 | 描述 | 金额 | 余额 |\n"
    report += "|------|------|------|------|------|------|------|\n"

    for trans in transactions:
        time_str = trans.time if trans.time else "-"
        type_str = "💳 快捷支付" if trans.transaction_type == TRANSACTION_TYPE_PAYMENT else "💰 定投扣款"
        amount_str = f"-¥{trans.amount:,.2f}" if trans.transaction_type == TRANSACTION_TYPE_PAYMENT else f"-¥{trans.amount:,.2f}"

        # 简化描述
        desc = trans.description
        if len(desc) > 25:
            desc = desc[:22] + "..."

        report += f"| {trans.date} | {time_str} | {trans.account} | {type_str} | {desc} | {amount_str} | ¥{trans.balance:,.2f} |\n"

    if not transactions:
        report += "\n⚠️  **本期暂无交易记录**\n"

    report += "\n---\n\n"
    report += "*注：本报告由程序自动生成，数据来源于 Gmail 邮件解析*"

    return report


def parse_existing_transactions(file_path: Path) -> List[Transaction]:
    """从已有的账单文件中解析现有交易记录"""
    if not file_path.exists():
        return []

    transactions = []

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 从详细交易记录表格中解析
    # 格式：| 日期 | 时间 | 账户 | 类型 | 描述 | 金额 | 余额 |
    pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

    for match in re.finditer(pattern, content):
        date = match.group(1)
        time = match.group(2) if match.group(2) != "-" else None
        account = match.group(3)
        trans_type = TRANSACTION_TYPE_PAYMENT if "快捷支付" in match.group(4) else TRANSACTION_TYPE_INVESTMENT
        description = match.group(5).strip()
        amount = float(match.group(6).replace(",", ""))
        balance = float(match.group(7).replace(",", ""))

        transactions.append(Transaction(
            account=account,
            date=date,
            time=time,
            transaction_type=trans_type,
            description=description,
            amount=amount,
            balance=balance,
            raw_content=""
        ))

    return transactions


def save_to_obsidian(report: str) -> Path:
    """保存报告到 Obsidian

    月度账单使用 YYYYMM-一卡通账单.md 格式
    """
    CONFIG["obsidian_dir"].mkdir(parents=True, exist_ok=True)

    now = datetime.now()

    # 统一使用 YYYYMM-一卡通账单.md 格式
    filename = now.strftime("%Y%m-一卡通账单.md")

    output_path = CONFIG["obsidian_dir"] / filename

    # 以写入模式写入（覆盖旧内容）
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ 报告已保存：{output_path}")
    return output_path


def merge_transactions(existing: List[Transaction], new: List[Transaction]) -> List[Transaction]:
    """合并交易记录，去重（基于日期 + 时间 + 账户 + 金额）"""
    # 创建现有交易的唯一键集合
    existing_keys = set()
    for t in existing:
        key = (t.date, t.time, t.account, t.transaction_type, t.description, t.amount)
        existing_keys.add(key)

    # 添加新交易（去重）
    merged = list(existing)
    for t in new:
        key = (t.date, t.time, t.account, t.transaction_type, t.description, t.amount)
        if key not in existing_keys:
            merged.append(t)

    # 按日期和时间排序
    merged.sort(key=lambda t: (t.date, t.time or "00:00"))

    return merged


def main():
    """主流程"""
    parser = argparse.ArgumentParser(description="招商银行一卡通账单解析工具")
    parser.add_argument("--period", choices=["day", "week", "month"], default="week",
                        help="统计周期：day(天), week(周), month(月)")
    parser.add_argument("--days", type=int, default=None,
                        help="自定义天数（优先于 period 参数）")
    parser.add_argument("--output-dir", "-o", type=str, default=None,
                        help="输出目录（覆盖 CONFIG 中的 obsidian_dir）")
    args = parser.parse_args()

    # 如果提供了 --output-dir 参数，则覆盖 CONFIG 配置
    if args.output_dir:
        CONFIG["obsidian_dir"] = Path(args.output_dir)

    # 确定输出文件路径
    now = datetime.now()
    output_filename = now.strftime("%Y%m-一卡通账单.md")
    output_path = CONFIG["obsidian_dir"] / output_filename

    # 1. 读取已有的交易记录（如果文件存在）
    existing_transactions = []
    if output_path.exists():
        print(f"📂 读取已有账单文件：{output_path}")
        existing_transactions = parse_existing_transactions(output_path)
        print(f"✅ 读取到 {len(existing_transactions)} 条现有交易记录")

    # 2. 从 Gmail 获取邮件
    days = args.days if args.days else (1 if args.period == "day" else (7 if args.period == "week" else 30))
    print(f"🔍 查询最近{days}天的一卡通账户变动通知...")

    messages = fetch_emails(days)
    if not messages:
        print("❌ 未找到邮件")
        return

    print(f"✅ 找到 {len(messages)} 封邮件")

    # 3. 解析邮件内容
    new_transactions = parse_all_emails(messages, days)

    if not new_transactions:
        print("⚠️  未找到可解析的交易记录")
        return

    # 4. 合并交易记录（去重）
    all_transactions = merge_transactions(existing_transactions, new_transactions)

    print(f"\n📊 合并后交易总数：{len(all_transactions)}")
    print(f"   - 原有交易：{len(existing_transactions)}")
    print(f"   - 新增交易：{len(all_transactions) - len(existing_transactions)}")

    # 5. 生成报告
    print("\n📄 生成报告...")
    report = generate_report(all_transactions)

    # 6. 保存到 Obsidian
    save_to_obsidian(report)

    # 7. 统计信息
    print("\n" + "=" * 60)
    print("✅ 账单解析完成！")
    print(f"📊 交易笔数：{len(all_transactions)}")
    print(f"📈 快捷支付：{sum(1 for t in all_transactions if t.transaction_type == TRANSACTION_TYPE_PAYMENT)} 笔")
    print(f"💰 定投扣款：{sum(1 for t in all_transactions if t.transaction_type == TRANSACTION_TYPE_INVESTMENT)} 笔")
    print(f"📄 报告位置：{output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
