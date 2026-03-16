#!/usr/bin/env python3
"""
Generate Obsidian note from Garmin running data with training type classification.
"""

import os
import sys
import json
from datetime import datetime

# 训练类型映射
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
    """根据活动名称或用户输入判断训练类型"""
    if user_input:
        for type_name in TRAINING_TYPES.keys():
            if type_name in user_input:
                return type_name
    
    # 根据活动名称判断
    activity_lower = activity_name.lower()
    if '间歇' in activity_lower or 'interval' in activity_lower:
        return '间歇跑'
    elif '节奏' in activity_lower or 'tempo' in activity_lower:
        return '节奏跑'
    elif 'lsd' in activity_lower or '长距离' in activity_lower:
        return 'LSD'
    elif '轻松' in activity_lower or 'easy' in activity_lower:
        return '轻松跑'
    elif '恢复' in activity_lower or 'recovery' in activity_lower:
        return '恢复跑'
    elif '跑步机' in activity_lower or 'treadmill' in activity_lower:
        return '跑步机'
    elif '马拉松' in activity_lower or 'marathon' in activity_lower:
        return '马拉松配速跑'
    
    return '轻松跑'  # 默认

def parse_pace(pace_str):
    """解析配速字符串为秒数"""
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
    """从秒数格式化为配速字符串"""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def format_pace_diff(current, previous):
    """格式化配速差异"""
    if not current or not previous:
        return None
    diff = current - previous
    if diff == 0:
        return "持平"
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff}秒/km"

def analyze_hr_zones(avg_hr, max_hr_activity):
    """分析心率区间估算"""
    # 假设用户的最大心率约为 190（如果没有提供），或者用活动最大心率+5
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

def analyze_running_dynamics(data):
    """分析跑步动态数据"""
    dynamics = {}
    splits = data.get('splits', [])
    if not splits:
        return dynamics
        
    strides = [s.get('stride_length') for s in splits if s.get('stride_length') and s.get('stride_length') != '-']
    vert_oscs = [s.get('vertical_oscillation') for s in splits if s.get('vertical_oscillation') and s.get('vertical_oscillation') != '-']
    ground_times = [s.get('ground_contact_time') for s in splits if s.get('ground_contact_time') and s.get('ground_contact_time') != '-']
    
    if strides:
        dynamics['avg_stride'] = round(sum(strides) / len(strides), 2)
    if vert_oscs:
        avg_osc = round(sum(vert_oscs) / len(vert_oscs), 1)
        dynamics['avg_vert_osc'] = avg_osc
        # 评价垂直振幅
        if avg_osc < 6: dynamics['osc_eval'] = "优秀 (极少多余跳跃)"
        elif avg_osc < 8: dynamics['osc_eval'] = "良好"
        elif avg_osc < 10: dynamics['osc_eval'] = "一般"
        else: dynamics['osc_eval'] = "偏高 (浪费能量)"
        
    if ground_times:
        avg_gct = round(sum(ground_times) / len(ground_times), 1)
        dynamics['avg_ground_contact'] = avg_gct
        # 评价触地时间
        if avg_gct < 210: dynamics['gct_eval'] = "精英级 (<210ms)"
        elif avg_gct < 240: dynamics['gct_eval'] = "优秀 (210-240ms)"
        elif avg_gct < 270: dynamics['gct_eval'] = "良好 (240-270ms)"
        else: dynamics['gct_eval'] = "偏长 (>270ms)"
        
    return dynamics

def analyze_progress(data, training_type, obsidian_path):
    """分析训练进步情况"""
    type_folder = os.path.join(obsidian_path, TRAINING_TYPES[training_type]['folder'])
    
    if not os.path.exists(type_folder):
        return None
    
    # 读取同类型的历史记录
    history = []
    for filename in os.listdir(type_folder):
        if filename.endswith('.md') and filename.startswith('20'):
            filepath = os.path.join(type_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 解析 frontmatter
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
    
    # 分析关键指标
    analysis = {
        'total_runs': len(history) + 1,  # 包含当前这次
        'comparisons': []
    }
    
    # 与上一次比较
    if history:
        last_run = history[-1]
        current_pace = parse_pace(data['avg_pace'])
        last_pace = parse_pace(last_run.get('pace', 'N/A'))
        
        if current_pace and last_pace:
            pace_diff = format_pace_diff(current_pace, last_pace)
            if pace_diff:
                analysis['comparisons'].append(f"配速: {pace_diff}")
        
        # 比较距离
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
    
    # 确定训练类型
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
    
    # 创建训练类型子目录
    type_folder = os.path.join(obsidian_path, type_info['folder'])
    os.makedirs(type_folder, exist_ok=True)
    
    # 生成文件名
    filename = f"{date}-{activity_name.replace(' ', '-')}.md"
    filepath = os.path.join(type_folder, filename)
    
    # 分析进步
    progress = analyze_progress(data, training_type, obsidian_path)
    
    # 分析心率区间
    hr_zones = analyze_hr_zones(avg_hr, max_hr)
    
    # 分析跑步动态
    dynamics = analyze_running_dynamics(data)
    
    # 生成 markdown 内容
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
- **卡路里**: {calories} kcal

## ❤️ 心率数据

- **平均心率**: {avg_hr} bpm
- **最大心率**: {max_hr} bpm"""

    if hr_zones:
        content += f"""
- **主要心率区间**: {hr_zones['avg_zone']}
- **区间参考**: {hr_zones['zones_breakdown']}"""

    content += f"""

## 🏃 跑步数据

- **平均步频**: {cadence} spm
- **累计爬升**: {elevation} m"""

    if dynamics:
        if 'avg_stride' in dynamics:
            content += f"\n- **平均步幅**: {dynamics['avg_stride']} m"
        if 'avg_vert_osc' in dynamics:
            content += f"\n- **垂直振幅**: {dynamics['avg_vert_osc']} cm ({dynamics.get('osc_eval', '')})"
        if 'avg_ground_contact' in dynamics:
            content += f"\n- **触地时间**: {dynamics['avg_ground_contact']} ms ({dynamics.get('gct_eval', '')})"

    content += f"""

"""

    # 添加 GPX 引用
    if gpx_path:
        gpx_filename = os.path.basename(gpx_path)
        content += f"""## 📍 GPS 轨迹

GPX 文件: `{gpx_filename}`

"""
    
    # 添加分段数据
    splits = data.get('splits', [])
    if splits:
        # 检查是否有步骤类型信息（CSV 格式）
        has_step_type = any(s.get('step_type') for s in splits)
        
        if has_step_type:
            # 统一使用单表格展示
            content += """## 📊 分段数据

| 组数 | 步骤 | 圈 | 距离 | 配速 | 用时 | 心率 | 步频 | 步幅(m) | 垂直振幅(cm) | 触地(ms) | 功率(W) |
|:---:|:---:|:--:|:----:|:----:|:----:|:----:|:----:|:-------:|:------------:|:--------:|:-------:|
"""
            for split in splits:
                interval = split.get('interval', '')
                step_type = split.get('step_type', '')
                lap = split.get('lap_number', 0)
                km = split['distance_km']
                pace = split['pace']
                duration = split['duration']
                hr = split.get('avg_hr', '-')
                cadence = split.get('avg_cadence', '-')
                stride = split.get('stride_length', '-')
                vert_osc = split.get('vertical_oscillation', '-')
                ground_time = split.get('ground_contact_time', '-')
                power = split.get('avg_power', '-')
                
                # 格式化显示
                km_str = f"{km:.2f}" if km < 1 else f"{int(km)}"
                hr_str = f"{int(hr)}" if hr != '-' else '-'
                cadence_str = f"{cadence:.0f}" if cadence != '-' else '-'
                stride_str = f"{stride:.2f}" if stride != '-' else '-'
                vert_osc_str = f"{vert_osc:.1f}" if vert_osc != '-' else '-'
                ground_time_str = f"{ground_time:.0f}" if ground_time != '-' else '-'
                power_str = f"{int(power)}" if power != '-' else '-'
                
                content += f"| {interval} | {step_type} | {lap} | {km_str} | {pace} | {duration} | {hr_str} | {cadence_str} | {stride_str} | {vert_osc_str} | {ground_time_str} | {power_str} |\n"
            
            content += "\n"
        else:
            # 原有格式（API 数据，无步骤类型）
            content += """## 📊 分段数据

| 圈 | 距离 | 配速 | 用时 | 心率 | 步频 | 步幅(m) | 垂直振幅(cm) | 垂直比(%) | 触地(ms) | 功率(W) |
|:--:|:----:|:----:|:----:|:----:|:----:|:-------:|:------------:|:---------:|:--------:|:-------:|
"""
            for i, split in enumerate(splits, 1):
                km = split['distance_km']
                pace = split['pace']
                duration = split['duration']
                hr = split.get('avg_hr', '-')
                cadence = split.get('avg_cadence', '-')
                stride = split.get('stride_length', '-')
                vert_osc = split.get('vertical_oscillation', '-')
                vert_ratio = split.get('vertical_ratio', '-')
                ground_time = split.get('ground_contact_time', '-')
                power = split.get('avg_power', '-')
                
                # 格式化显示
                km_str = f"{km:.2f}" if km < 1 else f"{int(km)}"
                hr_str = f"{int(hr)}" if hr != '-' else '-'
                cadence_str = f"{cadence:.0f}" if cadence != '-' else '-'
                stride_str = f"{stride:.2f}" if stride != '-' else '-'
                vert_osc_str = f"{vert_osc:.1f}" if vert_osc != '-' else '-'
                vert_ratio_str = f"{vert_ratio:.1f}" if vert_ratio != '-' else '-'
                ground_time_str = f"{ground_time:.0f}" if ground_time != '-' else '-'
                power_str = f"{int(power)}" if power != '-' else '-'
                
                content += f"| {i} | {km_str} | {pace} | {duration} | {hr_str} | {cadence_str} | {stride_str} | {vert_osc_str} | {vert_ratio_str} | {ground_time_str} | {power_str} |\n"
            
            content += "\n"
        
        # 分段分析
        if len(splits) > 1:
            paces = [parse_pace(s['pace']) for s in splits if parse_pace(s['pace'])]
            if paces:
                avg_pace_sec = sum(paces) / len(paces)
                fastest = min(paces)
                slowest = max(paces)
                pace_variance = slowest - fastest
                
                content += f"""### 配速分析

- **平均配速**: {format_pace_from_seconds(avg_pace_sec)}
- **最快**: {format_pace_from_seconds(fastest)}
- **最慢**: {format_pace_from_seconds(slowest)}
- **波动**: {pace_variance}秒/km
- **配速稳定性**: {"优秀" if pace_variance < 10 else "良好" if pace_variance < 20 else "需改进"}

"""
    
    # 添加进步分析
    if progress:
        content += f"""## 📈 训练分析

- **{training_type}总次数**: {progress['total_runs']} 次

"""
        if progress['comparisons']:
            content += "**与上次对比**:\n"
            for comp in progress['comparisons']:
                content += f"- {comp}\n"
            content += "\n"
    
    # 添加笔记区域
    content += """## 📝 训练笔记

### 训练感受
<!-- 记录今天的身体状态、训练感受 -->

### 完成情况
<!-- 是否完成训练计划？有什么调整？ -->

### 下次改进
<!-- 下次训练需要注意什么？ -->

"""
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath, training_type

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_obsidian_note.py <json_data_file> <obsidian_path> [training_type] [user_input]", file=sys.stderr)
        sys.exit(1)
    
    json_file = sys.argv[1]
    obsidian_path = sys.argv[2]
    training_type = sys.argv[3] if len(sys.argv) > 3 else None
    user_input = sys.argv[4] if len(sys.argv) > 4 else None
    
    # 读取 JSON 数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 确保输出目录存在
    os.makedirs(obsidian_path, exist_ok=True)
    
    # 生成笔记
    filepath, final_type = generate_note(data, obsidian_path, training_type, user_input)
    
    print(f"✅ Created note: {filepath}")
    print(f"📁 Training type: {final_type}")

if __name__ == '__main__':
    main()
