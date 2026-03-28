#!/usr/bin/env python3
"""
Phase 1 Task 6 端到端测试
测试完整流程

运行方式:
    python3 tests/verification/test_p1_t6_e2e.py
"""

import json
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import (
    read_config,
    authenticate_strava,
    get_latest_run,
    get_activity_streams,
    get_activity_laps,
    analyze_activity,
)
from scripts.generate_strava_note import generate_note


def test_e2e_flow():
    """测试端到端流程"""

    print("=" * 70)
    print("Phase 1 Task 6: 端到端流程测试")
    print("=" * 70)

    # Step 1: 读取配置
    print("\n[1/6] 读取配置...")
    try:
        config = read_config()
        print(f"✅ 配置读取成功")
        print(f"    Obsidian 路径: {config.get('obsidian_path', 'N/A')}")
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")
        return False

    # Step 2: 认证
    print("\n[2/6] 认证 Strava API...")
    try:
        client = authenticate_strava(config)
        print("✅ 认证成功")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return False

    # Step 3: 获取最新跑步活动
    print("\n[3/6] 获取最新跑步活动...")
    try:
        activity = get_latest_run(client)
        print(f"✅ 获取活动成功")
        print(f"    ID: {activity.id}")
        print(f"    名称: {activity.name}")
        print(f"    日期: {activity.start_date_local}")
    except Exception as e:
        print(f"❌ 获取活动失败: {e}")
        return False

    # Step 4: 获取 Streams
    print("\n[4/6] 获取活动 Streams...")
    try:
        streams = get_activity_streams(client, activity.id)
        print(f"✅ Streams 获取成功")
        print(f"    可用: {list(streams.keys()) if streams else 'None (跑步机)'}")
    except Exception as e:
        print(f"❌ Streams 获取失败: {e}")
        return False

    # Step 5: 获取 Laps
    print("\n[5/6] 获取活动 Laps...")
    try:
        laps = get_activity_laps(client, activity.id)
        print(f"✅ Laps 获取成功")
        print(f"    计圈数: {len(laps)}")
    except Exception as e:
        print(f"❌ Laps 获取失败: {e}")
        return False

    # Step 6: 分析活动并生成笔记
    print("\n[6/6] 分析活动并生成笔记...")
    try:
        # 分析活动数据
        result = analyze_activity(activity, streams, laps, gpx_path=None)

        print(f"✅ 活动分析成功")
        print(f"    距离: {result['distance_km']} km")
        print(f"    配速: {result['avg_pace']}")
        print(f"    用时: {result['duration']}")

        # 生成笔记
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = generate_note(result, tmpdir, training_type=None)
            print(f"✅ 笔记生成成功")
            print(f"    路径: {note_path}")

            # 验证笔记内容
            with open(note_path, 'r') as f:
                content = f.read()

            required_elements = [
                '---',  # frontmatter
                result['date'],
                result['activity_name'],
                str(result['distance_km']),
            ]

            all_found = all(elem in content for elem in required_elements)
            if all_found:
                print("✅ 笔记内容验证通过")
            else:
                print("❌ 笔记内容不完整")
                return False

    except Exception as e:
        print(f"❌ 分析或生成笔记失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 输出测试结果
    print("\n" + "=" * 70)
    print("✅ 端到端流程测试通过")
    print("\n可以进行 Git Commit:")
    print('  git commit -m "Phase 1 T6: 端到端流程测试"')
    return True


if __name__ == '__main__':
    success = test_e2e_flow()
    sys.exit(0 if success else 1)
