---
name: todo-reminder
description: 当用户说"提醒我xxx"时，自动在 Obsidian 的每日笔记中添加待办事项。不创建 cron 定时提醒（除非用户明确要求）。
---

# Todo Reminder

当用户说"提醒我xxx"、"todo xxx"、"帮我记一下xxx"时，在 Obsidian 每日笔记中添加待办。

## Obsidian 路径

- 每日笔记目录: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Projects/Daily/`
- 模板文件: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Resources/Templates/daily-template.md`
- 文件名格式: `YYYY-MM-DD.md`

## 操作步骤

1. 确定今天的日期 (2026-03-15)，格式化为:
   - `YYYY-MM-DD`: 2026-03-15
   - `dddd`: 星期几（如"星期日"）
2. 打开模板文件 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Resources/Templates/daily-template.md`
3. 读取模板内容，替换其中的动态变量:
   - `{{date:YYYY-MM-DD}}` → 2026-03-15
   - `{{date:dddd}}` → 星期日
4. 打开或创建每日笔记 `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Projects/Daily/2026-03-15.md`
5. 如果是新文件，写入替换后的模板内容
6. 在 `## 📋 今日待办` 或 `## 今日待办` 标题下添加待办事项:
   - 事项前加 `- [ ] ` 表示未完成
7. 保存文件
