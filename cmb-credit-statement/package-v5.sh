#!/bin/bash

# CMB Statement Skill 打包脚本 v5.0
# 打包更新后的 skill 文件

echo "📦 开始打包 CMB Statement Skill v5.0..."

# 设置变量
SKILL_NAME="cmb-statement-v5"
SKILL_DIR="/Users/xuandao/.openclaw/workspace/skills/cmb-statement"
OUTPUT_DIR="/Users/xuandao/.openclaw/workspace/skills"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
echo "📁 创建临时目录: $TEMP_DIR"

# 复制文件
echo "📋 复制 skill 文件..."
cp -r "$SKILL_DIR"/* "$TEMP_DIR/"

# 创建打包目录
PACKAGE_DIR="$TEMP_DIR/$SKILL_NAME"
mkdir -p "$PACKAGE_DIR"

# 移动文件到打包目录
mv "$TEMP_DIR"/* "$PACKAGE_DIR/" 2>/dev/null || true
rm -rf "$TEMP_DIR"/* 2>/dev/null || true

# 创建 skill 包
echo "📦 创建 skill 包..."
cd "$TEMP_DIR"
tar -czf "$OUTPUT_DIR/${SKILL_NAME}.tar.gz" "$SKILL_NAME"

# 清理临时文件
echo "🧹 清理临时文件..."
rm -rf "$TEMP_DIR"

echo "✅ 打包完成！"
echo "📁 输出文件: $OUTPUT_DIR/${SKILL_NAME}.tar.gz"
echo ""
echo "📊 打包内容："
echo "  - 更新后的分析脚本 (v5.0)"
echo "  - 增强的退货/退款标注功能"
echo "  - 分期账单独立拆分功能"
echo "  - 更新的 SKILL.md 文档"
echo "  - 参考文档和配置指南"
echo ""
echo "🚀 新功能："
echo "  ✅ 自动识别退货/退款并标注"
echo "  ✅ 消费分期单独统计和跟踪"
echo "  ✅ 增强的消费分类统计"
echo "  ✅ 更清晰的分期还款明细"