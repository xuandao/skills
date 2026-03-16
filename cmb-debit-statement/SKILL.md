---
name: cmb-debit-statement
description: 自动从 Gmail 拉取招商银行一卡通账户变动通知邮件，解析交易记录并生成账单到 Obsidian。使用方法：直接说"一卡通账单"或"check CMB debit statement"。
---

# CMB Debit Card Statement Analyzer

自动从 Gmail 拉取招商银行一卡通账户变动通知邮件，解析交易记录并生成账单到 Obsidian。

## 主要功能

- 📧 从 Gmail 自动拉取招商银行一卡通账户变动通知
- 💳 支持以下邮件格式解析：
  - **快捷支付**：
    - 完整格式：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元，余额 XX.XX
    - 无余额格式：您账户 XXXX 于 MM 月 DD 日 HH:mm 在 XXXX 快捷支付 XX.XX 元（余额字段缺失）
  - **定投扣款**：
    - 标准格式：您尾号 XXXX 的账户于 MM 月 DD 日执行「XXXX」的定投计划，扣款 XX 元，活期余额 XX.XX 元
    - 简化格式：您尾号为 XXXX 的账户于 MM 月 DD 日定投「XXXX」XX 元，活期余额 XX.XX 元
- 📅 支持按天、周、月过滤查询邮件
- 📊 生成交易汇总统计（按账户、按商户、按产品）
- 💾 自动保存到 Obsidian 笔记，月度数据自动合并去重

## 使用方法

### 命令行运行

```bash
# 默认：拉取最近 7 天（周）的交易
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py

# 按天：拉取最近 1 天的交易
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py --period day

# 按月：拉取最近 30 天的交易
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py --period month

# 自定义天数
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py --days 15

# 指定输出目录
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py --output-dir /path/to/obsidian/Areas/理财/招商银行

# 简写形式
python3 ~/.openclaw/workspace/skills/cmb-debit-statement/scripts/cmb-debit-auto-analysis.py -o /path/to/output
```

### OpenClaw 中使用

直接说：
- "一卡通账单"
- "check CMB debit statement"
- "拉取最近一周的一卡通交易"
- "拉取本月一卡通账单"

## 配置

编辑 `scripts/cmb-debit-auto-analysis.py` 中的配置：

```python
CONFIG = {
    # Gmail 查询条件（days 会被动态替换）
    "gmail_query_template": "一卡通账户变动通知 newer_than:{days}d",

    # Obsidian 保存路径
    "obsidian_dir": Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/理财/招商银行",

    # 账户过滤（可选）：只处理特定尾号的账户
    "account_filter": [],  # 例如：["9583", "0707"]，空数组表示不过滤
}
```

## 输出示例

生成的 Markdown 报告包含：

### 账单概况
- 📅 账单周期
- 💳 涉及账户
- 💰 总收入/总支出
- 📊 账户余额变化

### 交易分类统计
| 分类 | 笔数 | 金额 |
|------|------|------|
| 快捷支付 | 10 | ¥ 1,234.56 |
| 定投扣款 | 5 | ¥ 500.00 |

### 详细交易记录
| 日期 | 时间 | 账户 | 类型 | 描述 | 金额 | 余额 |
|------|------|------|------|------|------|------|
| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁（杭州）基金 | -10.00 | 4506.81 |

**文件命名格式**:
- `YYYYMM-一卡通账单.md`（月度账单，统一格式）
- 每次运行脚本时，会自动读取已有文件，合并交易记录（去重），重新生成完整报告

## 解析规则

详见 [references/parse-rules.md](references/parse-rules.md)

## 依赖

- `gws` (Gmail API 命令行工具)
- Python 3.9+

## 更新日志

- **v1.3** (2026-03-15): 修改为数据合并模式，每次运行自动读取已有交易，去重后重新生成完整报告
- **v1.2** (2026-03-15): 新增快捷支付无余额格式支持；新增 `--output-dir` 参数支持自定义输出目录
- **v1.1** (2026-03-15): 新增简化定投格式支持（"尾号为 XXXX"格式）
- **v1.0** (2026-03-15): 初始版本，支持快捷支付和定投扣款两种格式
