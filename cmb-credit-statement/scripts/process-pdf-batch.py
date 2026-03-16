#!/usr/bin/env python3
"""
批量处理PDF账单（用于HTML账单缺失的月份）
"""
import json, subprocess, base64, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 读取PDF账单列表
with open("/tmp/cmb_missing_pdf.json", "r") as f:
    statements = json.load(f)

CONFIG = {
    "download_dir": Path.home() / "Downloads" / "cmb-statements",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",
}

CATEGORY_KEYWORDS = {
    "餐饮": ["餐", "饭", "食", "咖啡", "茶", "酒", "美团", "饿了么", "肯德基", "麦当劳", "星巴克", "霸王茶姬", "赛百味", "外婆家", "莜面村", "瑞幸", "茵赫", "迈志豪"],
    "购物": ["超市", "商场", "淘宝", "京东", "拼多多", "天猫", "苹果", "小米", "华为", "沃尔玛", "罗森", "新宇", "便利", "小红书", "乐高"],
    "交通": ["滴滴", "出租", "地铁", "公交", "加油", "停车", "高速"],
    "娱乐": ["电影", "游戏", "健身", "KTV", "酒吧", "旅游", "乐高", "智乐鼓"],
    "生活": ["水电", "物业", "话费", "宽带", "医疗", "药店", "供电", "电信", "燃气", "水费", "电费", "阿里云"],
    "其他": []
}

def run_gws(api_path, params):
    cmd = ["gws"] + api_path.split() + ["--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def download_pdf(msg_id, att_id, filename):
    """下载PDF附件"""
    CONFIG["download_dir"].mkdir(parents=True, exist_ok=True)
    
    att_data = run_gws("gmail users messages attachments get", {
        "userId": "me",
        "messageId": msg_id,
        "id": att_id
    })
    
    pdf_bytes = base64.urlsafe_b64decode(att_data["data"])
    pdf_path = CONFIG["download_dir"] / filename
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    
    return pdf_path

def parse_pdf_statement(pdf_path):
    """解析PDF账单"""
    result = subprocess.run(["pdftotext", str(pdf_path), "-"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"PDF解析失败: {result.stderr}")
    
    text = result.stdout
    
    data = {
        "statement_date": None,
        "due_date": None,
        "credit_limit": None,
        "new_balance": None,
        "min_payment": None,
        "transactions": []
    }
    
    # 提取基本信息
    patterns = {
        "statement_date": r"账单日[\s\n]+(\d{4}年\d{2}月\d{2}日)",
        "due_date": r"(\d{4}年\d{2}月\d{2}日)[\s\n]+Payment Due Date",
        "credit_limit": r"信用额度[\s\n]+¥\s*([\d,]+\.\d{2})",
        "new_balance": r"本期应还金额[\s\n]+¥\s*([\d,]+\.\d{2})",
        "min_payment": r"本期最低还款额[\s\n]+.*?[\s\n]+¥\s*([\d,]+\.\d{2})",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            value = match.group(1)
            if key in ["credit_limit", "new_balance", "min_payment"]:
                value = float(value.replace(",", ""))
            data[key] = value
    
    # 提取交易记录
    trans_pattern = r"(\d{2}/\d{2})\s+(\d{2}/\d{2})?\s+(.+?)\s+([-\d,]+\.\d{2})\s+(\d{4})\s+([-\d,]+\.\d{2})"
    for match in re.finditer(trans_pattern, text):
        trans_date, post_date, desc, amount, card, orig_amount = match.groups()
        data["transactions"].append({
            "date": trans_date,
            "description": desc.strip(),
            "amount": float(amount.replace(",", "")),
            "card": card
        })
    
    return data

def categorize_transactions(transactions):
    categorized = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    for trans in transactions:
        matched = False
        for category, keywords in CATEGORY_KEYWORDS.items():
            if category != "其他" and any(kw in trans["description"] for kw in keywords):
                categorized[category].append(trans)
                matched = True
                break
        if not matched:
            categorized["其他"].append(trans)
    return categorized

def generate_report(data, source_info):
    report = f"# 招商银行信用卡账单分析\n\n**数据来源**: {source_info}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    
    report += f"## 📅 账单概况\n\n- **账单日**: {data['statement_date'] or 'N/A'}\n- **到期还款日**: {data['due_date'] or 'N/A'}\n"
    report += f"- **信用额度**: ¥ {data['credit_limit']:,.2f}\n" if data['credit_limit'] else "- **信用额度**: N/A\n"
    report += f"- **本期应还**: ¥ {data['new_balance']:,.2f}\n" if data['new_balance'] else "- **本期应还**: N/A\n"
    report += f"- **最低还款**: ¥ {data['min_payment']:,.2f}\n\n" if data['min_payment'] else "- **最低还款**: N/A\n\n"
    
    if data['credit_limit'] and data['new_balance']:
        report += f"- **额度使用率**: {(data['new_balance'] / data['credit_limit']) * 100:.1f}%\n\n"
    
    # 分卡统计
    card_stats = defaultdict(lambda: {"count": 0, "spending": 0, "payment": 0, "net": 0})
    for trans in data["transactions"]:
        card_stats[trans["card"]]["count"] += 1
        if trans["amount"] > 0:
            card_stats[trans["card"]]["spending"] += trans["amount"]
        else:
            card_stats[trans["card"]]["payment"] += trans["amount"]
        card_stats[trans["card"]]["net"] += trans["amount"]
    
    report += "### 💳 分卡消费统计\n\n| 卡号 | 交易笔数 | 消费金额 | 还款金额 | 净消费 |\n|------|----------|----------|----------|--------|\n"
    for card in sorted(card_stats.keys()):
        s = card_stats[card]
        report += f"| {card} | {s['count']} | ¥ {s['spending']:,.2f} | ¥ {s['payment']:,.2f} | ¥ {s['net']:,.2f} |\n"
    
    total_spending = sum(t['amount'] for t in data['transactions'] if t['amount'] > 0)
    total_payment = sum(t['amount'] for t in data['transactions'] if t['amount'] < 0)
    report += f"\n**汇总**: 总消费 ¥ {total_spending:,.2f} | 总还款 ¥ {total_payment:,.2f} | 净消费 ¥ {total_spending + total_payment:,.2f}\n\n"
    
    # 分类统计
    categorized = categorize_transactions(data['transactions'])
    report += "## 💰 消费分类统计\n\n| 分类 | 笔数 | 金额 | 占比 |\n|------|------|------|------|\n"
    for category, trans_list in categorized.items():
        if trans_list:
            amount = sum(t['amount'] for t in trans_list)
            report += f"| {category} | {len(trans_list)} | ¥ {amount:,.2f} | {(amount / total_spending * 100) if total_spending > 0 else 0:.1f}% |\n"
    report += f"\n**总消费**: ¥ {total_spending:,.2f}\n\n"
    
    # 交易明细
    report += "## 📝 交易明细\n\n"
    for category, trans_list in categorized.items():
        if trans_list:
            report += f"### {category}\n\n| 日期 | 描述 | 金额 | 卡号 |\n|------|------|------|------|\n"
            for trans in sorted(trans_list, key=lambda x: x['date']):
                report += f"| {trans['date']} | {trans['description']} | ¥ {trans['amount']:,.2f} | {trans['card']} |\n"
            report += "\n"
    
    # 消费建议
    report += "## 💡 消费建议\n\n"
    if data['credit_limit'] and data['new_balance']:
        usage_rate = (data['new_balance'] / data['credit_limit']) * 100
        if usage_rate > 80:
            report += "⚠️ **额度使用率较高**，建议及时还款。\n\n"
    
    max_category = max(categorized.items(), key=lambda x: sum(t['amount'] for t in x[1]))
    if max_category[1]:
        cat_name = max_category[0]
        cat_amount = sum(t['amount'] for t in max_category[1])
        report += f"📊 本期 **{cat_name}** 消费最多，共 ¥ {cat_amount:,.2f}，占总消费的 {(cat_amount/total_spending*100):.1f}%\n\n"
    
    return report

print(f"🚀 批量处理 {len(statements)} 份PDF账单...\n" + "=" * 100)
results = []

for stmt in statements:
    print(f"\n📄 {stmt['statement_date']}...")
    try:
        # 下载PDF
        print(f"   📥 下载: {stmt['filename']}")
        pdf_path = download_pdf(stmt['msg_id'], stmt['att_id'], stmt['filename'])
        
        # 解析PDF
        print(f"   📄 解析PDF...")
        data = parse_pdf_statement(pdf_path)
        
        if len(data['transactions']) == 0:
            results.append({"year_month": stmt['year_month'], "success": False, "error": "无交易"})
            print("   ⚠️  无交易")
            continue
        
        print(f"   ✅ {len(data['transactions'])} 笔")
        
        # 生成报告
        report = generate_report(data, f"PDF附件 (`{stmt['filename']}`)")
        
        # 保存
        CONFIG["obsidian_dir"].mkdir(parents=True, exist_ok=True)
        output_path = CONFIG["obsidian_dir"] / f"{stmt['year_month']}-信用卡账单分析.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"   ✅ 已保存: {output_path.name}")
        
        results.append({
            "year_month": stmt['year_month'],
            "success": True,
            "transactions": len(data['transactions']),
            "total_spending": sum(t['amount'] for t in data['transactions'] if t['amount'] > 0),
            "new_balance": data['new_balance']
        })
        
    except Exception as e:
        results.append({"year_month": stmt['year_month'], "success": False, "error": str(e)})
        print(f"   ❌ {e}")

print("\n" + "=" * 100 + "\n📊 结果\n" + "=" * 100)
for r in results:
    if r['success']:
        print(f"✅ {r['year_month']} | {r['transactions']:3d} 笔 | ¥{r['total_spending']:>10,.2f} | ¥{r['new_balance']:>10,.2f}")
    else:
        print(f"❌ {r['year_month']} | {r['error']}")
print("=" * 100)
