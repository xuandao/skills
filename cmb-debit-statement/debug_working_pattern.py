#!/usr/bin/env python3

import tempfile
import os
from pathlib import Path
import re
import sys

# Test what format would actually work by using simpler text instead of emojis
working_content = """# 招商银行一卡通账单 - 2026 年03 月

**更新时间**: 2026-03-15 13:25:31

---

## 📊 账单概况

### 💳 账户统计

| 账户 | 快捷支付笔数 | 快捷支付金额 | 定投扣款笔数 | 定投扣款金额 | 最后余额 |
|------|-------------|-------------|-------------|-------------|----------|
| 9583 | 1 | ¥ 10.00 | 0 | ¥ 0.00 | ¥ 4506.81 |

**汇总**: 快捷支付 1 笔 ¥10.00 | 定投扣款 0 笔 ¥0.00

## 📝 详细交易记录

| 日期 | 时间 | 账户 | 类型 | 描述 | 金额 | 余额 |
|------|------|------|------|------|------|------|
| 03/13 | 09:44 | 9583 | 快捷支付 | 支付宝-蚂蚁基金 | -¥10.00 | ¥4506.81 |
| 03/12 | - | 9583 | 定投扣款 | 嘉实沪深300 | -¥1000.00 | ¥5506.81 |

---

*注：本报告由程序自动生成，数据来源于 Gmail 邮件解析*

"""

print("Testing with simplified content (no emoji in the matching part):")
print(working_content)
print()

# Test a more generic pattern that doesn't rely on specific emoji characters
generic_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(.*?)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

matches = list(re.finditer(generic_pattern, working_content))
print(f"Generic pattern found {len(matches)} matches")
for i, match in enumerate(matches):
    print(f"  Match {i+1}: {match.groups()}")
    print(f"    Type: {repr(match.group(4))}")
    print(f"    Description: {repr(match.group(5))}")

print()
# Test the specific pattern with actual emoji values
specific_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(.*?快捷支付|.*?定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

specific_matches = list(re.finditer(specific_pattern, working_content))
print(f"Specific pattern found {len(specific_matches)} matches")
for i, match in enumerate(specific_matches):
    print(f"  Match {i+1}: {match.groups()}")
    print(f"    Type: {repr(match.group(4))}")
    print(f"    Description: {repr(match.group(5))}")

print()
# Try using the actual content from the generated report by running the generate_report function
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import importlib.util
spec = importlib.util.spec_from_file_location("cmb_debit_auto_analysis", scripts_dir / "cmb-debit-auto-analysis.py")
cmb_debit_auto_analysis = importlib.util.module_from_spec(spec)
sys.modules["cmb_debit_auto_analysis"] = cmb_debit_auto_analysis
spec.loader.exec_module(cmb_debit_auto_analysis)

# Create some test transactions
transactions = [
    cmb_debit_auto_analysis.Transaction("9583", "03/13", "09:44", "快捷支付", "支付宝-蚂蚁基金", 10.0, 4506.81, ""),
    cmb_debit_auto_analysis.Transaction("9583", "03/12", None, "定投扣款", "嘉实沪深300", 1000.0, 5506.81, ""),
]

# Generate a real report
report = cmb_debit_auto_analysis.generate_report(transactions)
print("Generated report:")
print(report)
print()

# Now test parsing the real report
generated_matches = list(re.finditer(specific_pattern, report))
print(f"Pattern matches in generated report: {len(generated_matches)}")
for i, match in enumerate(generated_matches):
    print(f"  Match {i+1}: {match.groups()}")

# And test the actual function with this generated report
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
    f.write(report)
    temp_file_path = f.name

try:
    result = cmb_debit_auto_analysis.parse_existing_transactions(Path(temp_file_path))
    print(f"\nActual function result: {len(result)} transactions")
    for i, trans in enumerate(result):
        print(f"  Transaction {i+1}: {trans.date} {trans.time} {trans.account} {trans.transaction_type} '{trans.description}' {trans.amount} {trans.balance}")
finally:
    os.unlink(temp_file_path)