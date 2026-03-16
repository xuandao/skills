---
name: obsidian-to-about
description: 将 Obsidian 收藏夹同步到 about 项目（Next.js 博客）。扫描 Obsidian 的 Resources/收藏夹 目录，将新内容转换为 about 项目的 content/bookmarks 格式。
---

# Obsidian 到 About 同步技能

定时将 Obsidian 中的收藏夹同步到 about 项目，用于构建个人网站。

## 源目录

- **收藏夹**: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Resources/收藏夹/`

## 目标目录

- **收藏夹**: `/Users/xuandao/.openclaw/workspace/git/about/content/bookmarks/`

## 同步逻辑

### 收藏夹同步

1. 扫描 Obsidian 收藏夹目录中的所有 `.md` 文件
2. 提取文件名中的日期（格式：`YYYY-MM-DD-slug.md`）
3. 检查目标目录是否已存在同名文件
4. 如果不存在，转换格式并复制到 about 项目

**格式转换**:

Obsidian 格式:
```markdown
---
title: "文章标题"
date: 2026-03-05
tags: [AI, 认知科学]
source: Harvard Business Review
url: https://hbr.org/...
authors: [作者名]
---

# 文章标题

> 原文 | 来源 | 日期
> 作者: xxx

正文内容...
```

About 项目格式:
```markdown
---
标题: 文章标题
作者: 作者名
来源: https://hbr.org/...
日期: 2026-03-05
标签: #AI #认知科学
---

# 文章标题

正文内容...
```

### 文件名规则

- 格式: `YYYY-MM-DD-slug.md`
- slug: 小写字母、数字、连字符
- 示例: `2026-03-06-para-method.md`

## 触发方式

- Cron 定时任务调用（默认每天凌晨 2 点）
- 手动执行：说"同步 Obsidian 到 about"

## 实现步骤

1. 读取 Obsidian 源目录文件列表
2. 读取 about 目标目录文件列表
3. 对比找出新增文件
4. 转换格式（提取 frontmatter 元数据，转换为 about 格式）
5. 写入目标目录
6. 执行 git add、commit、push

## Git 提交

- 提交信息: `sync(obsidian): 同步收藏夹 - YYYY-MM-DD HH:mm`
- 自动推送到远程仓库
