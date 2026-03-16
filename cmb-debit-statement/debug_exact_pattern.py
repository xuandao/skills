#!/usr/bin/env python3

import re

# The transaction line
line_6 = '| 03/13 | 09:44 | 9583 | 💳 快捷支付 | 支付宝 - 蚂蚁基金 | -¥10.00 | ¥4506.81 |'

# The exact pattern from the source code
pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*(💳 快捷支付|💰 定投扣款)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'

print("Using exact pattern from source:")
print("Pattern:", repr(pattern))
print()

match = re.search(pattern, line_6)
print("Does pattern match line_6?", bool(match))
if match:
    print("Groups:", match.groups())
    print("Group 1 (date):", repr(match.group(1)))
    print("Group 2 (time):", repr(match.group(2)))
    print("Group 3 (account):", repr(match.group(3)))
    print("Group 4 (type):", repr(match.group(4)))
    print("Group 5 (description):", repr(match.group(5)))
    print("Group 6 (amount):", repr(match.group(6)))
    print("Group 7 (balance):", repr(match.group(7)))
else:
    print("No match!")

print()
print("Let's also test with re.DOTALL flag which might be used when processing multi-line content:")
match_dotall = re.search(pattern, line_6, re.DOTALL)
print("With DOTALL flag:", bool(match_dotall))

print()
# Let's see what happens if we escape the emojis in the pattern
# Some regex engines might have trouble with emoji characters
emoji_test = "💳 快捷支付"
print("Emoji test:", repr(emoji_test))
import unicodedata
for i, char in enumerate(emoji_test):
    print(f"Character {i}: {repr(char)}, name: {unicodedata.name(char, 'UNNAMED')}")

print()
# Test a simpler approach with character classes for the type field
simple_pattern = r'\|\s*(\d{2}/\d{2})\s*\|\s*(-|\d{2}:\d{2})\s*\|\s*(\d{4})\s*\|\s*([^\|]+?)\s*\|\s*(.+?)\s*\|\s*-¥([\d,]+)\s*\|\s*¥([\d,]+)\s*\|'
simple_match = re.search(simple_pattern, line_6)
print("Simple pattern match (using [^|] for type):", bool(simple_match))
if simple_match:
    print("Groups:", simple_match.groups())