---
name: strava-running
description: 从 Strava 获取跑步数据并进行训练类型分类（间歇跑、节奏跑、轻松跑、LSD、马拉松配速跑、恢复跑、跑步机）。支持从 streams 数据生成 GPX 文件，追踪训练进度，并在 Obsidian 中生成分类笔记。当用户完成跑步并提到训练类型（如 "节奏跑完了"、"间歇跑完了"）或要求记录/分析最新的 Strava 跑步活动时使用。
---

# Strava Running

自动从 Strava 获取最新的跑步活动，按训练类型分类，分析训练进度，并在 Obsidian 中创建结构化笔记。

## 训练类型

支持 7 种训练类型的自动分类：

- **⚡ 间歇跑** (Interval) - 高强度间歇训练
- **🎯 节奏跑** (Tempo) - 乳酸阈值训练
- **🌤️ 轻松跑** (Easy) - 恢复性慢跑
- **🏃 LSD** - 长距离慢跑
- **🎽 马拉松配速跑** (Marathon Pace) - 目标配速训练
- **💆 恢复跑** (Recovery) - 低强度恢复
- **🏋️ 跑步机** (Treadmill) - 室内跑步机训练

## 工作流程

当用户说完成了一次跑步（如 "节奏跑完了"、"间歇跑完了"）：

1. **从用户输入中提取训练类型**
2. **使用 `scripts/fetch_strava_run.py` 获取最新跑步活动**
3. **使用 `scripts/generate_strava_note.py` 在 Obsidian 笔记库中生成分类笔记**
4. **通过与历史同类型训练对比分析进度**
5. **显示摘要和进度洞察，确认完成**

## 步骤 1: 获取跑步数据

运行数据获取脚本以获取最新的跑步活动：

```bash
python3 scripts/fetch_strava_run.py <gpx_output_dir>
```

脚本将执行以下操作：
- 从 `references/strava_config.json` 读取凭证
- 使用 OAuth2 (refresh_token) 认证 Strava API
- 获取最新的跑步活动
- 从 streams 数据生成 GPX 文件
- 将包含活动数据的 JSON 输出到 stdout

## 步骤 2: 生成分类笔记

将 JSON 输出保存到临时文件，然后运行：

```bash
python3 scripts/generate_strava_note.py <json_file> "/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/Running" "" "<user_input>"
```

参数说明：
- `json_file`: 步骤 1 生成的 JSON 数据文件路径
- `obsidian_running_path`: 跑步笔记的基础路径
- 第三个参数：留空（预留给显式训练类型）
- `user_input`: 用户的原始消息（如 "节奏跑完了"），用于类型检测

## 进度追踪

脚本会自动：
- 统计每种训练类型的总次数
- 与上次同类型训练对比
- 显示配速提升/下降
- 显示距离变化

## 配置

创建 `references/strava_config.json`，内容如下：
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "refresh_token": "your_refresh_token"
}
```

## 依赖

需要安装 `stravalib` 和 `gpxpy`：
```bash
pip3 install stravalib gpxpy
```

## 注意事项

- 训练类型从用户输入中检测（如 "节奏跑完了" → 节奏跑）
- 如果用户输入中无类型信息，则回退到从活动名称判断
- GPX 文件从 Strava streams 数据生成（latlng + altitude + time）
- 跑步机活动没有 GPS 数据，因此不生成 GPX 文件
- 进度分析需要至少 2 次同类型训练记录
