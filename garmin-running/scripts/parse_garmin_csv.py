#!/usr/bin/env python3
"""
Parse Garmin CSV export file and convert to JSON format.
"""

import sys
import csv
import json
from datetime import datetime

def parse_time(time_str):
    """解析时间字符串 (MM:SS.S 或 HH:MM:SS.S)"""
    if not time_str or time_str == '--':
        return 0
    
    parts = time_str.replace('.', ':').split(':')
    if len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:  # HH:MM:SS or MM:SS.S
        if '.' in time_str:  # MM:SS.S
            mins, secs = time_str.split(':')
            return int(mins) * 60 + float(secs)
        else:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def parse_pace(pace_str):
    """解析配速字符串 (M:SS)"""
    if not pace_str or pace_str == '--':
        return "N/A"
    return pace_str

def parse_csv(csv_file):
    """解析 Garmin CSV 文件"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # 最后一行是统计数据
    summary = rows[-1]
    splits_data = rows[:-1]
    
    # 解析基本信息
    result = {
        'activity_name': '跑步',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': 'N/A',
        'distance_km': float(summary['距离']),
        'duration': summary['时间'],
        'duration_seconds': parse_time(summary['时间']),
        'avg_pace': summary['平均配速'],
        'avg_hr': float(summary['平均心率']) if summary['平均心率'] else None,
        'max_hr': float(summary['最大心率']) if summary['最大心率'] else None,
        'calories': float(summary['热量消耗']) if summary['热量消耗'] else None,
        'elevation_gain': 'N/A',
        'avg_cadence': float(summary['平均步频']) if summary['平均步频'] else None,
        'gpx_path': None,
        'splits': []
    }
    
    # 解析分段数据
    current_interval = ''
    for row in splits_data:
        # 如果是汇总行（圈数包含 "-"），提取间隔编号
        if '-' in row['圈数']:
            current_interval = row['间隔']
            continue
        
        split = {
            'lap_number': int(row['圈数']) if row['圈数'] else 0,
            'interval': current_interval if row['步骤类型'] == '跑步' else '',
            'step_type': row['步骤类型'],
            'distance_km': float(row['距离']) if row['距离'] else 0,
            'duration': row['时间'],
            'duration_seconds': parse_time(row['时间']),
            'pace': parse_pace(row['平均配速']),
            'avg_hr': float(row['平均心率']) if row['平均心率'] else None,
            'max_hr': float(row['最大心率']) if row['最大心率'] else None,
            'avg_cadence': float(row['平均步频']) if row['平均步频'] else None,
            'stride_length': float(row['平均步长']) if row['平均步长'] else None,
            'vertical_oscillation': float(row['平均垂直摆动']) if row['平均垂直摆动'] else None,
            'vertical_ratio': float(row['平均垂直步幅比']) if row['平均垂直步幅比'] else None,
            'ground_contact_time': float(row['平均触地时间']) if row['平均触地时间'] else None,
            'avg_power': float(row['平均功率']) if row['平均功率'] else None,
            'normalized_power': float(row['Normalized Power® (NP®)']) if row['Normalized Power® (NP®)'] else None,
            'avg_power_per_kg': float(row['平均 W/kg']) if row['平均 W/kg'] else None,
        }
        
        result['splits'].append(split)
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: parse_garmin_csv.py <csv_file>", file=sys.stderr)
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    try:
        result = parse_csv(csv_file)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Failed to parse CSV: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
