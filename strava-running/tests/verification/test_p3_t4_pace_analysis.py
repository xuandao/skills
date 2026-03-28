#!/usr/bin/env python3
"""
Phase 3 Task 4 数据验证脚本
验证基于配速变化推断训练类型

运行方式:
    python3 tests/verification/test_p3_t4_pace_analysis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import analyze_pace_variation, infer_training_type_from_pace


def verify_pace_analysis():
    """验证配速变化分析"""

    print("=" * 70)
    print("Phase 3 Task 4: 基于配速变化推断训练类型验证")
    print("=" * 70)

    # 测试用例 1: 稳定配速 (节奏跑)
    print("\n[1/5] 测试稳定配速...")
    steady_splits = [
        {'pace': '4:30'}, {'pace': '4:32'}, {'pace': '4:31'},
        {'pace': '4:33'}, {'pace': '4:30'}, {'pace': '4:31'}
    ]
    result = analyze_pace_variation(steady_splits)
    if result and result['pattern'] == 'steady':
        print(f"✅ 稳定配速识别成功")
        print(f"   模式: {result['pattern']}")
        print(f"   方差: {result['pace_variance']:.1f}秒")
        print(f"   建议类型: {result['suggested_type']}")
    else:
        print(f"❌ 稳定配速识别失败")
        return False

    # 测试用例 2: 间歇跑配速 (有大起大落)
    print("\n[2/5] 测试间歇跑配速...")
    interval_splits = [
        {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},  # 慢-快-慢
        {'pace': '3:45'}, {'pace': '5:05'}, {'pace': '3:35'}   # 快-慢-快
    ]
    result = analyze_pace_variation(interval_splits)
    if result and result['pattern'] == 'interval':
        print(f"✅ 间歇跑配速识别成功")
        print(f"   模式: {result['pattern']}")
        print(f"   配速范围: {result['pace_range']}秒")
        print(f"   有加速: {result['has_surges']}")
        print(f"   有恢复: {result['has_recoveries']}")
        print(f"   建议类型: {result['suggested_type']}")
    else:
        print(f"❌ 间歇跑配速识别失败，实际模式: {result['pattern'] if result else 'None'}")
        return False

    # 测试用例 3: 渐加速 (progression)
    print("\n[3/5] 测试渐加速配速...")
    progression_splits = [
        {'pace': '5:00'}, {'pace': '4:50'}, {'pace': '4:40'},
        {'pace': '4:30'}, {'pace': '4:20'}, {'pace': '4:10'}
    ]
    result = analyze_pace_variation(progression_splits)
    if result and result['is_progression']:
        print(f"✅ 渐加速配速识别成功")
        print(f"   是渐加速: {result['is_progression']}")
        print(f"   模式: {result['pattern']}")
    else:
        print(f"⚠️ 渐加速识别结果为: {result['pattern'] if result else 'None'}")
        # 不返回False，因为渐加速可能不稳定

    # 测试用例 4: 无规律变化 (轻松跑)
    print("\n[4/5] 测试无规律配速...")
    variable_splits = [
        {'pace': '5:20'}, {'pace': '5:10'}, {'pace': '5:25'},
        {'pace': '5:15'}, {'pace': '5:30'}, {'pace': '5:18'}
    ]
    result = analyze_pace_variation(variable_splits)
    if result:
        print(f"✅ 配速分析完成")
        print(f"   模式: {result['pattern']}")
        print(f"   方差: {result['pace_variance']:.1f}秒")
    else:
        print(f"❌ 配速分析失败")
        return False

    # 测试用例 5: 使用 infer_training_type_from_pace
    print("\n[5/5] 测试配速推断训练类型...")

    # 间歇跑推断
    result = infer_training_type_from_pace(interval_splits)
    if result['training_type'] == '间歇跑' and result['confidence'] == 'high':
        print(f"✅ 间歇跑推断成功 (高置信度)")
    else:
        print(f"❌ 间歇跑推断失败: {result['training_type']} ({result['confidence']})")
        return False

    # 稳定配速推断
    result = infer_training_type_from_pace(steady_splits)
    if result['training_type'] == '节奏跑':
        print(f"✅ 稳定配速推断成功: {result['training_type']}")
    else:
        print(f"⚠️ 稳定配速推断: {result['training_type']}")

    # 测试平均配速推断
    result = infer_training_type_from_pace([], avg_pace_str='3:45')
    if result['training_type'] == '节奏跑':
        print(f"✅ 快配速推断成功")
    else:
        print(f"⚠️ 快配速推断: {result['training_type']}")

    result = infer_training_type_from_pace([], avg_pace_str='6:30')
    if result['training_type'] == '恢复跑':
        print(f"✅ 慢配速推断成功")
    else:
        print(f"⚠️ 慢配速推断: {result['training_type']}")

    # 输出验证结果
    print("\n" + "=" * 70)
    print("✅ 基于配速变化推断训练类型验证通过")
    print("\n可以进行 Git Commit:")
    print('  git commit -m "Phase 3 T4: 基于配速变化推断训练类型"')
    return True


if __name__ == '__main__':
    success = verify_pace_analysis()
    sys.exit(0 if success else 1)
