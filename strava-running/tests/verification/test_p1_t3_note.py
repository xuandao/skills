#!/usr/bin/env python3
"""
Phase 1 Task 3 数据验证脚本
验证 generate_strava_note.py 笔记生成功能

运行方式:
    python3 tests/verification/test_p1_t3_note.py
"""

import json
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import (
    generate_note,
    get_training_type,
    analyze_hr_zones,
    parse_pace,
    TRAINING_TYPES,
)


def verify_note_generation():
    """验证笔记生成功能"""

    print("=" * 70)
    print("Phase 1 Task 3: 笔记生成数据验证")
    print("=" * 70)

    # 准备测试数据
    test_data = {
        "activity_id": 17848143875,
        "activity_name": "Morning Run",
        "activity_type": "running",
        "date": "2026-03-25",
        "time": "08:22",
        "distance_km": 6.73,
        "duration": "33:34",
        "duration_seconds": 2014,
        "avg_pace": "4:59",
        "avg_hr": 157.2,
        "max_hr": 193,
        "calories": 363,
        "elevation_gain": "N/A",
        "avg_cadence": 93.0,
        "gpx_path": None,
        "splits": [
            {
                "lap_number": 1,
                "distance_km": 1.0,
                "duration": "5:24",
                "pace": "5:23",
                "avg_hr": 124,
                "max_hr": 137,
            },
            {
                "lap_number": 2,
                "distance_km": 1.0,
                "duration": "5:09",
                "pace": "5:08",
                "avg_hr": 140,
                "max_hr": 145,
            },
        ],
        "strava_data": {
            "average_speed": 3.34,
            "max_speed": 4.24,
            "average_watts": 271.5,
            "kilojoules": 546.8,
            "has_heartrate": True,
            "suffer_score": None,
        }
    }

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        print("\n[1/4] 测试笔记生成...")
        try:
            filepath = generate_note(test_data, tmpdir, "跑步机")
            print(f"✅ 笔记生成成功")
            print(f"    路径: {filepath}")

            # 验证文件存在
            if os.path.exists(filepath):
                print("✅ 文件已创建")
            else:
                print("❌ 文件未创建")
                return False

            # 验证文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            checks = [
                ("包含 frontmatter", "---" in content),
                ("包含活动名称", "Morning Run" in content),
                ("包含日期", "2026-03-25" in content),
                ("包含距离", "6.73" in content),
                ("包含配速", "4:59" in content),
                ("包含心率", "157.2" in content),
                ("包含训练类型", "跑步机" in content),
                ("包含分段数据", "圈数" in content),
                ("包含感受记录", "训练感受" in content),
            ]

            for check_name, check_result in checks:
                if check_result:
                    print(f"    ✅ {check_name}")
                else:
                    print(f"    ❌ {check_name}")
                    return False

        except Exception as e:
            print(f"❌ 笔记生成失败: {e}")
            return False

        # 测试训练类型识别
        print("\n[2/4] 测试训练类型识别...")
        test_cases = [
            ("跑了个间歇", None, "间歇跑"),
            ("Morning Run", None, "轻松跑"),  # 默认
            ("Tempo Run", None, "节奏跑"),
            (None, "跑步机训练", "跑步机"),
        ]

        for activity_name, user_input, expected in test_cases:
            result = get_training_type(activity_name or "Run", user_input)
            if result == expected:
                print(f"    ✅ '{activity_name or user_input}' -> {result}")
            else:
                print(f"    ❌ '{activity_name or user_input}' -> {result}, 期望 {expected}")
                return False

        # 测试心率区间分析
        print("\n[3/4] 测试心率区间分析...")
        hr_result = analyze_hr_zones(157.2, 193)
        if hr_result:
            print(f"    ✅ 心率区间分析成功")
            print(f"    估算最大心率: {hr_result['estimated_max_hr']}")
            print(f"    平均区间: {hr_result['avg_zone']}")
        else:
            print("❌ 心率区间分析失败")
            return False

        # 测试配速解析
        print("\n[4/4] 测试配速解析...")
        pace_tests = [
            ("4:59", 299),
            ("5:30", 330),
            ("N/A", None),
        ]

        for pace_str, expected in pace_tests:
            result = parse_pace(pace_str)
            if result == expected:
                print(f"    ✅ '{pace_str}' -> {result}秒")
            else:
                print(f"    ❌ '{pace_str}' -> {result}秒, 期望 {expected}")
                return False

    # 输出验证结果
    print("\n" + "=" * 70)
    print("✅ 笔记生成功能验证通过")
    print("\n可以进行 Git Commit:")
    print('  git commit -m "Phase 1 T3: 测试笔记生成功能"')
    return True


if __name__ == '__main__':
    success = verify_note_generation()
    sys.exit(0 if success else 1)
