#!/usr/bin/env python3

import re

# Test simple parts of the pattern individually
line1 = '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝-蚂蚁基金 | -¥10.00 | ¥4,506.81 |'

# Break down the original pattern
# r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

# Part 1: date and time
p1 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|'
print("Part 1 (date and time):", re.search(p1, line1) is not None)

# Part 2: add account number
p2 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|'
print("Part 2 (with account):", re.search(p2, line1) is not None)

# Part 3: add type (this is where it might fail)
p3 = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|'
print("Part 3 (with type):", re.search(p3, line1) is not None)

# Full pattern with verbose debugging
print()
print("Full pattern breakdown:")
pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print(f"Pattern: {repr(pattern)}")
print(f"Line: {repr(line1)}")

# Check character by character for any hidden characters
print()
print("Character analysis:")
for i, char in enumerate(line1):
    print(f"{i:2d}: {repr(char)} ({ord(char)})")

# Test each group separately in the actual line
print()
print("Testing the actual string segments in the line:")
segments = line1.split('|')
for i, seg in enumerate(segments):
    print(f"Segment {i}: {repr(seg.strip())}")

# Manually construct the pattern to ensure each part matches
print()
print("Testing manual reconstruction:")
parts = [
    r'\|\s*',  # Start with |
    r'(\d{2}/\d{2})',  # Date: 03/13
    r'\s*\|\s*',  # | with whitespace
    r'(-|\d{2}:\d{2})',  # Time: 09:44
    r'\s*\|\s*',  # | with whitespace
    r'(\d{4})',  # Account: 9583
    r'\s*\|\s*',  # | with whitespace
    r'(💳 快捷支付|💰 定投扣款)',  # Type: 💳 快捷支付
    r'\s*\|\s*',  # | with whitespace
    r'(.+?)',  # Description: 支付宝-蚂蚁基金
    r'\s*\|\s*',  # | with whitespace
    r'-¥([\d,]+)',  # Amount: -¥10.00
    r'\s*\|\s*',  # | with whitespace
    r'¥([\d,]+)',  # Balance: ¥4,506.81
    r'\s*\|'  # End with |
]

manual_pattern = ''.join(parts)
print(f"Manual pattern: {repr(manual_pattern)}")
manual_match = re.search(manual_pattern, line1)
print(f"Manual pattern matches: {bool(manual_match)}")
if manual_match:
    print(f"Groups: {manual_match.groups()}")