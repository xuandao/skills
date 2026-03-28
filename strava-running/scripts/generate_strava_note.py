#!/usr/bin/env python3
"""
Generate Obsidian note from Strava running data with training type classification.
"""

import os
import sys
import json
from datetime import datetime

# Training type mapping
TRAINING_TYPES = {
    '间歇跑': {
        'emoji': '⚡',
        'folder': '间歇跑',
        'description': '高强度间歇训练',
        'key_metrics': ['avg_pace', 'max_hr', 'avg_cadence']
    },
    '节奏跑': {
        'emoji': '🎯',
        'folder': '节奏跑',
        'description': '乳酸阈值训练',
        'key_metrics': ['avg_pace', 'avg_hr', 'duration']
    },
    '轻松跑': {
        'emoji': '🌤️',
        'folder': '轻松跑',
        'description': '恢复性慢跑',
        'key_metrics': ['distance_km', 'avg_hr', 'duration']
    },
    'LSD': {
        'emoji': '🏃',
        'folder': 'LSD',
        'description': '长距离慢跑',
        'key_metrics': ['distance_km', 'duration', 'avg_pace']
    },
    '马拉松配速跑': {
        'emoji': '🎽',
        'folder': '马拉松配速跑',
        'description': '目标配速训练',
        'key_metrics': ['avg_pace', 'distance_km', 'avg_hr']
    },
    '恢复跑': {
        'emoji': '💆',
        'folder': '恢复跑',
        'description': '低强度恢复',
        'key_metrics': ['avg_hr', 'duration']
    },
    '跑步机': {
        'emoji': '🏋️',
        'folder': '跑步机',
        'description': '室内跑步机训练',
        'key_metrics': ['distance_km', 'avg_pace', 'calories']
    }
}


def get_training_type(activity_name, user_input=None):
    """Determine training type from user input or activity name"""
    # 关键词映射（支持部分匹配）
    keywords = {
        '间歇跑': ['间歇', 'interval'],
        '节奏跑': ['节奏', 'tempo'],
        'LSD': ['lsd', '长距离'],
        '轻松跑': ['轻松', 'easy'],
        '恢复跑': ['恢复', 'recovery'],
        '跑步机': ['跑步机', 'treadmill'],
        '马拉松配速跑': ['马拉松', 'marathon pace'],
    }

    # 优先从用户输入检测
    if user_input:
        user_lower = user_input.lower()
        for type_name, words in keywords.items():
            if any(word in user_lower for word in words):
                return type_name

    # 从活动名称检测
    activity_lower = activity_name.lower()
    for type_name, words in keywords.items():
        if any(word in activity_lower for word in words):
            return type_name

    return '轻松跑'  # Default


def parse_pace(pace_str):
    """Parse pace string to seconds"""
    if pace_str == 'N/A' or not pace_str:
        return None
    try:
        parts = pace_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except:
        pass
    return None


def format_pace_from_seconds(seconds):
    """Format seconds to pace string"""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def format_pace_diff(current, previous):
    """Format pace difference"""
    if not current or not previous:
        return None
    diff = current - previous
    if diff == 0:
        return "持平"
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff}秒/km"


def analyze_hr_zones(avg_hr, max_hr_activity):
    """Analyze heart rate zones"""
    try:
        max_hr = int(max_hr_activity) if max_hr_activity and max_hr_activity != 'N/A' else 190
        avg_hr_int = int(avg_hr) if avg_hr and avg_hr != 'N/A' else None

        if not avg_hr_int:
            return None

        z1 = max_hr * 0.5
        z2 = max_hr * 0.6
        z3 = max_hr * 0.7
        z4 = max_hr * 0.8
        z5 = max_hr * 0.9

        if avg_hr_int < z2:
            zone = "Zone 1 (恢复/热身 - <60%)"
        elif avg_hr_int < z3:
            zone = "Zone 2 (轻松/有氧基础 - 60-70%)"
        elif avg_hr_int < z4:
            zone = "Zone 3 (马拉松配速/有氧进阶 - 70-80%)"
        elif avg_hr_int < z5:
            zone = "Zone 4 (乳酸阈值/无氧 - 80-90%)"
        else:
            zone = "Zone 5 (极限/冲刺 - >90%)"

        return {
            "estimated_max_hr": max_hr,
            "avg_zone": zone,
            "zones_breakdown": f"Z1(>{int(z1)}), Z2(>{int(z2)}), Z3(>{int(z3)}), Z4(>{int(z4)}), Z5(>{int(z5)})"
        }
    except:
        return None


def analyze_progress(data, training_type, obsidian_path):
    """Analyze training progress"""
    type_folder = os.path.join(obsidian_path, TRAINING_TYPES[training_type]['folder'])

    if not os.path.exists(type_folder):
        return None

    # Read history
    history = []
    for filename in os.listdir(type_folder):
        if filename.endswith('.md') and filename.startswith('20'):
            filepath = os.path.join(type_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            frontmatter = parts[1]
                            record = {}
                            for line in frontmatter.strip().split('\n'):
                                if ':' in line:
                                    key, value = line.split(':', 1)
                                    record[key.strip()] = value.strip()
                            history.append(record)
            except:
                continue

    if len(history) < 1:
        return None

    # Analyze
    analysis = {
        'total_runs': len(history) + 1,
        'comparisons': []
    }

    if history:
        last_run = history[-1]
        current_pace = parse_pace(data['avg_pace'])
        last_pace = parse_pace(last_run.get('pace', 'N/A'))

        if current_pace and last_pace:
            pace_diff = format_pace_diff(current_pace, last_pace)
            if pace_diff:
                analysis['comparisons'].append(f"配速: {pace_diff}")

        try:
            current_dist = float(data['distance_km'])
            last_dist = float(last_run.get('distance', 0))
            if last_dist > 0:
                dist_diff = current_dist - last_dist
                analysis['comparisons'].append(f"距离: {dist_diff:+.2f}km")
        except:
            pass

    return analysis


def generate_note(data, obsidian_path, training_type=None, user_input=None):
    """Generate Obsidian markdown note from running data"""

    if not training_type:
        training_type = get_training_type(data['activity_name'], user_input)

    type_info = TRAINING_TYPES[training_type]

    date = data['date']
    activity_name = data['activity_name']
    distance = data['distance_km']
    duration = data['duration']
    avg_pace = data['avg_pace']
    avg_hr = data.get('avg_hr', 'N/A')
    max_hr = data.get('max_hr', 'N/A')
    calories = data.get('calories', 'N/A')
    elevation = data.get('elevation_gain', 'N/A')
    cadence = data.get('avg_cadence', 'N/A')
    gpx_path = data.get('gpx_path')
    splits = data.get('splits', [])

    # Get Strava-specific data
    strava_data = data.get('strava_data', {})

    # Create training type folder
    type_folder = os.path.join(obsidian_path, type_info['folder'])
    os.makedirs(type_folder, exist_ok=True)

    # Generate filename
    filename = f"{date}-{activity_name.replace(' ', '-')}.md"
    filepath = os.path.join(type_folder, filename)

    # Analyze progress
    progress = analyze_progress(data, training_type, obsidian_path)

    # Analyze HR zones
    hr_zones = analyze_hr_zones(avg_hr, max_hr)

    # Generate markdown content
    content = f"""---
date: {date}
type: running
training_type: {training_type}
distance: {distance}
pace: {avg_pace}
avg_hr: {avg_hr}
---

# {type_info['emoji']} {activity_name}

> **训练类型**: {training_type} - {type_info['description']}

## 📊 基本数据

- **日期**: {date} {data['time']}
- **距离**: {distance} km
- **用时**: {duration}
- **配速**: {avg_pace} /km
- **消耗**: {calories} 卡路里

## 💓 心率数据

- **平均心率**: {avg_hr} bpm
- **最大心率**: {max_hr} bpm
"""

    if hr_zones:
        content += f"""
### 心率区间分析

- **估算最大心率**: {hr_zones['estimated_max_hr']} bpm
- **平均心率区间**: {hr_zones['avg_zone']}

**区间划分**: {hr_zones['zones_breakdown']}
"""

    content += f"""
## 🏃 跑步数据

- **平均步频**: {cadence} spm
- **累计爬升**: {elevation} m
"""

    # Add Strava-specific metrics
    if strava_data.get('max_speed'):
        max_pace = format_pace_from_seconds(int(1000 / strava_data['max_speed'])) if strava_data['max_speed'] > 0 else "N/A"
        content += f"- **最高配速**: {max_pace} /km\n"

    if strava_data.get('average_watts'):
        content += f"- **平均功率**: {strava_data['average_watts']} W\n"

    if strava_data.get('suffer_score'):
        content += f"- **痛苦指数**: {strava_data['suffer_score']}\n"

    content += f"""
## 📈 训练分析

- **{training_type}总次数**: {progress['total_runs'] if progress else 1} 次
"""

    if progress and progress['comparisons']:
        content += """
**与上次对比**:
"""
        for comp in progress['comparisons']:
            content += f"- {comp}\n"

    if splits:
        content += """
## 🔄 分段数据

| 圈数 | 距离 | 用时 | 配速 | 平均心率 | 最大心率 |
|------|------|------|------|----------|----------|
"""
        for split in splits:
            hr_avg = split.get('avg_hr', '-')
            hr_max = split.get('max_hr', '-')
            content += f"| {split['lap_number']} | {split['distance_km']}km | {split['duration']} | {split['pace']}/km | {hr_avg} | {hr_max} |\n"

    if gpx_path:
        content += f"""
## 📍 GPX 文件

- **文件路径**: `{gpx_path}`
"""

    content += """
---

## 📝 训练感受

- [ ] 状态很好，轻松完成
- [ ] 状态一般，按计划完成
- [ ] 状态较差，勉强完成
- [ ] 未完成/中断

### 身体感受

<!-- 记录跑步过程中的身体感受 -->

### 改进点

<!-- 记录需要改进的地方 -->
"""

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_strava_note.py <json_file> <obsidian_path> [training_type] [user_input]", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]
    obsidian_path = sys.argv[2]
    training_type = sys.argv[3] if len(sys.argv) > 3 else None
    user_input = sys.argv[4] if len(sys.argv) > 4 else None

    # Load data
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Generate note
    filepath = generate_note(data, obsidian_path, training_type, user_input)

    print(f"✅ Note created: {filepath}")


if __name__ == '__main__':
    main()
