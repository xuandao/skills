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
    """Determine training type from user input or activity name

    支持多种自然语言输入方式，包括口语化表达和英文关键词。
    用户输入优先级高于活动名称。
    """
    # 扩展关键词映射（支持部分匹配和同义词）
    keywords = {
        '间歇跑': [
            '间歇', 'interval', 'hiit', '高强度',
            '间歇训练', '跑间歇', '跑了个间歇',
            '法特莱克', 'fartlek', '变速跑'
        ],
        '节奏跑': [
            '节奏', 'tempo', '乳酸阈值', 'threshold',
            '节奏训练', '跑节奏', 'tempo run',
            '巡航间歇'
        ],
        'LSD': [
            'lsd', '长距离', 'long run', 'lsd跑',
            '长距离慢跑', 'lsd训练', '周末长距离',
            'lsd长距离', '慢跑长距离'
        ],
        '轻松跑': [
            '轻松跑', 'easy run', '有氧跑', '轻松慢跑',
            '轻松训练', '有氧慢跑', 'easy jog',
            '恢复性慢跑', '有氧基础'
        ],
        '恢复跑': [
            '恢复', '放松', 'recovery', '休息跑', '放松跑',
            '恢复训练', '恢复慢跑', 'recovery run',
            '排酸跑', '放松慢跑', '休息恢复'
        ],
        '跑步机': [
            '跑步机', 'treadmill', '室内跑', '室内训练',
            '跑步机训练', '跑跑步机', 'treadmill run',
            'gym跑', '健身房跑步'
        ],
        '马拉松配速跑': [
            '马拉松', 'marathon pace', '马配', 'mp',
            '马拉松配速', '比赛配速', 'race pace',
            'marathon', '目标配速', 'goal pace'
        ]
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


def analyze_activity_name(activity_name, distance_km=None, duration_min=None):
    """智能分析活动名称推断训练类型

    除了关键词匹配外，还结合距离和时间特征进行推断。

    Args:
        activity_name: Strava 活动名称
        distance_km: 距离(公里)
        duration_min: 时长(分钟)

    Returns:
        dict: {
            'training_type': 训练类型,
            'confidence': 置信度 ('high', 'medium', 'low'),
            'reason': 推断原因
        }
    """
    name_lower = activity_name.lower()

    # 首先使用关键词匹配
    keywords = {
        '间歇跑': ['interval', 'hiit', 'fartlek', '间歇', '变速'],
        '节奏跑': ['tempo', 'threshold', '乳酸阈值', '节奏'],
        'LSD': ['lsd', 'long run', '长距离'],
        '轻松跑': ['easy', '轻松', 'jog'],
        '恢复跑': ['recovery', '恢复', '放松'],
        '跑步机': ['treadmill', '跑步机', 'indoor', '室内'],
        '马拉松配速跑': ['marathon', '马拉松', 'race pace']
    }

    # 关键词匹配
    for type_name, words in keywords.items():
        if any(word in name_lower for word in words):
            return {
                'training_type': type_name,
                'confidence': 'high',
                'reason': f'活动名称包含关键词'
            }

    # 基于距离和时间的启发式推断
    if distance_km and duration_min:
        pace_min_per_km = duration_min / distance_km

        # 长距离慢跑 (LSD): 距离 > 15km 或 时间 > 90分钟
        if distance_km >= 15 or duration_min >= 90:
            return {
                'training_type': 'LSD',
                'confidence': 'medium',
                'reason': f'距离{distance_km}km/时长{duration_min}分钟符合LSD特征'
            }

        # 轻松跑: 配速较慢 (> 6:00/km) 或距离短 (< 5km)
        if pace_min_per_km >= 6.0 or distance_km < 5:
            return {
                'training_type': '轻松跑',
                'confidence': 'low',
                'reason': f'配速{pace_min_per_km:.1f}min/km或距离较短'
            }

    # 默认
    return {
        'training_type': '轻松跑',
        'confidence': 'low',
        'reason': '无明确特征，默认轻松跑'
    }


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
    """Analyze heart rate zones and infer training intensity

    Returns zone information and training intensity inference.
    """
    try:
        max_hr = int(max_hr_activity) if max_hr_activity and max_hr_activity != 'N/A' else 190
        avg_hr_int = int(avg_hr) if avg_hr and avg_hr != 'N/A' else None

        if not avg_hr_int:
            return None

        # 计算心率区间边界
        z1 = max_hr * 0.5
        z2 = max_hr * 0.6
        z3 = max_hr * 0.7
        z4 = max_hr * 0.8
        z5 = max_hr * 0.9

        # 确定平均心率所在区间
        if avg_hr_int < z2:
            zone = "Zone 1 (恢复/热身 - <60%)"
            zone_num = 1
            intensity = "低"
            suggested_type = "恢复跑"
        elif avg_hr_int < z3:
            zone = "Zone 2 (轻松/有氧基础 - 60-70%)"
            zone_num = 2
            intensity = "低-中"
            suggested_type = "轻松跑"
        elif avg_hr_int < z4:
            zone = "Zone 3 (马拉松配速/有氧进阶 - 70-80%)"
            zone_num = 3
            intensity = "中"
            suggested_type = "马拉松配速跑"
        elif avg_hr_int < z5:
            zone = "Zone 4 (乳酸阈值/无氧 - 80-90%)"
            zone_num = 4
            intensity = "高"
            suggested_type = "节奏跑"
        else:
            zone = "Zone 5 (极限/冲刺 - >90%)"
            zone_num = 5
            intensity = "极高"
            suggested_type = "间歇跑"

        return {
            "estimated_max_hr": max_hr,
            "avg_zone": zone,
            "zone_num": zone_num,
            "intensity": intensity,
            "suggested_type": suggested_type,
            "zones_breakdown": f"Z1(>{int(z1)}), Z2(>{int(z2)}), Z3(>{int(z3)}), Z4(>{int(z4)}), Z5(>{int(z5)})"
        }
    except:
        return None


def infer_training_type_from_hr(avg_hr, max_hr_activity, duration_min=None):
    """基于心率数据推断训练类型

    Args:
        avg_hr: 平均心率
        max_hr_activity: 活动最大心率（用于估算最大心率）
        duration_min: 活动时长（分钟），可选

    Returns:
        dict: {
            'training_type': 推断的训练类型,
            'confidence': 置信度 ('high', 'medium', 'low'),
            'reason': 推断原因,
            'zone_info': 心率区间信息
        }
    """
    zone_info = analyze_hr_zones(avg_hr, max_hr_activity)

    if not zone_info:
        return {
            'training_type': '轻松跑',
            'confidence': 'low',
            'reason': '无心率数据，默认轻松跑',
            'zone_info': None
        }

    zone_num = zone_info['zone_num']
    suggested_type = zone_info['suggested_type']
    intensity = zone_info['intensity']

    # 结合时长进行更精确的判断
    if duration_min:
        if zone_num >= 4 and duration_min < 30:
            # 高心率但短时长 - 可能是间歇跑
            confidence = 'high'
            reason = f"心率区间Z{zone_num}({intensity})且时长{duration_min}分钟，符合间歇跑特征"
        elif zone_num == 3 and duration_min >= 60:
            # 中等心率且长时长 - 可能是马拉松配速跑或LSD
            if duration_min >= 90:
                confidence = 'medium'
                suggested_type = 'LSD'
                reason = f"心率区间Z{zone_num}且时长{duration_min}分钟，可能是LSD"
            else:
                confidence = 'medium'
                reason = f"心率区间Z{zone_num}({intensity})且时长{duration_min}分钟，可能是马拉松配速跑"
        elif zone_num <= 2 and duration_min >= 60:
            # 低心率且长时长 - 恢复跑或轻松跑
            confidence = 'medium'
            reason = f"心率区间Z{zone_num}({intensity})且时长较长，适合恢复"
        else:
            confidence = 'medium'
            reason = f"心率区间Z{zone_num}({intensity})，建议{suggested_type}"
    else:
        confidence = 'medium'
        reason = f"心率区间Z{zone_num}({intensity})，建议{suggested_type}"

    return {
        'training_type': suggested_type,
        'confidence': confidence,
        'reason': reason,
        'zone_info': zone_info
    }


def analyze_pace_variation(splits):
    """分析配速变化特征

    Args:
        splits: 分段数据列表，每项包含 'pace' 字段 (格式: "M:SS")

    Returns:
        dict: {
            'avg_pace_sec': 平均配速(秒),
            'pace_variance': 配速方差,
            'pace_range': 配速范围(秒),
            'is_consistent': 是否稳定,
            'has_surges': 是否有加速,
            'has_recoveries': 是否有恢复,
            'pattern': 配速模式 ('steady', 'interval', 'progression', 'variable'),
            'suggested_type': 建议训练类型
        }
    """
    if not splits or len(splits) < 2:
        return None

    # 解析配速
    pace_seconds = []
    for split in splits:
        pace_str = split.get('pace', 'N/A')
        if pace_str != 'N/A':
            try:
                parts = pace_str.split(':')
                if len(parts) == 2:
                    seconds = int(parts[0]) * 60 + int(parts[1])
                    pace_seconds.append(seconds)
            except:
                continue

    if len(pace_seconds) < 2:
        return None

    # 计算统计量
    import statistics
    avg_pace = statistics.mean(pace_seconds)
    min_pace = min(pace_seconds)
    max_pace = max(pace_seconds)
    pace_range = max_pace - min_pace

    try:
        pace_variance = statistics.stdev(pace_seconds)
    except:
        pace_variance = 0

    # 分析配速模式
    # 判断是否稳定 (方差 < 10秒)
    is_consistent = pace_variance < 10

    # 判断是否有间歇特征（有大起伏）
    has_surges = pace_range > 30  # 配速差 > 30秒

    # 判断是否有恢复段（配速较慢的段落）
    slow_threshold = avg_pace + 15
    has_recoveries = any(p > slow_threshold for p in pace_seconds)

    # 判断是否有渐加速特征（每段越来越快）
    progression_count = 0
    for i in range(1, len(pace_seconds)):
        if pace_seconds[i] < pace_seconds[i-1] - 5:  # 快5秒以上
            progression_count += 1
    is_progression = progression_count >= len(pace_seconds) // 2

    # 确定配速模式
    if is_consistent:
        pattern = 'steady'
        suggested_type = '节奏跑'
        reason = '配速稳定，可能是节奏跑或马拉松配速跑'
    elif has_surges and has_recoveries:
        pattern = 'interval'
        suggested_type = '间歇跑'
        reason = f'配速变化大(范围{pace_range}秒)，有快有慢，符合间歇跑特征'
    elif is_progression:
        pattern = 'progression'
        suggested_type = '节奏跑'
        reason = '配速逐渐加快，可能是渐加速跑'
    else:
        pattern = 'variable'
        suggested_type = '轻松跑'
        reason = f'配速变化不规律(方差{pace_variance:.1f}秒)，可能是轻松跑'

    return {
        'avg_pace_sec': avg_pace,
        'pace_variance': pace_variance,
        'pace_range': pace_range,
        'is_consistent': is_consistent,
        'has_surges': has_surges,
        'has_recoveries': has_recoveries,
        'is_progression': is_progression,
        'pattern': pattern,
        'suggested_type': suggested_type,
        'reason': reason,
        'pace_data': pace_seconds
    }


def infer_training_type_from_pace(splits, avg_pace_str=None):
    """基于配速数据推断训练类型

    Args:
        splits: 分段数据列表
        avg_pace_str: 平均配速字符串 (可选)

    Returns:
        dict: {
            'training_type': 推断的训练类型,
            'confidence': 置信度,
            'reason': 推断原因,
            'pace_analysis': 配速分析详情
        }
    """
    pace_analysis = analyze_pace_variation(splits)

    if not pace_analysis:
        # 没有分段数据，尝试从平均配速推断
        if avg_pace_str and avg_pace_str != 'N/A':
            try:
                parts = avg_pace_str.split(':')
                avg_pace_sec = int(parts[0]) * 60 + int(parts[1])

                # 简单推断：快配速可能是间歇或节奏，慢配速可能是恢复
                if avg_pace_sec < 300:  # < 5:00/km
                    return {
                        'training_type': '节奏跑',
                        'confidence': 'low',
                        'reason': f'平均配速较快({avg_pace_str})，可能是节奏跑或间歇跑',
                        'pace_analysis': None
                    }
                elif avg_pace_sec > 400:  # > 6:40/km
                    return {
                        'training_type': '恢复跑',
                        'confidence': 'low',
                        'reason': f'平均配速较慢({avg_pace_str})，可能是恢复跑',
                        'pace_analysis': None
                    }
            except:
                pass

        return {
            'training_type': '轻松跑',
            'confidence': 'low',
            'reason': '无配速分段数据，默认轻松跑',
            'pace_analysis': None
        }

    # 有配速分析结果
    pattern = pace_analysis['pattern']
    suggested_type = pace_analysis['suggested_type']

    # 根据模式确定置信度
    if pattern == 'interval':
        confidence = 'high'
    elif pattern == 'steady':
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'training_type': suggested_type,
        'confidence': confidence,
        'reason': pace_analysis['reason'],
        'pace_analysis': pace_analysis
    }


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
