#!/usr/bin/env python3
"""
批量处理长桥月结单
使用完整的分析格式（与单月分析相同）
"""

import subprocess
import json
import time
import sys
from pathlib import Path

# 配置
TARGET_MONTHS = [
    "202501", "202502", "202503", "202504", "202505", "202506",
    "202507", "202508", "202509", "202510", "202511", "202512",
    "202601"
]

SCRIPT_DIR = Path(__file__).parent
MONTHLY_SCRIPT = SCRIPT_DIR / "longbridge-monthly-analysis.py"

def main():
    print("\n=== 长桥证券月结单批量分析 ===\n")
    print(f"目标月份: {', '.join(TARGET_MONTHS)}\n")
    print("⚠️  预计需要 30-40 分钟，请耐心等待...\n")
    
    # 1. 获取所有月结单邮件
    print("📧 获取所有月结单...")
    result = subprocess.run([
        "gws", "gmail", "users", "messages", "list",
        "--params", json.dumps({
            "userId": "me",
            "q": "from:noreply@longbridge.hk subject:月结单",
            "maxResults": 50
        })
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 搜索邮件失败: {result.stderr}")
        return 1
    
    messages = json.loads(result.stdout).get("messages", [])
    print(f"✅ 找到 {len(messages)} 封邮件\n")
    
    # 2. 构建月份到邮件ID的映射
    print("📋 识别目标月结单...")
    month_to_id = {}
    
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
            if "statement-monthly-" in filename and filename.endswith(".pdf"):
                import re
                month_match = re.search(r"(\d{6})", filename)
                if month_match:
                    month = month_match.group(1)
                    if month in TARGET_MONTHS:
                        month_to_id[month] = msg["id"]
                        print(f"  ✅ {month}")
                        break
    
    print(f"\n找到 {len(month_to_id)} 份目标月结单\n")
    
    if not month_to_id:
        print("❌ 未找到任何目标月结单")
        return 1
    
    # 3. 按月份顺序处理
    print("开始批量处理...\n")
    success_count = 0
    
    for i, month in enumerate(sorted(month_to_id.keys()), 1):
        print(f"[{i}/{len(month_to_id)}] 📄 处理 {month}...")
        
        # 读取原始脚本
        with open(MONTHLY_SCRIPT, "r", encoding="utf-8") as f:
            script_content = f.read()
        
        # 修改脚本：替换查询条件为指定邮件ID
        modified_script = script_content.replace(
            '"maxResults": 1',
            '"maxResults": 50'
        ).replace(
            'data["messages"][0]["id"]',
            f'"{month_to_id[month]}"'
        )
        
        # 执行修改后的脚本
        result = subprocess.run(
            [sys.executable, "-c", modified_script],
            capture_output=True,
            text=True,
            cwd=SCRIPT_DIR
        )
        
        if result.returncode == 0:
            print(f"  ✅ 成功\n")
            success_count += 1
        else:
            print(f"  ❌ 失败")
            # 只显示错误的前100个字符
            error_msg = result.stderr.strip()
            if error_msg:
                print(f"     {error_msg[:100]}")
            print()
        
        # 避免API限流
        if i < len(month_to_id):
            time.sleep(2)
    
    print(f"\n✅ 完成！成功处理 {success_count}/{len(month_to_id)} 份月结单\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
