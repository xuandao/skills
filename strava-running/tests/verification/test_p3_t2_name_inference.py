#!/usr/bin/env python3
"""
Phase 3 Task 2 数据验证脚本
验证活动名称智能推断

运行方式:
    python3 tests/verification/test_p3_t2_name_inference.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import analyze_activity_name


def verify_name_inference():
    """验证活动名称智能推断"""

    print("=" * 70)
    print("Phase 3 Task 2: 活动名称智能推断验证")
    print("=" * 70)

    # 测试用例: (活动名称, 距离km, 时长min, 期望类型)
    test_cases = [
        # 关键词高置信度匹配
        ("Morning Interval Run", None, None, "间歇跑"),
        ("Tempo Tuesday", None, None, "节奏跑"),
        ("Sunday LSD", None, None, "LSD"),
        ("Easy Recovery Run", None, None, "轻松跑"),
        ("Treadmill Session", None, None, "跑步机"),
        ("Marathon Pace Practice", None, None, "马拉松配速跑"),

        # 中文关键词
        ("无锡马拉松", None, None, "马拉松配速跑"),
        ("周末长距离", None, None, "LSD"),
        ("间歇训练", None, None, "间歇跑"),
        ("节奏跑", None, None, "节奏跑"),

        # 基于距离和时间的启发式推断
        ("Morning Run", 21.0, 120, "LSD"),  # 半马距离
        ("Evening Jog", 3.0, 20, "轻松跑"),  # 短距离
        ("Long Run", 16.0, 90, "LSD"),  # 长距离
        ("Short Run", 4.0, 25, "轻松跑"),  # 短距离慢配速

        # 默认情况
        ("Just Run", None, None, "轻松跑"),
        ("Running", 10.0, 50, "轻松跑"),  # 无关键词但有数据
    ]

    print(f"\n测试 {len(test_cases)} 个活动名称推断...\n")

    passed = 0
    failed = 0

    for activity_name, distance, duration, expected in test_cases:
        result = analyze_activity_name(activity_name, distance, duration)
        actual_type = result['training_type']
        confidence = result['confidence']
        reason = result['reason']

        if actual_type == expected:
            print(f"✅ '{activity_name}' -> {actual_type} ({confidence})")
            print(f"   原因: {reason}")
            passed += 1
        else:
            print(f"❌ '{activity_name}' -> {actual_type}, 期望 {expected}")
            print(f"   原因: {reason}")
            failed += 1

    # 输出验证结果
    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("✅ 活动名称智能推断验证通过")
        print("\n可以进行 Git Commit:")
        print('  git commit -m "Phase 3 T2: 实现活动名称智能推断"')
        return True
    else:
        print(f"❌ 有 {failed} 个测试失败")
        return False


if __name__ == '__main__':
    success = verify_name_inference()
    sys.exit(0 if success else 1)
