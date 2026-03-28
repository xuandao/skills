#!/usr/bin/env python3
"""
Phase 3 Task 3 数据验证脚本
验证基于心率区间推断训练强度

运行方式:
    python3 tests/verification/test_p3_t3_hr_zones.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import (
    analyze_hr_zones,
    infer_training_type_from_hr
)


def verify_hr_zones():
    """验证心率区间分析"""

    print("=" * 70)
    print("Phase 3 Task 3: 基于心率区间推断训练强度验证")
    print("=" * 70)

    # 测试用例: (平均心率, 最大心率, 时长, 期望区间, 期望类型)
    # 假设最大心率 190
    test_cases = [
        # Zone 1: 恢复跑
        (95, 190, None, 1, "恢复跑", "低"),
        (110, 190, None, 1, "恢复跑", "低"),

        # Zone 2: 轻松跑
        (120, 190, None, 2, "轻松跑", "低-中"),
        (130, 190, None, 2, "轻松跑", "低-中"),

        # Zone 3: 马拉松配速跑
        (140, 190, None, 3, "马拉松配速跑", "中"),
        (150, 190, None, 3, "马拉松配速跑", "中"),

        # Zone 4: 节奏跑
        (160, 190, None, 4, "节奏跑", "高"),
        (170, 190, None, 4, "节奏跑", "高"),

        # Zone 5: 间歇跑
        (175, 190, None, 5, "间歇跑", "极高"),
        (185, 190, None, 5, "间歇跑", "极高"),

        # 结合时长的判断
        (170, 190, 20, 4, "节奏跑", "高"),  # 高心率+短时长=节奏跑（Zone 4）
        (145, 190, 120, 3, "LSD", "中"),   # 中心率+长时长=LSD
    ]

    print(f"\n测试 {len(test_cases)} 个心率区间推断...\n")

    passed = 0
    failed = 0

    for avg_hr, max_hr, duration, expected_zone, expected_type, expected_intensity in test_cases:
        result = infer_training_type_from_hr(avg_hr, max_hr, duration)

        actual_type = result['training_type']
        actual_zone = result['zone_info']['zone_num'] if result['zone_info'] else None
        actual_intensity = result['zone_info']['intensity'] if result['zone_info'] else None

        if actual_type == expected_type and actual_zone == expected_zone:
            print(f"✅ 心率{avg_hr} -> Zone {actual_zone} ({actual_intensity}) -> {actual_type}")
            print(f"   原因: {result['reason']}")
            passed += 1
        else:
            print(f"❌ 心率{avg_hr} -> Zone {actual_zone} ({actual_type}), 期望 Zone {expected_zone} ({expected_type})")
            failed += 1

    # 测试 analyze_hr_zones 单独功能
    print("\n" + "-" * 70)
    print("测试心率区间边界值...\n")

    boundary_tests = [
        # (平均心率, 期望区间)
        (100, 1),   # < 114 (190*0.6)
        (120, 2),   # 114-133 (190*0.6-0.7)
        (140, 3),   # 133-152 (190*0.7-0.8)
        (160, 4),   # 152-171 (190*0.8-0.9)
        (175, 5),   # > 171 (190*0.9)
    ]

    for avg_hr, expected_zone in boundary_tests:
        result = analyze_hr_zones(avg_hr, 190)
        if result and result['zone_num'] == expected_zone:
            print(f"✅ 心率{avg_hr} -> Zone {result['zone_num']}: {result['avg_zone']}")
            passed += 1
        else:
            actual_zone = result['zone_num'] if result else None
            print(f"❌ 心率{avg_hr} -> Zone {actual_zone}, 期望 Zone {expected_zone}")
            failed += 1

    # 输出验证结果
    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("✅ 基于心率区间推断训练强度验证通过")
        print("\n可以进行 Git Commit:")
        print('  git commit -m "Phase 3 T3: 基于心率区间推断训练强度"')
        return True
    else:
        print(f"❌ 有 {failed} 个测试失败")
        return False


if __name__ == '__main__':
    success = verify_hr_zones()
    sys.exit(0 if success else 1)
