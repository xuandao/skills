---
name: obsidian-to-about
description: 将 Obsidian 收藏夹同步到 about 项目（Next.js 博客）。遵循 BOOKMARK_RULES.md 规范，提取元数据并生成 AI 摘要格式。
---

# Obsidian 到 About 同步技能

定时将 Obsidian 中的收藏夹同步到 about 项目，用于构建个人网站。

## 源目录

- **收藏夹**: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Resources/收藏夹/`

## 目标目录

- **收藏夹**: `/Users/xuandao/.openclaw/workspace/git/about/content/bookmarks/`

## 同步逻辑

### 收藏夹同步

1. 扫描 Obsidian 收藏夹目录中的所有 `.md` 文件。
2. 提取文件名或 frontmatter 中的日期（格式：`YYYY-MM-DD`）。
3. 检查目标目录是否已存在同名文件。
4. 如果不存在，按照 `BOOKMARK_RULES.md` 格式进行转换：
   - **元数据映射**: `title` (标题), `url` (来源), `date` (日期), `tags` (标签数组), `description` (描述), `summary` (摘要)。
   - **摘要提取**: 优先从 Obsidian 的 `summary` 字段提取，若无则尝试从正文的 `## 摘要` 或第一个引用块提取。
   - **格式规范**: 使用标准 YAML frontmatter，`tags` 为 JSON 数组格式。

### 文件内容模板 (遵循 BOOKMARK_RULES.md)

```markdown
---
title: "文章标题"
url: "原始链接"
date: "YYYY-MM-DD"
tags: ["标签1", "标签2"]
description: "描述内容"
summary: "AI 生成的精炼摘要"
---

# 文章标题

正文内容...
```

## 触发方式

- Cron 定时任务调用（默认每天凌晨 2 点）
- 手动执行：说"同步 Obsidian 到 about"

## Git 提交

- 提交信息: `sync(obsidian): 同步收藏夹 - YYYY-MM-DD HH:mm`
- 自动拉取、提交并推送到远程仓库。

