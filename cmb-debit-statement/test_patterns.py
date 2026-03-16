#!/usr/bin/env python3

import re

# The transaction lines from the generated report
line1 = '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝-蚂蚁基金 | -¥10.00 | ¥4,506.81 |'
line2 = '| 03/12 | - | 9583 | 💰 定投扣款 | 嘉实沪深300 | -¥1,000.00 | ¥5,506.81 |'

print("Testing different patterns:")

# Original problematic pattern
original = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print("1. Original pattern:")
for line_num, line in enumerate([line1, line2], 1):
    match = re.search(original, line)
    print(f"   Line {line_num}: {bool(match)} - {match.groups() if match else 'NO MATCH'}")

print()

# Pattern with escaped emojis
escaped = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(\\U0001f4b3\\s*快\\s*捷\\s*支\\s*付|\\U0001f4b0\\s*定\\s*投\\s*扣\\s*款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
# That won't work literally. Let me try a different approach

# Alternative: use Unicode codepoints for the emojis
import codecs
emoji1_unicode = '\U0001f4b3 快捷支付'  # Credit Card emoji
emoji2_unicode = '\U0001f4b0 定投扣款'  # Money Bag emoji

print("2. Using Unicode escapes in a separate test:")
print(f"   Emoji 1 (Credit Card + 快捷支付): {repr(emoji1_unicode)}")
print(f"   Emoji 2 (Money Bag + 定投扣款): {repr(emoji2_unicode)}")

# Test if we can match just the emoji part
credit_card_match = re.search(r'\U0001f4b3\s*快捷支付', line1)
print(f"   Credit card match in line1: {bool(credit_card_match)}")

money_bag_match = re.search(r'\U0001f4b0\s*定投扣款', line2)
print(f"   Money bag match in line2: {bool(money_bag_match)}")

print()

# Let's create a working pattern by replacing emoji expressions with broader matches
# Since we know the emojis are there, we can use a more general pattern that matches the format
working_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*([^|]*?[快定][^|]*?[捷投][^|]*?[支付款])\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print("3. Working pattern (generic type matching):")
for line_num, line in enumerate([line1, line2], 1):
    match = re.search(working_pattern, line)
    print(f"   Line {line_num}: {bool(match)} - {match.groups() if match else 'NO MATCH'}")

print()

# Or a more precise approach: use alternation but with proper Unicode handling
precise_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*((?:\U0001f4b3|\U0001f4b0)\s*[^\d\s]+\s+[^\d\s]+)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print("4. Precise pattern (using Unicode escapes):")
for line_num, line in enumerate([line1, line2], 1):
    match = re.search(precise_pattern, line)
    print(f"   Line {line_num}: {bool(match)} - {match.groups() if match else 'NO MATCH'}")

print()

# Most practical approach: use a general character class that captures the pattern we need
practical_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*([^\|]*?快.*?支付|[^\|]*?定.*?扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print("5. Practical pattern (using regex alternation with general match):")
for line_num, line in enumerate([line1, line2], 1):
    match = re.search(practical_pattern, line)
    print(f"   Line {line_num}: {bool(match)} - {match.groups() if match else 'NO MATCH'}")