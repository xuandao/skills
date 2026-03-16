---
name: cmb-credit-statement
description: 自动从 Gmail 拉取招商银行信用卡账单（月度/每日），解析交易记录并生成带动态计算的分析报告到 Obsidian。使用方法：直接说"分析招商银行账单"或"check CMB statement"。
---

# CMB Credit Card Statement Analyzer v6.0

自动从 Gmail 拉取招商银行信用卡账单，解析交易记录并生成**带动态计算**的分析报告到 Obsidian。

## 🆕 新增功能 (v6.0)

- **每日交易支持**: 新增"每日信用管家"邮件解析，支持单日/多日汇总
- **报表目录配置**: 支持命令行 `--output-dir` 参数自定义保存路径
- **外币自动转换**: 美元/港币等外币交易自动按汇率转换为 CNY 统计
- **日月分离**: 月度账单与每日交易独立处理，互不干扰

## 🆕 保留功能 (v5.1)

- **消费分类统计优化**: 按金额倒序排列，「其他」放最后，新增合计行与应还金额一致
- **分期过滤逻辑**: 基于金额匹配自动排除已退货的分期（含对应本金记录）
- **自动过滤退款**: 已退款的交易对（支出+退款）在交易明细中不显示
- **智能关键词匹配**: 关键词扩展至 7 大类别，大小写不敏感

## 🆕 保留功能 (v5.0)

- **退货/退款自动标注**: 自动识别并标注退货和退款交易
- **分期账单独立拆分**: 消费分期单独统计，便于跟踪还款进度
- **增强分类统计**: 分类从 5 类扩展到 7 类，新增「投资理财」分类

## 主要功能

### 月度账单
- 📧 从 Gmail 自动拉取招商银行信用卡月度账单
- 📄 解析 HTML 格式账单（账单概况 + 交易明细）
- 💳 分卡消费统计（按卡号汇总）
- 💰 智能分类消费（餐饮、购物、交通、娱乐、生活、分期等）
- 💳 消费分期独立统计（本期金额 + 剩余待还）
- 🔄 自动识别退货/退款交易
- 📊 生成可视化分析报告
- 💾 自动保存到 Obsidian 笔记

### 每日交易
- 📧 从 Gmail 自动拉取"每日信用管家"邮件
- 📅 支持单日/多日汇总（1 个汇总文件）
- 💱 外币交易自动转 CNY（USD/HKD/EUR 等）
- 💰 智能消费分类
- 📊 按卡号分组展示交易明细
- 💾 自动保存到 Obsidian 笔记

## 使用方法

### 命令行运行

```bash
# ============ 月度账单 ============
# 默认：拉取最新一份月度账单
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-monthly-statement.py

# 自定义输出目录
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-monthly-statement.py --output-dir /path/to/output

# 自定义 Gmail 查询
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-monthly-statement.py --query "subject:信用卡账单 newer_than:30d"

# ============ 每日交易 ============
# 默认：拉取最近 1 天的交易
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-daily-statement.py

# 拉取最近 7 天的交易（汇总到 1 个文件）
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-daily-statement.py --days 7

# 指定日期
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-daily-statement.py --date 2026-03-14

# 自定义输出目录
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-daily-statement.py --output-dir /path/to/output

# 组合参数
python3 ~/.openclaw/workspace/skills/cmb-credit-statement/scripts/cmb-daily-statement.py -d 3 -o /path/to/output
```

### OpenClaw 中使用

```
# 月度账单
- "分析招商银行账单"
- "check CMB statement"
- "拉取本月信用卡账单"

# 每日交易
- "拉取最近 7 天信用卡交易"
- "昨日信用卡消费"
- "check CMB daily statement"
```

## 📁 输出文件

| 类型 | 文件名格式 | 说明 |
|------|-----------|------|
| 月度账单 | `YYYYMM-信用卡账单分析.md` | 月度汇总分析报告 |
| 每日交易 | `YYYYMMDD-信用卡日账单.md` | 单日/多日汇总报告 |

## 配置

### 默认配置

编辑脚本中的 `DEFAULT_CONFIG`：

```python
# cmb-monthly-statement.py 或 cmb-daily-statement.py
DEFAULT_CONFIG = {
    "gmail_query": "(from:招商银行 OR from:cmbchina.com) subject:信用卡电子账单 newer_than:90d",
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",
}
```

### 命令行参数

**月度账单参数：**
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --output-dir | -o | 自定义输出目录 | 配置文件路径 |
| --query | -q | 自定义 Gmail 查询 | 配置文件查询 |
| --max-results | -m | 最多处理邮件数 | 1 |

**每日交易参数：**
| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --days | -d | 拉取最近 N 天交易 | 1 |
| --date | | 指定日期 (YYYY-MM-DD) | 无 |
| --output-dir | -o | 自定义输出目录 | 配置文件路径 |
| --query | -q | 自定义 Gmail 查询 | 配置文件查询 |

## 汇率配置

在 `cmb_common.py` 中配置汇率：

```python
EXCHANGE_RATES = {
    "CNY": 1.0,
    "USD": 7.25,  # 美元兑人民币
    "HKD": 0.93,  # 港币兑人民币
    "EUR": 7.85,  # 欧元兑人民币
    "JPY": 0.048, # 日元兑人民币
    "GBP": 9.15,  # 英镑兑人民币
}
```

## 依赖

- `gws` (Gmail API 命令行工具)
- Python 3.9+
- Obsidian Dataview 插件（用于动态计算）

## 文件结构

```
cmb-credit-statement/
├── SKILL.md                        # 使用说明
├── scripts/
│   ├── cmb-monthly-statement.py    # 月度账单处理器
│   ├── cmb-daily-statement.py      # 每日交易处理器
│   ├── cmb_common.py               # 公共模块（分类、汇率等）
│   ├── process-pdf-batch.py        # PDF 批处理（遗留）
│   ├── cmb-auto-analysis.py        # 旧版（保留兼容）
│   └── ...
├── references/
│   ├── configuration.md            # 配置指南
│   ├── statement-format.md         # 账单格式说明
│   ├── dataview-guide.md           # Dataview 使用指南
│   └── daily-statement-format.md   # 日账单格式说明
└── templates/
    ├── monthly-report-template.md  # 月报模板
    └── daily-report-template.md    # 日报模板
```

## 更新日志

- **v6.0** (2026-03-15): 新增每日交易支持（每日信用管家邮件解析）；新增--output-dir 命令行参数；外币自动转 CNY；日月账单分离处理
- **v5.1** (2026-03-14): 消费分类统计优化（倒序 + 合计），分期过滤逻辑（基于金额匹配排除已退货），关键词扩展至 7 大类
- **v5.0** (2026-03-14): 新增退货/退款自动标注，分期账单独立拆分功能
- **v4.0** (2026-03-07): 新增 Dataview 动态计算，支持手动编辑后自动更新统计
- **v3.1** (2026-03-07): 添加 PDF 批处理脚本，完成 2025 全年账单梳理
- **v3.0** (2026-03-07): 移除 PDF 解析，专注 HTML 邮件账单，新增分卡统计
- **v2.0** (2026-03-07): 新增 HTML 正文账单支持，优先处理无附件账单
- **v1.0** (2026-03-07): 初始版本，仅支持 PDF 附件

## 参考文档

- [配置指南](references/configuration.md)
- [账单格式说明](references/statement-format.md)
- [Dataview 使用说明](references/dataview-guide.md)
