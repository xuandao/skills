#!/usr/bin/env python3
"""
批量更新现有报告为Dataview版本
"""
import re
from pathlib import Path

obsidian_dir = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行"
processed_months = ["202501", "202502", "202503", "202504", "202505", "202506", 
                    "202508", "202509", "202510", "202511", "202512", "202601"]

print("🔄 批量更新现有报告为Dataview版本...")
print("=" * 100)

updated_count = 0
failed_count = 0

for ym in processed_months:
    report_path = obsidian_dir / f"{ym}-账单分析.md"
    
    if not report_path.exists():
        print(f"⚠️  {ym}: 文件不存在")
        continue
    
    print(f"\n📄 {ym}...")
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已有Dataview
        if "```dataviewjs" in content:
            print(f"   ✅ 已包含Dataview")
            continue
        
        # 提取信用额度和本期应还
        credit_limit_match = re.search(r"信用额度\*\*: ¥ ([\d,]+\.\d{2})", content)
        new_balance_match = re.search(r"本期应还\*\*: ¥ ([\d,]+\.\d{2})", content)
        
        credit_limit = float(credit_limit_match.group(1).replace(",", "")) if credit_limit_match else None
        new_balance = float(new_balance_match.group(1).replace(",", "")) if new_balance_match else None
        
        # 构建Dataview代码（使用原始字符串避免转义问题）
        dataview_overview = r"""
```dataviewjs
// 动态计算总消费、还款和额度使用率
const transactions = dv.current().file.lists
    .filter(l => l.text.match(/^\| \d{2}\/\d{2} \|/))
    .map(l => {
        const match = l.text.match(/¥\s*([-\d,]+\.\d{2})/);
        return match ? parseFloat(match[1].replace(',', '')) : 0;
    });

const totalSpending = transactions.filter(t => t > 0).reduce((a, b) => a + b, 0);
const totalPayment = transactions.filter(t => t < 0).reduce((a, b) => a + b, 0);
const netSpending = totalSpending + totalPayment;
"""
        
        if credit_limit and new_balance:
            dataview_overview += f"const usageRate = ({new_balance} / {credit_limit}) * 100;\n\n"
            dataview_overview += """dv.paragraph(`
- **总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
- **总还款**: ¥ ${Math.abs(totalPayment).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
- **净消费**: ¥ ${netSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
- **额度使用率**: ${usageRate.toFixed(1)}%
`);
```

"""
        else:
            dataview_overview += """dv.paragraph(`
- **总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
- **总还款**: ¥ ${Math.abs(totalPayment).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
- **净消费**: ¥ ${netSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
`);
```

"""
        
        # 在最低还款后插入
        content = re.sub(
            r"(- \*\*最低还款\*\*:.*?\n)\n",
            r"\1" + dataview_overview,
            content
        )
        
        # 移除旧的额度使用率和汇总行
        content = re.sub(r"- \*\*额度使用率\*\*:.*?\n\n", "", content)
        content = re.sub(r"\*\*汇总\*\*:.*?\n\n", "", content, flags=re.DOTALL)
        content = re.sub(r"\n\*\*总消费\*\*:.*?\n\n", "\n\n", content)
        
        # 替换分卡统计表格为Dataview
        dataview_card = r"""### 💳 分卡消费统计

```dataviewjs
// 动态按卡号统计
const lines = dv.current().file.lists
    .filter(l => l.text.match(/^\| \d{2}\/\d{2} \|.*\| \d{4} \|$/));

const cardStats = {};

lines.forEach(l => {
    const match = l.text.match(/\| ([-\d,]+\.\d{2}) \| (\d{4}) \|$/);
    if (match) {
        const amount = parseFloat(match[1].replace(',', ''));
        const card = match[2];
        if (!cardStats[card]) cardStats[card] = {count: 0, spending: 0, payment: 0};
        cardStats[card].count++;
        if (amount > 0) cardStats[card].spending += amount;
        else cardStats[card].payment += amount;
    }
});

let table = '| 卡号 | 交易笔数 | 消费金额 | 还款金额 | 净消费 |\\n';
table += '|------|----------|----------|----------|--------|\\n';
Object.keys(cardStats).sort().forEach(card => {
    const s = cardStats[card];
    const net = s.spending + s.payment;
    table += `| ${card} | ${s.count} | ¥ ${s.spending.toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ¥ ${Math.abs(s.payment).toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ¥ ${net.toLocaleString('zh-CN', {minimumFractionDigits: 2})} |\\n`;
});
dv.paragraph(table);
```

"""
        
        content = re.sub(
            r"### 💳 分卡消费统计\n\n\| 卡号.*?\n\n",
            dataview_card,
            content,
            flags=re.DOTALL
        )
        
        # 替换消费分类统计为Dataview
        dataview_category = r"""## 💰 消费分类统计

```dataviewjs
// 动态分类统计
const categories = {
    "餐饮": ["餐", "饭", "食", "咖啡", "茶"],
    "购物": ["超市", "商场", "淘宝", "京东", "天猫"],
    "交通": ["滴滴", "地铁", "公交", "加油"],
    "娱乐": ["电影", "游戏", "健身", "旅游"],
    "生活": ["水电", "话费", "宽带", "医疗"],
};

const lines = dv.current().file.lists.filter(l => l.text.match(/^\| \d{2}\/\d{2} \|/));
const categoryStats = {};
let totalSpending = 0;

lines.forEach(l => {
    const descMatch = l.text.match(/\| \d{2}\/\d{2} \| (.+?) \|/);
    const amountMatch = l.text.match(/¥\s*([-\d,]+\.\d{2})/);
    if (descMatch && amountMatch) {
        const desc = descMatch[1];
        const amount = parseFloat(amountMatch[1].replace(',', ''));
        if (amount > 0) {
            totalSpending += amount;
            let matched = false;
            for (const [cat, keywords] of Object.entries(categories)) {
                if (keywords.some(kw => desc.includes(kw))) {
                    if (!categoryStats[cat]) categoryStats[cat] = {count: 0, amount: 0};
                    categoryStats[cat].count++;
                    categoryStats[cat].amount += amount;
                    matched = true;
                    break;
                }
            }
            if (!matched) {
                if (!categoryStats['其他']) categoryStats['其他'] = {count: 0, amount: 0};
                categoryStats['其他'].count++;
                categoryStats['其他'].amount += amount;
            }
        }
    }
});

let table = '| 分类 | 笔数 | 金额 | 占比 |\\n|------|------|------|------|\\n';
Object.entries(categoryStats).sort((a, b) => b[1].amount - a[1].amount).forEach(([cat, stats]) => {
    const pct = (stats.amount / totalSpending * 100).toFixed(1);
    table += `| ${cat} | ${stats.count} | ¥ ${stats.amount.toLocaleString('zh-CN', {minimumFractionDigits: 2})} | ${pct}% |\\n`;
});
table += `\\n**总消费**: ¥ ${totalSpending.toLocaleString('zh-CN', {minimumFractionDigits: 2})}`;
dv.paragraph(table);
```

"""
        
        content = re.sub(
            r"## 💰 消费分类统计\n\n\| 分类.*?\n\n",
            dataview_category,
            content,
            flags=re.DOTALL
        )
        
        # 添加使用说明
        if "**💡 使用说明**" not in content:
            usage_note = "\n---\n\n"
            usage_note += "**💡 使用说明**:\n"
            usage_note += "- 本报告使用 Obsidian Dataview 插件实现动态计算\n"
            usage_note += "- 修改「交易明细」中的金额后，「账单概况」、「分卡统计」、「分类统计」会自动更新\n"
            usage_note += "- 需要在 Obsidian 中安装并启用 Dataview 插件\n"
            usage_note += "- 可以手动添加、删除或修改交易记录，统计会实时反映变化\n"
            content += usage_note
        
        # 保存
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"   ✅ 已更新")
        updated_count += 1
        
    except Exception as e:
        print(f"   ❌ {e}")
        failed_count += 1

print("\n" + "=" * 100)
print(f"📊 更新结果: ✅ {updated_count} 份 | ❌ {failed_count} 份")
print("=" * 100)
