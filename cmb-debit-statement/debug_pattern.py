#!/usr/bin/env python3

import re

# The transaction line
line_6 = '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁基金 | -¥10.00 | ¥4506.81 |'

# Break down the pattern to test parts
# Original: r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

# Testing first part: date
part1 = r'\|\s*(\d{2}/\d{2})\s*\|'
print("Part 1 (date) pattern:", repr(part1))
match = re.search(part1, line_6)
print("Match date part:", bool(match))
if match:
    print("  Date found:", repr(match.group(1)))
else:
    print("  No match for date part")

print()

# Testing first two parts: date and time
part2 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|'
print("Part 2 (date + time) pattern:", repr(part2))
match = re.search(part2, line_6)
print("Match date+time part:", bool(match))
if match:
    print("  Groups:", match.groups())
else:
    print("  No match for date+time part")

print()

# Testing with first three parts: date, time, account
part3 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|'
print("Part 3 (date + time + account) pattern:", repr(part3))
match = re.search(part3, line_6)
print("Match date+time+account part:", bool(match))
if match:
    print("  Groups:", match.groups())
else:
    print("  No match for date+time+account part")

print()

# Testing with first four parts: date, time, account, type
part4 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|'
print("Part 4 (date + time + account + type) pattern:", repr(part4))
match = re.search(part4, line_6)
print("Match date+time+account+type part:", bool(match))
if match:
    print("  Groups:", match.groups())
else:
    print("  No match for date+time+account+type part")

print()

# Full pattern
full_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
print("Full pattern:", repr(full_pattern))
match = re.search(full_pattern, line_6)
print("Full pattern match:", bool(match))
if match:
    print("  Groups:", match.groups())
else:
    print("  No match for full pattern")

print()
print("Line 6:", repr(line_6))