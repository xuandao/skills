#!/usr/bin/env python3

import tempfile
import os
from pathlib import Path
import re
import sys

# Add the scripts directory to the path to import the module
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

import importlib.util
spec = importlib.util.spec_from_file_location("cmb_debit_auto_analysis", scripts_dir / "cmb-debit-auto-analysis.py")
cmb_debit_auto_analysis = importlib.util.module_from_spec(spec)
sys.modules["cmb_debit_auto_analysis"] = cmb_debit_auto_analysis
spec.loader.exec_module(cmb_debit_auto_analysis)

# Test the actual functionality step by step to see what's happening
print("Testing the original regex pattern in the actual function...")

# Create a transaction and generate a report
transactions = [
    cmb_debit_auto_analysis.Transaction("9583", "03/13", "09:44", "快捷支付", "支付宝-蚂蚁基金", 10.0, 4506.81, "原始邮件内容"),
    cmb_debit_auto_analysis.Transaction("9583", "03/12", None, "定投扣款", "嘉实沪深300", 1000.0, 5506.81, "原始邮件内容")
]

report = cmb_debit_auto_analysis.generate_report(transactions)
print("Generated report has been created.")
print("First, let's look at the transaction table part:")
lines = report.split('\n')
in_table = False
for line in lines:
    if '详细交易记录' in line:
        in_table = True
        print(line)
    elif in_table:
        print(line)
        if '|' not in line and line.strip() == '':
            in_table = False
            break
        elif '----' not in line and '日期' not in line and line.strip().startswith('|'):
            # This is a transaction row
            print(f"  -> Transaction line: {repr(line)}")

print()
print("Testing the actual function's pattern directly...")
# Extract the pattern from the source code
original_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
print(f"Original pattern: {repr(original_pattern)}")

# Find lines that look like transaction records
transaction_lines = []
for line in lines:
    if line.strip().startswith('|') and '¥' in line and ('快捷支付' in line or '定投扣款' in line):
        transaction_lines.append(line.strip())

print(f"Found {len(transaction_lines)} transaction lines:")
for i, line in enumerate(transaction_lines):
    print(f"  Line {i}: {repr(line)}")

    # Test the original pattern on each line
    match = re.search(original_pattern, line)
    print(f"    Original pattern matches: {bool(match)}")
    if match:
        print(f"      Groups: {match.groups()}")

print()
print("Try to debug with a simple test using raw emoji matching...")
# Let's try matching just the emoji part separately
for line in lines:
    if '快捷支付' in line or '定投扣款' in line:
        print(f"Testing line: {repr(line)}")
        # Test simpler pattern for emoji matching
        emoji_pattern = r'(💳 快捷支付|💰 定投扣款)'
        emoji_match = re.search(emoji_pattern, line)
        print(f"  Emoji pattern matches: {bool(emoji_match)}")
        if emoji_match:
            print(f"    Matched: {repr(emoji_match.group(1))}")

        # Test simplified pattern without emoji
        simple_pattern = r'(\S*快捷支付|\S*定投扣款)'
        simple_match = re.search(simple_pattern, line)
        print(f"  Simple pattern matches: {bool(simple_match)}")
        if simple_match:
            print(f"    Matched: {repr(simple_match.group(1))}")