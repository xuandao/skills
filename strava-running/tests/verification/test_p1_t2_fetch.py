#!/usr/bin/env python3
"""
Phase 1 Task 2 数据验证脚本
验证 fetch_strava_run.py 获取最新活动功能

运行方式:
    python3 tests/verification/test_p1_t2_fetch.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import (
    read_config,
    authenticate_strava,
    get_latest_run,
    get_activity_streams,
    get_activity_laps,
)


def verify_fetch_latest():
    """验证获取最新活动功能"""

    print("=" * 70)
    print("Phase 1 Task 2: 获取最新活动数据验证")
    print("=" * 70)

    # 读取配置
    print("\n[1/5] 读取配置...")
    try:
        config = read_config()
        print("✅ 配置读取成功")
    except Exception as e:
        print(f"❌ 配置读取失败: {e}")
        return False

    # 认证
    print("\n[2/5] 认证 Strava API...")
    try:
        client = authenticate_strava(config)
        print("✅ 认证成功")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return False

    # 获取最新活动
    print("\n[3/5] 获取最新跑步活动...")
    try:
        activity = get_latest_run(client)
        print(f"✅ 获取活动成功")
        print(f"    ID: {activity.id}")
        print(f"    名称: {activity.name}")
        print(f"    类型: {activity.type}")
        print(f"    距离: {activity.distance}")
        print(f"    时间: {activity.moving_time}")
    except Exception as e:
        print(f"❌ 获取活动失败: {e}")
        return False

    # 获取 streams
    print("\n[4/5] 获取活动 streams...")
    try:
        streams = get_activity_streams(client, activity.id)
        print(f"✅ Streams 获取成功")
        print(f"    可用 streams: {list(streams.keys())}")
    except Exception as e:
        print(f"❌ Streams 获取失败: {e}")
        return False

    # 获取 laps
    print("\n[5/5] 获取活动 laps...")
    try:
        laps = get_activity_laps(client, activity.id)
        print(f"✅ Laps 获取成功")
        print(f"    计圈数量: {len(laps)}")
        if laps:
            print(f"    第一圈: {laps[0].lap_index}, 距离: {laps[0].distance}")
    except Exception as e:
        print(f"❌ Laps 获取失败: {e}")
        return False

    # 验证跑步机/户外跑判断
    print("\n" + "-" * 70)
    print("GPS 数据检查:")
    if activity.map and activity.map.summary_polyline:
        print("✅ 有 GPS 数据 (户外跑)")
    else:
        print("⚠️  无 GPS 数据 (跑步机)")

    # 输出验证结果
    print("\n" + "=" * 70)
    print("✅ 获取最新活动功能验证通过")
    print("\n可以进行 Git Commit:")
    print('  git commit -m "Phase 1 T2: 测试获取最新活动功能"')
    return True


if __name__ == '__main__':
    success = verify_fetch_latest()
    sys.exit(0 if success else 1)
