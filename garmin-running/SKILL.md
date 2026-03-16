---
name: garmin-running
description: Fetch and analyze Garmin Connect running data with training type classification (interval, tempo, easy, LSD, marathon pace, recovery, treadmill). Download GPX files (if available), track progress, and generate categorized Obsidian running notes. Use when the user mentions they finished a run with training type (e.g., "节奏跑完了", "间歇跑完了") or asks to log/analyze their latest Garmin running activity.
---

# Garmin Running

Automatically fetch the latest running activity from Garmin Connect, classify by training type, analyze progress, and create structured notes in Obsidian.

## Training Types

Supports 7 training types with automatic classification:

- **⚡ 间歇跑** (Interval) - 高强度间歇训练
- **🎯 节奏跑** (Tempo) - 乳酸阈值训练
- **🌤️ 轻松跑** (Easy) - 恢复性慢跑
- **🏃 LSD** - 长距离慢跑
- **🎽 马拉松配速跑** (Marathon Pace) - 目标配速训练
- **💆 恢复跑** (Recovery) - 低强度恢复
- **🏋️ 跑步机** (Treadmill) - 室内跑步机训练

## Workflow

When the user says they finished a run (e.g., "节奏跑完了", "间歇跑完了"):

1. **Extract training type** from user input
2. **Fetch latest run** using `scripts/fetch_garmin_run_v3.py`
3. **Generate categorized note** using `scripts/generate_obsidian_note_v2.py` into the Obsidian vault: `/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/Running`
4. **Analyze progress** by comparing with previous runs of the same type
5. **Confirm completion** with summary and progress insights

## Step 1: Fetch Running Data

Run the fetch script to get the latest running activity:

```bash
python3 scripts/fetch_garmin_run_v3.py <gpx_output_dir>
```

The script will:
- Read credentials from `references/garmin_config.json`
- Login to Garmin Connect using `garth` library
- Fetch the latest running activity
- Download the GPX file (if available)
- Output JSON with activity data to stdout

## Step 2: Generate Categorized Note

Save the JSON output to a temporary file, then run:

```bash
python3 scripts/generate_obsidian_note_v2.py <json_file> "/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/Running" "" "<user_input>"
```

Parameters:
- `json_file`: Path to JSON data from step 1
- `obsidian_running_path`: Base path for running notes (configured to your Obsidian vault path)
- Third parameter: Leave empty (reserved for explicit training type)
- `user_input`: User's original message (e.g., "节奏跑完了") for type detection

This creates a markdown note with:
- **Categorized folder structure** (e.g., `.../Areas/Running/节奏跑/`)
- **Training type badge** with emoji and description
- **Basic metrics** (distance, duration, pace, calories)
- **Heart rate data** (average, max)
- **Running metrics** (cadence, elevation)
- **Progress analysis** (total runs of this type, comparison with last run)
- **Structured note sections** (training feeling, completion status, improvements)
- **GPX file reference** (if available)

## Progress Tracking

The script automatically:
- Counts total runs of each training type
- Compares current run with the last run of the same type
- Shows pace improvement/regression (e.g., "-21秒/km" means 21 seconds faster)
- Shows distance change (e.g., "+1.16km")

Example progress output:
```
## 📈 训练分析

- **节奏跑总次数**: 2 次

**与上次对比**:
- 配速: -21秒/km
- 距离: +1.16km
```

## Configuration

Create `references/garmin_config.json` with:
```json
{
  "email": "your@email.com",
  "password": "yourpassword"
}
```

## Dependencies

Requires `garth` Python package:
```bash
pip3 install garth
```

## Notes

- Training type is detected from user input (e.g., "节奏跑完了" → 节奏跑)
- Falls back to activity name if no type in user input
- Treadmill runs don't have GPS data (no GPX files)
- Outdoor runs will have GPX files with full GPS tracks
- Progress analysis requires at least 2 runs of the same type
