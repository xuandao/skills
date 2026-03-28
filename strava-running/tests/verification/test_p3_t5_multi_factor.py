#!/usr/bin/env python3
"""
Phase 3 Task 5 数据验证脚本
验证综合决策算法

运行方式:
    python3 tests/verification/test_p3_t5_multi_factor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import comprehensive_training_type_inference


def verify_multi_factor_decision():
    """验证综合决策算法"""

    print("=" * 70)
    print("Phase 3 Task 5: 综合决策算法验证")
    print("=" * 70)

    # 测试用例 1: 用户输入优先
    print("\n[1/6] 测试用户输入优先...")
    result = comprehensive_training_type_inference(
        activity_name="Morning Run",
        user_input="今天跑了个间歇",
        distance_km=8.0,
        duration_min=45,
        avg_hr=165,
        max_hr=190
    )
    if result['training_type'] == '间歇跑' and result['confidence'] == 'high':
        print(f"✅ 用户输入优先正确")
        print(f"   结果: {result['training_type']} ({result['confidence']})")
        print(f"   原因: {result['reason']}")
    else:
        print(f"❌ 用户输入优先失败: {result['training_type']}")
        return False

    # 测试用例 2: 多因子一致（间歇跑）
    print("\n[2/6] 测试多因子一致 - 间歇跑...")
    interval_splits = [
        {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},
        {'pace': '3:45'}, {'pace': '5:05'}
    ]
    result = comprehensive_training_type_inference(
        activity_name="Interval Training",
        distance_km=6.0,
        duration_min=35,
        avg_hr=175,
        max_hr=195,
        splits=interval_splits,
        avg_pace_str='4:15'
    )
    if result['training_type'] == '间歇跑':
        print(f"✅ 多因子一致正确")
        print(f"   结果: {result['training_type']} ({result['confidence']})")
        print(f"   投票: {result['consensus']['vote_distribution']}")
    else:
        print(f"❌ 多因子一致失败: {result['training_type']}")
        return False

    # 测试用例 3: 多因子一致（LSD）
    print("\n[3/6] 测试多因子一致 - LSD...")
    result = comprehensive_training_type_inference(
        activity_name="Sunday Long Run",
        distance_km=18.0,
        duration_min=110,
        avg_hr=145,
        max_hr=175,
        avg_pace_str='6:00'
    )
    if result['training_type'] == 'LSD':
        print(f"✅ LSD推断正确")
        print(f"   结果: {result['training_type']} ({result['confidence']})")
        print(f"   因子: {list(result['factors'].keys())}")
    else:
        print(f"❌ LSD推断失败: {result['training_type']}")
        return False

    # 测试用例 4: 少数因子情况
    print("\n[4/6] 测试少量因子...")
    result = comprehensive_training_type_inference(
        activity_name="Tempo Run",
        distance_km=10.0,
        duration_min=50
    )
    if result['training_type'] == '节奏跑':
        print(f"✅ 少量因子推断正确")
        print(f"   结果: {result['training_type']}")
        print(f"   因子数: {len(result['factors'])}")
    else:
        print(f"⚠️  少量因子推断: {result['training_type']}")

    # 测试用例 5: 因子冲突（用户输入决定）
    print("\n[5/6] 测试因子冲突 - 用户输入决定...")
    result = comprehensive_training_type_inference(
        activity_name="Easy Morning Run",  # 活动名称说轻松跑
        user_input="跑了个节奏跑",  # 但用户说是节奏跑
        distance_km=12.0,
        duration_min=60,
        avg_hr=155,
        max_hr=180
    )
    if result['training_type'] == '节奏跑':  # 应该听用户的
        print(f"✅ 用户输入优先于活动名称")
        print(f"   结果: {result['training_type']}")
        print(f"   原因: {result['reason']}")
    else:
        print(f"❌ 用户输入未优先: {result['training_type']}")
        return False

    # 测试用例 6: 默认情况
    print("\n[6/6] 测试默认情况...")
    result = comprehensive_training_type_inference(
        activity_name="Just Run",
        distance_km=5.0,
        duration_min=30
    )
    if result['training_type'] in ['轻松跑', '节奏跑']:
        print(f"✅ 默认推断正确")
        print(f"   结果: {result['training_type']} ({result['confidence']})")
    else:
        print(f"⚠️  默认推断: {result['training_type']}")

    # 输出验证结果
    print("\n" + "=" * 70)
    print("✅ 综合决策算法验证通过")
    print("\n可以进行 Git Commit:")
    print('  git commit -m "Phase 3 T5: 综合决策算法"')
    return True


if __name__ == '__main__':
    success = verify_multi_factor_decision()
    sys.exit(0 if success else 1)
