#!/usr/bin/env python3
"""
Phase 1 Task 1 数据验证脚本
验证 fetch_strava_run.py 中的单位转换功能

运行方式:
    python3 tests/verification/test_p1_t1_units.py
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stravalib.client import Client


def verify_unit_conversion():
    """验证单位转换功能"""

    print("=" * 70)
    print("Phase 1 Task 1: 单位转换数据验证")
    print("=" * 70)

    # 读取配置
    config_path = Path(__file__).parent.parent.parent / "references" / "strava_config.json"
    with open(config_path) as f:
        config = json.load(f)

    # 认证
    print("\n[1/3] 正在认证 Strava API...")
    client = Client()
    try:
        refresh = client.refresh_access_token(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            refresh_token=config['refresh_token']
        )
        client.access_token = refresh['access_token']
        print("✅ 认证成功")
    except Exception as e:
        print(f"❌ 认证失败: {e}")
        return False

    # 获取最近2条活动进行验证
    print("\n[2/3] 获取最近2条活动...")
    try:
        activities = list(client.get_activities(limit=2))
        print(f"✅ 获取到 {len(activities)} 条活动")
    except Exception as e:
        print(f"❌ 获取活动失败: {e}")
        return False

    # 验证单位转换
    print("\n[3/3] 验证单位转换...")
    all_passed = True

    for i, act in enumerate(activities, 1):
        print(f"\n  活动 {i}: {act.name}")
        print(f"    ID: {act.id}")

        # 验证距离
        if act.distance:
            print(f"    distance: {act.distance} (类型: {type(act.distance).__name__})")
            try:
                distance_m = float(act.distance.magnitude if hasattr(act.distance, 'magnitude') else act.distance)
                print(f"    ✅ 距离转换: {distance_m} m")
            except Exception as e:
                print(f"    ❌ 距离转换失败: {e}")
                all_passed = False

        # 验证速度
        if act.average_speed:
            print(f"    average_speed: {act.average_speed} (类型: {type(act.average_speed).__name__})")
            try:
                speed = float(act.average_speed.magnitude
                              if hasattr(act.average_speed, 'magnitude')
                              else act.average_speed)
                pace_sec_per_km = 1000 / speed
                pace_min = int(pace_sec_per_km // 60)
                pace_sec = int(pace_sec_per_km % 60)
                print(f"    ✅ 速度转换: {speed:.2f} m/s -> {pace_min}:{pace_sec:02d}/km")
            except Exception as e:
                print(f"    ❌ 速度转换失败: {e}")
                all_passed = False

        # 验证时间
        if act.moving_time:
            print(f"    moving_time: {act.moving_time} (类型: {type(act.moving_time).__name__})")
            try:
                duration_sec = act.moving_time.total_seconds()
                print(f"    ✅ 时间转换: {duration_sec} 秒")
            except Exception as e:
                print(f"    ❌ 时间转换失败: {e}")
                all_passed = False

        # 验证海拔
        if act.total_elevation_gain:
            print(f"    elevation_gain: {act.total_elevation_gain} (类型: {type(act.total_elevation_gain).__name__})")
            try:
                elevation = float(act.total_elevation_gain.magnitude
                                  if hasattr(act.total_elevation_gain, 'magnitude')
                                  else act.total_elevation_gain)
                print(f"    ✅ 海拔转换: {elevation} m")
            except Exception as e:
                print(f"    ❌ 海拔转换失败: {e}")
                all_passed = False

    # 输出验证结果
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 所有单位转换验证通过")
        print("\n可以进行 Git Commit:")
        print("  git add .")
        print("  git commit -m \"Phase 1 T1: 修复单位转换问题\n\")")
        return True
    else:
        print("❌ 部分验证失败，请修复后再提交")
        return False


if __name__ == '__main__':
    success = verify_unit_conversion()
    sys.exit(0 if success else 1)
