#!/usr/bin/env python3
"""
Generate Obsidian note from Garmin running data.
"""

import os
import sys
import json
from datetime import datetime

def generate_note(data, obsidian_path):
    """Generate Obsidian markdown note from running data"""
    
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
    
    # Generate filename
    filename = f"{date}-{activity_name.lower().replace(' ', '-')}.md"
    filepath = os.path.join(obsidian_path, filename)
    
    # Generate markdown content
    content = f"""---
date: {date}
type: running
distance: {distance}
duration: {duration}
pace: {avg_pace}
avg_hr: {avg_hr}
max_hr: {max_hr}
calories: {calories}
elevation: {elevation}
cadence: {cadence}
---

# {activity_name}

## 📊 基本数据

- **日期**: {date} {data['time']}
- **距离**: {distance} km
- **用时**: {duration}
- **配速**: {avg_pace} /km
- **卡路里**: {calories} kcal

## ❤️ 心率数据

- **平均心率**: {avg_hr} bpm
- **最大心率**: {max_hr} bpm

## 🏃 跑步数据

- **平均步频**: {cadence} spm
- **累计爬升**: {elevation} m

"""
    
    # Add GPX reference if available
    if gpx_path:
        gpx_filename = os.path.basename(gpx_path)
        content += f"""## 📍 GPS 轨迹

GPX 文件: `{gpx_filename}`

"""
    
    # Add notes section
    content += """## 📝 笔记

<!-- 在这里添加你的跑步感受和笔记 -->

"""
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_obsidian_note.py <json_data_file> <obsidian_path>", file=sys.stderr)
        sys.exit(1)
    
    json_file = sys.argv[1]
    obsidian_path = sys.argv[2]
    
    # Read JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure output directory exists
    os.makedirs(obsidian_path, exist_ok=True)
    
    # Generate note
    filepath = generate_note(data, obsidian_path)
    
    print(f"✅ Created note: {filepath}")

if __name__ == '__main__':
    main()
