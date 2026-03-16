#!/usr/bin/env python3

import tempfile
import os
from pathlib import Path
import re
import sys

# Create a test file with the exact format that the function would normally process
# Based on the source code, let's make a realistic test
realistic_content = """# 招商银行一卡通账单 - 2026 年03 月

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
| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝-蚂蚁基金 | -¥10.00 | ¥4506.81 |
| 03/12 | - | 9583 | 💰 定投扣款 | 嘉实沪深300 | -¥1000.00 | ¥5506.81 |

---

*注：本报告由程序自动生成，数据来源于 Gmail 邮件解析*

"""

print("Realistic content for testing:")
print(realistic_content)
print()

# Create a temporary file
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md', encoding='utf-8') as f:
    f.write(realistic_content)
    temp_file_path = f.name

print(f"Created temp file: {temp_file_path}")

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

    # Test the actual function
    result = cmb_debit_auto_analysis.parse_existing_transactions(Path(temp_file_path))
    print(f"Function parse_existing_transactions returned {len(result)} transactions")
    for i, trans in enumerate(result):
        print(f"  Transaction {i+1}: {trans.date} {trans.time} {trans.account} {trans.transaction_type} '{trans.description}' {trans.amount} {trans.balance}")

    # Also let's manually check what the regex finds in the content
    pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
    print(f"\nTesting pattern directly: {repr(pattern)}")

    matches = list(re.finditer(pattern, realistic_content))
    print(f"Direct regex found {len(matches)} matches")
    for i, match in enumerate(matches):
        print(f"  Match {i+1}: {match.groups()}")

finally:
    os.unlink(temp_file_path)