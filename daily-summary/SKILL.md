---
name: daily-summary
description: 每日总结助手。自动归档旧笔记、创建今日 Daily Note、继承未完成待办，并汇总 openClaw 状态与最近收藏，通过 Telegram 推送每日简报。
---

# 每日总结技能 (Daily Summary)

该技能旨在自动化每日的 Obsidian 笔记维护及信息同步流程。

## 核心功能

1.  **Obsidian 笔记管理**:
    *   **归档**: 自动将 `Projects/Daily` 目录中早于 7 天前的笔记移动至 `Archive/Daily`。
    *   **建档**: 使用 `Resources/Templates/daily-template.md` 创建今日笔记（如果尚未创建）。
    *   **迁移**: 从昨日笔记中提取未完成的待办事项（带有 `- [ ]` 且包含日期标签 `📅` 的行），自动添加到今日笔记中。
2.  **系统与知识汇总**:
    *   **openClaw 状态**: 统计定时任务总数、启用数、错误状态及当前 Token 消耗。
    *   **收藏回顾**: 提取 `Resources/收藏夹` 中最新的 3 篇笔记标题与摘要。
    *   **每日灵感**: 自动生成一句古诗词及 3 条“历史上的今天”。
3.  **Telegram 推送**:
    *   汇总上述所有信息，通过 Telegram 发送精美的“每日晨报”。

## 运行方式

该技能通过 openClaw 的 Cron 插件定时触发。

### 触发指令示例
"执行每日总结任务"

### 脚本位置
`/Users/xuandao/.openclaw/workspace/skills/daily-summary/scripts/daily_manager.py`

## 配置说明

- **Obsidian 根目录**: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7`
- **每日笔记目录**: `Projects/Daily`
- **归档目录**: `Archive/Daily`
- **收藏夹目录**: `Resources/收藏夹`
- **模板文件**: `Resources/Templates/daily-template.md`

## 简报模板 (Telegram)

```markdown
# 🌅 每日简报 | {{today}}

## 🌟 晨间灵感
> {{poem}}
> —— {{poem_author}}

### 📜 历史上的今天
- {{history_event_1}}
- {{history_event_2}}
- {{history_event_3}}

## 🤖 系统状态 (openClaw)
- 任务总数: {{oc_total}} (启用: {{oc_enabled}})
- 健康状况: {{oc_health}}
- 资源消耗: {{oc_tokens}}

## 📚 最近收藏
- {{fav_1_title}}: {{fav_1_summary}}
- ...

## 📋 任务概况
- 今日已归档 {{archived_count}} 篇旧笔记。
- 从昨日继承了 {{migrated_count}} 项待办任务。
```
