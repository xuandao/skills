#!/bin/bash
set -e

SRC="/Users/xuandao/.openclaw/workspace/skills"
DEST="/Users/xuandao/work/xuandao/skills"

echo "🔄 同步 skills..."
echo "源目录: $SRC"
echo "目标目录: $DEST"

# 确保目标目录存在
mkdir -p "$DEST"

# 全量覆盖复制（删除目标目录中源目录没有的文件，但保留 .git）
rsync -av --delete --exclude='.git' "$SRC/" "$DEST/"

echo "✅ 复制完成"

# 进入目标目录执行 git 操作
cd "$DEST"

# 检查是否有变更
if [ -z "$(git status --porcelain)" ]; then
    echo "📭 没有变更需要提交"
    exit 0
fi

# 添加所有变更
git add -A

# 提交
git commit -m "Sync skills from workspace ($(date +%Y-%m-%d %H:%M:%S))"

# 推送
git push origin main

echo "✅ 同步完成并推送到远程"
