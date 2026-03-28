#!/usr/bin/env python3
"""
Phase 3 Task 1 数据验证脚本
验证用户输入识别功能

运行方式:
    python3 tests/verification/test_p3_t1_input_detection.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import get_training_type


def verify_input_detection():
    """验证用户输入识别"""

    print("=" * 70)
    print("Phase 3 Task 1: 用户输入识别验证")
    print("=" * 70)

    # 测试用例: (用户输入, 期望结果)
    test_cases = [
        # 间歇跑
        ("今天跑了个间歇", "间歇跑"),
        ("HIIT训练", "间歇跑"),
        ("法特莱克跑", "间歇跑"),
        ("变速跑练习", "间歇跑"),
        ("跑了个interval", "间歇跑"),
        ("高强度间歇训练", "间歇跑"),

        # 节奏跑
        ("节奏跑完成了", "节奏跑"),
        ("今天tempo run", "节奏跑"),
        ("乳酸阈值训练", "节奏跑"),
        ("threshold训练", "节奏跑"),
        ("节奏训练", "节奏跑"),
        ("跑了个tempo", "节奏跑"),

        # LSD
        ("周末LSD", "LSD"),
        ("长距离慢跑", "LSD"),
        ("lsd训练", "LSD"),
        ("周末长距离", "LSD"),
        ("long run", "LSD"),
        ("lsd长距离", "LSD"),

        # 轻松跑
        ("轻松跑一下", "轻松跑"),
        ("easy run", "轻松跑"),
        ("有氧慢跑", "轻松跑"),
        ("轻松训练", "轻松跑"),
        ("有氧基础跑", "轻松跑"),
        ("easy jog", "轻松跑"),

        # 恢复跑
        ("恢复跑", "恢复跑"),
        ("recovery run", "恢复跑"),
        ("放松慢跑", "恢复跑"),  # 放松属于恢复跑
        ("排酸跑", "恢复跑"),
        ("休息恢复", "恢复跑"),
        ("recovery jog", "恢复跑"),

        # 跑步机
        ("跑步机训练", "跑步机"),
        ("treadmill run", "跑步机"),
        ("室内跑步", "跑步机"),
        ("gym跑步", "跑步机"),
        ("跑跑步机", "跑步机"),
        ("室内训练", "跑步机"),

        # 马拉松配速跑
        ("马拉松配速训练", "马拉松配速跑"),
        ("马配跑", "马拉松配速跑"),
        ("MP训练", "马拉松配速跑"),
        ("marathon pace", "马拉松配速跑"),
        ("比赛配速跑", "马拉松配速跑"),
        ("目标配速训练", "马拉松配速跑"),

        # 无匹配时默认轻松跑
        ("随便跑一下", "轻松跑"),
        ("日常跑步", "轻松跑"),
        ("", "轻松跑"),
    ]

    print(f"\n测试 {len(test_cases)} 个输入用例...\n")

    passed = 0
    failed = 0

    for user_input, expected in test_cases:
        result = get_training_type("Morning Run", user_input)
        if result == expected:
            print(f"✅ '{user_input}' -> {result}")
            passed += 1
        else:
            print(f"❌ '{user_input}' -> {result}, 期望 {expected}")
            failed += 1

    # 输出验证结果
    print("\n" + "=" * 70)
    print(f"测试结果: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("✅ 用户输入识别验证通过")
        print("\n可以进行 Git Commit:")
        print('  git commit -m "Phase 3 T1: 优化用户输入识别"')
        return True
    else:
        print(f"❌ 有 {failed} 个测试失败")
        return False


if __name__ == '__main__':
    success = verify_input_detection()
    sys.exit(0 if success else 1)
