#!/usr/bin/env python3

import re

# The transaction line
line_6 = '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁基金 | -¥10.00 | ¥4506.81 |'

# Test the problematic part specifically
# Pattern before description: \|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*
# Then description: (.+?)
# Then end of description: \s*\|\s*-¥
# Then amount: ([\d,]+)
# Then end: \s*\|\s*¥
# Then balance: ([\d,]+)
# Then end: \s*\|

before_desc = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*'
after_desc = r'\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
full_pattern = before_desc + r'(.+?)' + after_desc

print("Before description part:", repr(before_desc))
print("After description part:", repr(after_desc))
print("Full pattern:", repr(full_pattern))
print()

# Let's manually decompose the line to understand the pipe splitting
parts = [p.strip() for p in line_6.split('|')]
print("Parts after splitting by | and stripping:")
for i, part in enumerate(parts):
    print(f"  [{i}]: {repr(part)}")

print()
print("Looking for the '支付宝 - 蚂蚁基金' part...")
for i, part in enumerate(parts):
    if '支付宝' in part:
        print(f"Found '支付宝' in part [{i}]: {repr(part)}")

print()
# Test if our regex captures properly
match = re.search(full_pattern, line_6)
print("Full pattern matches:", bool(match))
if match:
    print("Groups:", match.groups())
    print("Group 1 (date):", repr(match.group(1)))
    print("Group 2 (time):", repr(match.group(2)))
    print("Group 3 (account):", repr(match.group(3)))
    print("Group 4 (type):", repr(match.group(4)))
    print("Group 5 (description):", repr(match.group(5)))
    print("Group 6 (amount):", repr(match.group(6)))
    print("Group 7 (balance):", repr(match.group(7)))

print()
# Let's also test if there are invisible characters in our test data
print("Raw line:", repr(line_6))
print("Characters in description part:")
desc_start = line_6.find('支付宝')
desc_end = line_6.find('| -¥10.00')
if desc_start != -1 and desc_end != -1:
    desc_part = line_6[desc_start:desc_end].strip()
    print(f"Description segment: {repr(desc_part)}")
    print("Individual characters:")
    for i, char in enumerate(desc_part):
        print(f"  [{i}]: {repr(char)} ord={ord(char)}")