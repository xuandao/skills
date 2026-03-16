# 配置指南

## 用户配置

在使用前，需要修改 `scripts/cmb-auto-analysis.py` 中的配置：

```python
CONFIG = {
    # Gmail 查询条件
    "gmail_query": "(from:招商银行 OR from:cmbchina.com) (subject:账单 OR subject:对账单) has:attachment newer_than:90d",
    
    # PDF 下载目录
    "download_dir": Path.home() / "Downloads" / "cmb-statements",
    
    # Obsidian 笔记保存路径
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",
}
```

## Gmail 查询语法

### 基本查询

```python
# 查询招商银行发送的邮件
"from:招商银行 OR from:cmbchina.com"

# 主题包含"账单"
"subject:账单"

# 包含附件
"has:attachment"
```

### 时间过滤

```python
# 最近 7 天
"newer_than:7d"

# 最近 30 天
"newer_than:30d"

# 最近 90 天
"newer_than:90d"

# 指定日期范围
"after:2026/01/01 before:2026/03/31"
```

### 组合查询

```python
# 完整示例
"(from:招商银行 OR from:cmbchina.com) (subject:账单 OR subject:对账单) has:attachment newer_than:90d"
```

## Obsidian 路径配置

### macOS (iCloud)

```python
Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/Areas/理财/招商银行"
```

### macOS (本地)

```python
Path.home() / "Documents/<VaultName>/Areas/理财/招商银行"
```

### Linux

```python
Path.home() / "Documents/<VaultName>/Areas/理财/招商银行"
```

### Windows

```python
Path("C:/Users/<Username>/Documents/<VaultName>/Areas/理财/招商银行")
```

## 消费分类自定义

修改 `CATEGORY_KEYWORDS` 字典来自定义分类规则：

```python
CATEGORY_KEYWORDS = {
    "餐饮": ["餐", "饭", "食", "咖啡", "茶", "酒", "美团", "饿了么"],
    "购物": ["超市", "商场", "淘宝", "京东", "拼多多", "天猫"],
    "交通": ["滴滴", "出租", "地铁", "公交", "加油", "停车"],
    "娱乐": ["电影", "游戏", "健身", "KTV", "酒吧", "旅游"],
    "生活": ["水电", "物业", "话费", "宽带", "医疗", "药店"],
    "教育": ["学费", "培训", "书店", "图书"],  # 新增分类
    "其他": []
}
```

### 添加新分类

```python
"投资": ["证券", "基金", "股票", "理财"],
"保险": ["保险", "平安", "太平洋"],
"宠物": ["宠物", "猫粮", "狗粮", "兽医"],
```

### 优化匹配规则

如果需要更精确的匹配，可以修改 `categorize_transactions()` 函数：

```python
def categorize_transactions(transactions: List[Dict]) -> Dict[str, List[Dict]]:
    categorized = {cat: [] for cat in CATEGORY_KEYWORDS.keys()}
    
    for trans in transactions:
        desc = trans["description"]
        matched = False
        
        # 优先级匹配：先匹配更具体的分类
        priority_categories = ["餐饮", "交通", "娱乐"]
        
        for category in priority_categories:
            keywords = CATEGORY_KEYWORDS[category]
            if any(kw in desc for kw in keywords):
                categorized[category].append(trans)
                matched = True
                break
        
        if not matched:
            for category, keywords in CATEGORY_KEYWORDS.items():
                if category in priority_categories or category == "其他":
                    continue
                if any(kw in desc for kw in keywords):
                    categorized[category].append(trans)
                    matched = True
                    break
        
        if not matched:
            categorized["其他"].append(trans)
    
    return categorized
```

## 报告格式自定义

### 修改输出文件名

在 `save_to_obsidian()` 函数中：

```python
# 默认格式: 202502-账单分析.md
filename = f"{match.group(1)}{match.group(2)}-账单分析.md"

# 自定义格式
filename = f"CMB-{match.group(1)}-{match.group(2)}.md"  # CMB-2025-02.md
filename = f"{match.group(1)}年{match.group(2)}月账单.md"  # 2025年02月账单.md
```

### 添加自定义报告内容

在 `generate_report()` 函数中添加：

```python
# 在报告末尾添加自定义内容
report += "## 📌 备注\n\n"
report += "- 本报告由自动化工具生成\n"
report += "- 数据来源: 招商银行信用卡账单 PDF\n"
report += f"- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

# 添加标签
report += "---\n\n"
report += "#理财 #信用卡 #招商银行\n"
```

### 修改表格格式

```python
# 默认格式
report += "| 分类 | 笔数 | 金额 | 占比 |\n"
report += "|------|------|------|------|\n"

# 添加更多列
report += "| 分类 | 笔数 | 金额 | 占比 | 平均单笔 |\n"
report += "|------|------|------|------|----------|\n"

# 计算平均单笔金额
avg_amount = amount / count if count > 0 else 0
report += f"| {category} | {count} | ¥ {amount:,.2f} | {percentage:.1f}% | ¥ {avg_amount:.2f} |\n"
```

## 自动化运行

### 使用 cron 定时任务

```bash
# 每月 16 号早上 9 点运行（账单日后一天）
0 9 16 * * python3 ~/.openclaw/workspace/skills/cmb-statement/scripts/cmb-auto-analysis.py

# 每天晚上 22 点运行
0 22 * * * python3 ~/.openclaw/workspace/skills/cmb-statement/scripts/cmb-auto-analysis.py
```

### 使用 OpenClaw cron

```python
# 在 OpenClaw 中设置定时任务
cron.add({
    "name": "招商银行账单分析",
    "schedule": {
        "kind": "cron",
        "expr": "0 9 16 * *",  # 每月 16 号早上 9 点
        "tz": "Asia/Shanghai"
    },
    "payload": {
        "kind": "systemEvent",
        "text": "分析招商银行账单"
    },
    "sessionTarget": "main",
    "enabled": True
})
```

## 依赖安装

### macOS

```bash
# 安装 poppler (包含 pdftotext)
brew install poppler

# 验证安装
pdftotext -v
```

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install poppler-utils
```

### Linux (CentOS/RHEL)

```bash
sudo yum install poppler-utils
```

## 故障排查

### 问题 1: 找不到 gws 命令

```bash
# 检查 gws 是否安装
which gws

# 如果未安装，参考 OpenClaw 文档安装
```

### 问题 2: Gmail API 认证失败

```bash
# 检查 Gmail API 是否已配置
gws gmail users messages list --params '{"userId": "me", "maxResults": 1}'

# 如果失败，需要重新配置 Gmail API 认证
```

### 问题 3: PDF 解析失败

```bash
# 检查 pdftotext 是否安装
pdftotext -v

# 手动测试 PDF 提取
pdftotext sample.pdf -
```

### 问题 4: Obsidian 路径错误

```bash
# 检查路径是否存在
ls -la ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/

# 如果不存在，修改配置中的路径
```

## 高级配置

### 多账户支持

如果有多张招商银行信用卡，可以修改代码支持多账户：

```python
ACCOUNTS = {
    "1719": {"name": "主卡", "color": "blue"},
    "1727": {"name": "副卡", "color": "green"},
    "2693": {"name": "附属卡", "color": "orange"},
}

# 在报告中按卡号分组
for card_num, account_info in ACCOUNTS.items():
    card_trans = [t for t in transactions if t['card'] == card_num]
    if card_trans:
        report += f"### {account_info['name']} (尾号 {card_num})\n\n"
        # ... 生成该卡的交易明细
```

### 导出到其他格式

```python
# 导出为 CSV
import csv

def export_to_csv(transactions, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'description', 'amount', 'card'])
        writer.writeheader()
        writer.writerows(transactions)

# 导出为 JSON
import json

def export_to_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### 数据可视化

```python
# 使用 matplotlib 生成图表
import matplotlib.pyplot as plt

def generate_chart(categorized, output_path):
    categories = list(categorized.keys())
    amounts = [sum(t['amount'] for t in trans) for trans in categorized.values()]
    
    plt.figure(figsize=(10, 6))
    plt.bar(categories, amounts)
    plt.title('消费分类统计')
    plt.xlabel('分类')
    plt.ylabel('金额 (¥)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
```
