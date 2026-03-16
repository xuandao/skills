#!/usr/bin/env python3
"""
生成带Dataview动态计算的账单报告
修改交易记录后，统计数据会自动更新
"""

def generate_report_with_dataview(data, source_info, category_keywords):
    """生成带Dataview公式的报告"""
    from datetime import datetime
    
    report = f"# 招商银行信用卡账单分析\n\n"
    report += f"**数据来源**: {source_info}\n"
    report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += "---\n\n"
    
    # 账单概况（静态信息）
    report += "## 📅 账单概况\n\n"
    report += f"- **账单月份**: {data['statement_date'] or 'N/A'}\n"
    report += f"- **到期还款日**: {data['due_date'] or 'N/A'}\n"
    report += f"- **信用额度**: ¥ {data['credit_limit']:,.2f}\n" if data['credit_limit'] else "- **信用额度**: N/A\n"
    report += f"- **本期应还**: ¥ {data['new_balance']:,.2f}\n\n" if data['new_balance'] else "- **本期应还**: N/A\n\n"
    
    # 动态计算总消费和额度使用率
    report += "```dataviewjs\n"
    report += "// 动态计算总消费、还款和额度使用率\n"
    report += "const transactions = dv.current().file.lists\n"
    report += "    .filter(l => l.text.match(/^\\| \\d{2}\\/\\d{2} \\|/))\n"
    report += "    .map(l => {\n"
    report += "        const match = l.text.match(/¥\\s*([-\\d,]+\\.\\d{2})/);\n"
    report += "        return match ? parseFloat(match[1].replace(',', '')) : 0;\n"
    report += "    });\n\n"
    report += "const totalSpending = transactions.filter(t => t > 0).reduce((a, b) => a + b, 0);\n"
    report += "const totalPayment = transactions.filter(t => t < 0).reduce((a, b) => a + b, 0);\n"
    report += "const netSpending = totalSpending + totalPayment;\n"
    
    if data['credit_limit'] and data['new_balance']:
        report += f"const usageRate = ({data['new_balance']} / {data['credit_limit']}) * 100;\n\n"
        report += "dv.paragraph(`\n"
        report += "- **总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "- **总还款**: ¥ ${Math.abs(totalPayment).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "- **净消费**: ¥ ${netSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "- **额度使用率**: ${usageRate.toFixed(1)}%\n"
        report += "`);\n"
    else:
        report += "dv.paragraph(`\n"
        report += "- **总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "- **总还款**: ¥ ${Math.abs(totalPayment).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "- **净消费**: ¥ ${netSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}\n"
        report += "`);\n"
    
    report += "```\n\n"
    
    # 动态分卡统计
    report += "### 💳 分卡消费统计\n\n"
    report += "```dataviewjs\n"
    report += "// 动态按卡号统计\n"
    report += "const lines = dv.current().file.lists\n"
    report += "    .filter(l => l.text.match(/^\\| \\d{2}\\/\\d{2} \\|.*\\| \\d{4} \\|$/));\n\n"
    report += "const cardStats = {};\n\n"
    report += "lines.forEach(l => {\n"
    report += "    const match = l.text.match(/\\| ([-\\d,]+\\.\\d{2}) \\| (\\d{4}) \\|$/);\n"
    report += "    if (match) {\n"
    report += "        const amount = parseFloat(match[1].replace(',', ''));\n"
    report += "        const card = match[2];\n"
    report += "        if (!cardStats[card]) cardStats[card] = {count: 0, spending: 0, payment: 0};\n"
    report += "        cardStats[card].count++;\n"
    report += "        if (amount > 0) cardStats[card].spending += amount;\n"
    report += "        else cardStats[card].payment += amount;\n"
    report += "    }\n"
    report += "});\n\n"
    report += "let table = '| 卡号 | 交易笔数 | 消费金额 | 还款金额 | 净消费 |\\\\n';\n"
    report += "table += '|------|----------|----------|----------|--------|\\\\n';\n"
    report += "Object.keys(cardStats).sort().forEach(card => {\n"
    report += "    const s = cardStats[card];\n"
    report += "    const net = s.spending + s.payment;\n"
    report += "    table += `| ${card} | ${s.count} | ¥ ${s.spending.toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ¥ ${Math.abs(s.payment).toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ¥ ${net.toLocaleString('zh-CN', {minimumFractionDigits: 2})} |\\\\n`;\n"
    report += "});\n"
    report += "dv.paragraph(table);\n"
    report += "```\n\n"
    
    # 动态分类统计
    report += "## 💰 消费分类统计\n\n"
    report += "```dataviewjs\n"
    report += "// 动态分类统计\n"
    report += "const categories = {\n"
    for cat, keywords in category_keywords.items():
        if cat != "其他":
            kw_str = '", "'.join(keywords[:5])  # 只取前5个关键词
            report += f'    "{cat}": ["{kw_str}"],\n'
    report += "};\n\n"
    report += "const lines = dv.current().file.lists.filter(l => l.text.match(/^\\| \\d{2}\\/\\d{2} \\|/));\n"
    report += "const categoryStats = {};\n"
    report += "let totalSpending = 0;\n\n"
    report += "lines.forEach(l => {\n"
    report += "    const descMatch = l.text.match(/\\| \\d{2}\\/\\d{2} \\| (.+?) \\|/);\n"
    report += "    const amountMatch = l.text.match(/¥\\s*([-\\d,]+\\.\\d{2})/);\n"
    report += "    if (descMatch && amountMatch) {\n"
    report += "        const desc = descMatch[1];\n"
    report += "        const amount = parseFloat(amountMatch[1].replace(',', ''));\n"
    report += "        if (amount > 0) {\n"
    report += "            totalSpending += amount;\n"
    report += "            let matched = false;\n"
    report += "            for (const [cat, keywords] of Object.entries(categories)) {\n"
    report += "                if (keywords.some(kw => desc.includes(kw))) {\n"
    report += "                    if (!categoryStats[cat]) categoryStats[cat] = {count: 0, amount: 0};\n"
    report += "                    categoryStats[cat].count++;\n"
    report += "                    categoryStats[cat].amount += amount;\n"
    report += "                    matched = true;\n"
    report += "                    break;\n"
    report += "                }\n"
    report += "            }\n"
    report += "            if (!matched) {\n"
    report += "                if (!categoryStats['其他']) categoryStats['其他'] = {count: 0, amount: 0};\n"
    report += "                categoryStats['其他'].count++;\n"
    report += "                categoryStats['其他'].amount += amount;\n"
    report += "            }\n"
    report += "        }\n"
    report += "    }\n"
    report += "});\n\n"
    report += "let table = '| 分类 | 笔数 | 金额 | 占比 |\\\\n|------|------|------|------|\\\\n';\n"
    report += "Object.entries(categoryStats).sort((a, b) => b[1].amount - a[1].amount).forEach(([cat, stats]) => {\n"
    report += "    const pct = (stats.amount / totalSpending * 100).toFixed(1);\n"
    report += "    table += `| ${cat} | ${stats.count} | ¥ ${stats.amount.toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ${pct}% |\\\\n`;\n"
    report += "});\n"
    report += "table += `\\\\n**总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2})}`;\n"
    report += "dv.paragraph(table);\n"
    report += "```\n\n"
    
    # 交易明细（静态，可手动编辑）
    report += "## 📝 交易明细\n\n"
    
    # 按分类输出交易
    from collections import defaultdict
    
    def categorize_transactions(transactions):
        categorized = {cat: [] for cat in category_keywords.keys()}
        for trans in transactions:
            matched = False
            for category, keywords in category_keywords.items():
                if category != "其他" and any(kw in trans["description"] for kw in keywords):
                    categorized[category].append(trans)
                    matched = True
                    break
            if not matched:
                categorized["其他"].append(trans)
        return categorized
    
    categorized = categorize_transactions(data['transactions'])
    
    for category, trans_list in categorized.items():
        if trans_list:
            report += f"### {category}\n\n"
            report += "| 日期 | 描述 | 金额 | 卡号 |\n"
            report += "|------|------|------|------|\n"
            for trans in sorted(trans_list, key=lambda x: x['date']):
                report += f"| {trans['date']} | {trans['description']} | ¥ {trans['amount']:,.2f} | {trans['card']} |\n"
            report += "\n"
    
    # 消费建议
    report += "## 💡 消费建议\n\n"
    report += "```dataviewjs\n"
    if data['credit_limit'] and data['new_balance']:
        report += f"const usageRate = ({data['new_balance']} / {data['credit_limit']}) * 100;\n"
        report += "let advice = '';\n"
        report += "if (usageRate > 80) {\n"
        report += "    advice += '⚠️ **额度使用率较高**，建议及时还款，避免影响信用评分。\\\\n\\\\n';\n"
        report += "}\n"
        report += "advice += '📊 本报告使用 Dataview 实现动态计算，修改交易记录后统计数据会自动更新。';\n"
        report += "dv.paragraph(advice);\n"
    else:
        report += "dv.paragraph('📊 本报告使用 Dataview 实现动态计算，修改交易记录后统计数据会自动更新。');\n"
    report += "```\n\n"
    
    # 使用说明
    report += "---\n\n"
    report += "**💡 使用说明**:\n"
    report += "- 本报告使用 Obsidian Dataview 插件实现动态计算\n"
    report += "- 修改「交易明细」中的金额后，「账单概况」、「分卡统计」、「分类统计」会自动更新\n"
    report += "- 需要在 Obsidian 中安装并启用 Dataview 插件\n"
    report += "- 可以手动添加、删除或修改交易记录，统计会实时反映变化\n"
    
    return report

# 示例使用
if __name__ == "__main__":
    sample_data = {
        "statement_date": "2026年02月",
        "due_date": "2026年03月01日",
        "credit_limit": 88000.00,
        "new_balance": 25380.48,
        "min_payment": 1324.40,
        "transactions": [
            {"date": "01/12", "description": "支付宝-杭州茵赫餐饮管理有限公司", "amount": 5.00, "card": "2693"},
            {"date": "01/12", "description": "支付宝-杭州迈志豪餐饮管理有限公司", "amount": 17.10, "card": "2693"},
            {"date": "01/15", "description": "支付宝-浙江新宇商业集团有限公司", "amount": 14.40, "card": "2693"},
            {"date": "02/01", "description": "银联转账还款", "amount": -1414.30, "card": "1727"},
        ]
    }
    
    category_keywords = {
        "餐饮": ["餐", "饭", "食", "咖啡", "茶", "美团", "饿了么", "星巴克", "茵赫", "迈志豪"],
        "购物": ["超市", "商场", "淘宝", "京东", "天猫", "苹果", "新宇"],
        "交通": ["滴滴", "地铁", "公交", "加油"],
        "娱乐": ["电影", "游戏", "健身", "旅游"],
        "生活": ["水电", "话费", "宽带", "医疗"],
        "其他": []
    }
    
    report = generate_report_with_dataview(sample_data, "邮件正文（HTML）", category_keywords)
    print(report)
