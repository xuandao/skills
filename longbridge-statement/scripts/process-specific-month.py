#!/usr/bin/env python3
"""
处理指定月份的长桥月结单
用法: python3 process-specific-month.py 202501
"""

import sys
import json
import subprocess
import re
from pathlib import Path

if len(sys.argv) < 2:
    print("用法: python3 process-specific-month.py YYYYMM")
    sys.exit(1)

target_month = sys.argv[1]

print(f"\n=== 处理 {target_month} 月结单 ===\n")

# 1. 搜索所有月结单
print("📧 搜索月结单...")
result = subprocess.run([
    "gws", "gmail", "users", "messages", "list",
    "--params", json.dumps({
        "userId": "me",
        "q": "from:noreply@longbridge.hk subject:月结单",
        "maxResults": 50
    })
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ 搜索失败: {result.stderr}")
    sys.exit(1)

messages = json.loads(result.stdout).get("messages", [])
print(f"✅ 找到 {len(messages)} 封邮件")

# 2. 查找目标月份的邮件
print(f"🔍 查找 {target_month}...")
target_message_id = None

for msg in messages:
    result = subprocess.run([
        "gws", "gmail", "users", "messages", "get",
        "--params", json.dumps({"userId": "me", "id": msg["id"]})
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        continue
    
    message = json.loads(result.stdout)
    parts = message["payload"].get("parts", [message["payload"]])
    
    for part in parts:
        filename = part.get("filename", "")
        if f"statement-monthly-{target_month}" in filename:
            target_message_id = msg["id"]
            print(f"✅ 找到邮件: {msg['id']}")
            print(f"   附件: {filename}")
            break
    
    if target_message_id:
        break

if not target_message_id:
    print(f"❌ 未找到 {target_month} 的月结单")
    sys.exit(1)

# 3. 读取原始脚本并修改
print(f"\n📝 准备分析脚本...")
script_path = Path(__file__).parent / "longbridge-monthly-analysis.py"

with open(script_path, "r", encoding="utf-8") as f:
    script_content = f.read()

# 修改脚本：将 maxResults 改为 50，并指定邮件ID
modified_script = script_content.replace(
    'data["messages"][0]["id"]',
    f'"{target_message_id}"'
).replace(
    '"maxResults": 1',
    '"maxResults": 50'
)

# 4. 执行修改后的脚本
print(f"🤖 开始分析...\n")
result = subprocess.run(
    [sys.executable, "-c", modified_script],
    cwd=Path(__file__).parent
)

if result.returncode == 0:
    print(f"\n✅ {target_month} 处理成功！")
else:
    print(f"\n❌ {target_month} 处理失败")
    sys.exit(1)
