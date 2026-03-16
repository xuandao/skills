#!/bin/bash
# 测试长桥月结单定时任务
# 模拟 cron 环境运行脚本

echo "=== 测试长桥月结单定时任务 ==="
echo "时间: $(date)"
echo ""

# 设置环境变量（cron 环境下可能缺少）
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin"
export HOME="/Users/xuandao"

# 运行脚本
echo "运行脚本..."
/usr/bin/python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-monthly-analysis.py

echo ""
echo "退出码: $?"
echo "完成时间: $(date)"
