#!/usr/bin/env python3

import tempfile
from pathlib import Path
import re
import sys

# Define the sample content exactly as in the test
sample_content = """# 招商银行一卡通账单 - 2026 年03 月

## 📝 详细交易记录

| 日期 | 时间 | 账户 | 类型 | 描述 | 金额 | 余额 |
|------|------|------|------|------|------|------|
| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁基金 | -¥10.00 | ¥4506.81 |
| 03/12 | - | 9583 | 💰 定投扣款 | 嘉实沪深300 | -¥1000.00 | ¥5506.81 |

"""

print("Full sample content:")
print(repr(sample_content))
print()

# Split into lines
lines = sample_content.split('\n')
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")

# The specific lines containing transactions are line 6 and 7
print()
print("Testing the transaction lines individually:")
line_6 = lines[6]  # '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁基金 | -¥10.00 | ¥4506.81 |'
line_7 = lines[7]  # '| 03/12 | - | 9583 | 💰 定投扣款 | 嘉实沪深300 | -¥1000.00 | ¥5506.81 |'

print(f"Line 6: {repr(line_6)}")
print(f"Line 7: {repr(line_7)}")

# The regex pattern from the actual function
pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print()
print("Pattern:", repr(pattern))

print()
print("Testing pattern on line_6:")
matches_6 = list(re.finditer(pattern, line_6))
print(f"Found {len(matches_6)} matches on line_6")

for i, match in enumerate(matches_6):
    print(f"  Match {i+1}:")
    print(f"    Full match: {repr(match.group(0))}")
    print(f"    Groups: {match.groups()}")
    print(f"    Group 1 (date): {repr(match.group(1))}")
    print(f"    Group 2 (time): {repr(match.group(2))}")
    print(f"    Group 3 (account): {repr(match.group(3))}")
    print(f"    Group 4 (type): {repr(match.group(4))}")
    print(f"    Group 5 (desc): {repr(match.group(5))}")
    print(f"    Group 6 (amount): {repr(match.group(6))}")
    print(f"    Group 7 (balance): {repr(match.group(7))}")

print()
print("Testing pattern on line_7:")
matches_7 = list(re.finditer(pattern, line_7))
print(f"Found {len(matches_7)} matches on line_7")

for i, match in enumerate(matches_7):
    print(f"  Match {i+1}:")
    print(f"    Full match: {repr(match.group(0))}")
    print(f"    Groups: {match.groups()}")
    print(f"    Group 1 (date): {repr(match.group(1))}")
    print(f"    Group 2 (time): {repr(match.group(2))}")
    print(f"    Group 3 (account): {repr(match.group(3))}")
    print(f"    Group 4 (type): {repr(match.group(4))}")
    print(f"    Group 5 (desc): {repr(match.group(5))}")
    print(f"    Group 6 (amount): {repr(match.group(6))}")
    print(f"    Group 7 (balance): {repr(match.group(7))}")

print()
print("Testing the actual pattern with temporary file approach to reproduce the original issue...")
# Now let's test using the actual function with a real file
import os

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
    f.write(sample_content)
    temp_file_path = f.name

try:
    # Add the scripts directory to the path to import the module
    scripts_dir = Path(__file__).parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    # Import the module using importlib since the filename contains hyphens
    import importlib.util
    spec = importlib.util.spec_from_file_location("cmb_debit_auto_analysis", scripts_dir / "cmb-debit-auto-analysis.py")
    cmb_debit_auto_analysis = importlib.util.module_from_spec(spec)
    sys.modules["cmb_debit_auto_analysis"] = cmb_debit_auto_analysis
    spec.loader.exec_module(cmb_debit_auto_analysis)

    result = cmb_debit_auto_analysis.parse_existing_transactions(Path(temp_file_path))
    print(f"Function parse_existing_transactions returned {len(result)} transactions")
    for i, trans in enumerate(result):
        print(f"  Transaction {i+1}: {trans.date} {trans.account} {trans.description} {trans.amount}")
finally:
    os.unlink(temp_file_path)