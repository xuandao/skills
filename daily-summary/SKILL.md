---
name: daily-summary
description: 每日深度总结与行动指南。自动执行 Daily 维护，并由 Agent 自主分析知识库动态，生成智能建议。
---

# 每日深度总结技能 (Daily Summary Agentic Workflow)

该技能采用 **Agentic Workflow** 模式。脚本仅负责最基础的文件维护，所有的分析、总结、日程安排及研究建议均由 Agent 直接读取知识库内容后自主生成。

## 运行方式

通过 openClaw 的 Cron 插件定时触发，或直接对 Agent 下令。

### 触发指令
"执行每日深度总结任务"

## Agent 执行指南 (指令规则)

当收到执行指令时，Agent **必须** 严格按照以下步骤自主完成任务：

### 1. 基础维护 (基础动作)
- 运行 `scripts/daily_manager.py`。
- 获取输出中的 `today_note_path` (今日笔记路径) 和 `obsidian_root` (库根目录)。

### 2. 知识获取 (自主阅读)
- **获取动态**: 使用 `run_shell_command` 在 `obsidian_root` 中运行 `find . -name "*.md" -mtime -3`，找出近 3 天修改的文件。
- **深度阅读**: 使用 `read_file` 阅读上述文件的内容（优先阅读最近修改的 5-10 篇）。
- **获取收藏**: 阅读 `Resources/收藏夹` 目录下最新的 1-2 篇笔记。
- **系统状态**: 运行 `openclaw sessions --all-agents --active 1440 --json` 获取过去 24 小时的 Token 消耗。

### 3. 智能分析与生成 (逻辑核心)
Agent 需根据读到的内容，自主生成以下两个部分：

#### [部分 A：Telegram 极简简报]
- **要求**: 极其简洁，总长度 < 200 字。
- **包含**: 🌟 晨间灵感（一句诗）、📅 核心日程（1-3点建议）、🤖 系统消耗、📚 1条核心收藏。
- **结尾**: 提示“详细深度洞察已同步至 Daily 笔记”。
- **发送**: 通过 Telegram 推送到目标 ID (5247154884)。

#### [部分 B：Daily 深度洞察]
- **要求**: 专业、深刻。
- **内容**: 
    - **近 3 日动态回顾**: 梳理最近关注的重点 (Focus)、新想法 (Ideas) 和心得 (Insights)。
    - **任务分析**: 结合昨日遗留任务与笔记内容，提供今日重点推进事项的深度分析。
    - **调研建议**: 提供 2-3 条开放性的思维建议或前瞻性方案调研思路。
- **写入**: 将此部分内容以 `## 🧠 AI 深度洞察与调研建议` 为标题，**追加 (Append)** 到 `today_note_path` 文件的末尾。

## 配置说明 (config.json)

- **OBSIDIAN_ROOT**: Obsidian 库的绝对路径。
- **DAILY_FOLDER**: 每日笔记相对路径。
- **ARCHIVE_FOLDER**: 归档相对路径。
- **TEMPLATE_PATH**: 每日笔记模板路径。

## 注意事项
- Agent 必须保持专业、前瞻性的口吻。
- 严禁在 Telegram 发送长篇大论。
- 所有的“研讨性、分析性”内容必须留在 Daily 笔记中，保持手机端的清爽。
