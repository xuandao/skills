---
name: daily-summary
description: 每日深度总结与行动指南。自动执行 Daily 维护，并由 Agent 自主分析知识库动态，生成智能建议。
---

# 每日深度总结技能 (Daily Summary Agentic Workflow)

该技能采用 **Agentic Workflow** 模式。脚本仅负责最基础的文件维护，所有的分析、总结、日程安排及研究建议均由 Agent 直接读取知识库内容后自主生成。

## 运行方式

通过 openClaw 的 Cron 插件定时触发，或直接对 Agent 下令。

### 触发指令
- "执行每日深度总结任务"

## Agent 执行指南 (指令规则)

当收到执行指令时，Agent **必须** 严格按照以下步骤自主完成任务：

### 1. 基础维护 (基础动作)
- 运行 `scripts/daily_manager.py`。
- 获取输出中的 `today_note_path` (今日笔记路径)、`obsidian_root` (库根目录)、`date` (今日日期与星期) 以及 `weather` (今日天气)。

### 2. 知识获取 (自主阅读)
- **获取动态**: 使用 `run_shell_command` 在 `obsidian_root` 中运行 `find . -name "*.md" -mtime -3`，找出近 3 天修改的文件。
- **获取运动数据**: 使用 `run_shell_command` 在 `obsidian_root` 中运行 `find Areas/Running -name "*.md" -mtime -7`，找出近 7 天的运动笔记并阅读。
- **深度阅读**: 使用 `read_file` 阅读上述文件的内容（优先阅读最近修改的 5-10 篇）。
- **获取收藏**: 阅读 `Resources/收藏夹` 目录下最新的 1-2 篇笔记。
- **系统状态**: 运行 `openclaw sessions --all-agents --active 1440 --json` 获取过去 24 小时的 Token 消耗。

### 3. 智能分析与生成 (逻辑核心)
Agent 需根据读到的内容，自主生成以下两个部分：

#### [部分 A：微信极简简报]
- **要求**: 极其简洁，总长度 < 200 字。
- **包含**:
    - 📅 **日期**: 使用输出中的 `date`。
    - ⛅️ **天气**: 使用输出中的 `weather`。
    - 🌟 **晨间灵感**: 一句诗或格言。
    - 📅 **核心日程**: 以列表形式展示 **3 条**今日关键事项（每条 5-10 字）。
    - 🤖 **系统消耗**: 过去 24h Token 消耗。
    - 📚 **核心收藏**: 整理1篇收藏的核心要点，并给出 **1-3 点**行动建议。
- **结尾**: 提示"详细深度洞察已同步至 Daily 笔记"。

#### [部分 A-验证：简报格式校验]
生成简报后，**必须**进行以下验证：
- **字数检查**: 总长度必须 < 200 字（含标点符号）。
- **元素完整性**: 确认包含所有 6 个必需元素（📅日期、⛅️天气、🌟晨间灵感、📅核心日程、🤖系统消耗、📚1条核心收藏）。
- **结尾检查**: 确认包含"详细深度洞察已同步至 Daily 笔记"提示。
- **格式检查**: 使用 emoji 作为各段落的视觉分隔符。
- **处理逻辑**:
  - 若字数超标：压缩日程描述，精简收藏推荐，保留核心信息。
  - 若缺少元素：补充缺失内容。
  - 验证通过后，进入发送环节。

- **发送**: 验证通过后，使用 `message` 工具发送简报。
  - **channel**: `openclaw-weixin`
  - **target**: 默认用户（`default`），即 `~/.openclaw/openclaw-weixin/config.json` 中配置的默认接收用户
  - **如需指定其他用户**: 使用微信用户 ID（格式如 `o9cq80yucIURnSweSPPPtbeGBMUE@im.wechat`）
  - **获取方式**: 查看 `~/.openclaw/openclaw-weixin/accounts/{account-id}.context-tokens.json` 文件的 key

#### [部分 B：Daily 深度洞察]
- **要求**: 专业、简练，避免冗长论述，每点 2-3 句话即可。
- **前置步骤：获取前3日 Daily 文档**
  - 使用 `run_shell_command` 在 `DAILY_FOLDER` 中运行 `find . -name "*.md" -mtime -4`，找出前3天的 Daily 笔记。
  - 使用 `read_file` 阅读这些文件，提取其中的深度洞察内容。
- **内容**:
    - **动态回顾**: 仅提炼近3日的新关注点、关键想法（Focus/Ideas/Insights），**避免重复**已记录的内容。
    - **🏃 运动表现**: 简述近7天运动状态，给出今日/本周运动建议（1-2句话）。
    - **任务重点**: 指出今日最优先推进的1-2个事项及原因。
    - **调研建议**: 1-2条开放性思维建议或前瞻调研方向。

#### [部分 B-验证：内容去重检查]
生成洞察内容后，**必须**进行以下验证：
- **重复检查**: 将生成的内容与**前3日 Daily 笔记**中的洞察内容进行比对。
- **去重规则**:
  - 若发现相同或高度相似的观点：删除或改写，确保今日内容有**新增价值**。
  - 若运动建议与前日重复：根据最新身体状态调整建议。
  - 若任务重点已连续多日出现：标记为"持续推进"，简要说明当前进展即可。
- **简洁检查**: 确认每部分内容不超过 3 句话，总字数控制在 300 字以内。
- **处理逻辑**:
  - 验证未通过：返回重写，删除重复/冗余内容。
  - 验证通过：进入写入环节。

- **写入**: 验证通过后，将此部分内容以 `## 🧠 AI 深度洞察与调研建议` 为标题，**追加 (Append)** 到 `today_note_path` 文件的末尾。

## 配置说明

### Obsidian 配置 (config.json)

- **OBSIDIAN_ROOT**: Obsidian 库的绝对路径。
- **DAILY_FOLDER**: 每日笔记相对路径。
- **ARCHIVE_FOLDER**: 归档相对路径。
- **TEMPLATE_PATH**: 每日笔记模板路径。

### 微信发送配置

微信简报发送需要配置目标用户 ID：

1. **查找用户 ID**：
   ```bash
   cat ~/.openclaw/openclaw-weixin/accounts/{account-id}.context-tokens.json
   ```
   文件的 key 即为微信用户 ID，格式如：`o9cq80yucIURnSweSPPPtbeGBMUE@im.wechat`

2. **发送参数**：
   - `channel`: `openclaw-weixin`
   - `target`: 上述用户 ID
   - `message`: 简报内容

## 脚本说明

### daily_manager.py
- 归档 7 天前的笔记
- 提取未完成任务
- 创建/更新今日笔记
- 获取天气和日历事件

## 注意事项
- Agent 必须保持专业、前瞻性的口吻。
- 简报内容需简洁，避免发送长篇大论。
- 所有的"研讨性、分析性"内容必须留在 Daily 笔记中，保持手机端的清爽。

