#!/usr/bin/env python3
"""
Garmin Connect API 探索脚本
用于发现可用的日常健康数据接口
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from garth import Client
except ImportError:
    print("❌ Please install garth: pip3 install garth", file=sys.stderr)
    sys.exit(1)


def read_config():
    """Read Garmin credentials from config file"""
    script_dir = Path(__file__).parent.parent.parent / "garmin-running"
    config_file = script_dir / "references" / "garmin_config.json"

    if not config_file.exists():
        # Try daily-summary skill config
        script_dir = Path(__file__).parent.parent
        config_file = script_dir / "references" / "garmin_config.json"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    return config.get('email'), config.get('password')


def login_garmin(email, password):
    """Login to Garmin Connect using garth"""
    try:
        client = Client()
        client.login(email, password)
        return client
    except Exception as e:
        print(f"❌ Login failed: {e}", file=sys.stderr)
        sys.exit(1)


def try_endpoint(client, endpoint, params=None, description=""):
    """尝试调用一个 API 端点"""
    try:
        result = client.connectapi(endpoint, params=params or {})
        print(f"✅ {description}")
        print(f"   Endpoint: {endpoint}")
        print(f"   Data keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        if isinstance(result, dict) and result:
            # 打印部分数据示例
            sample = dict(list(result.items())[:3])
            print(f"   Sample: {json.dumps(sample, indent=2, ensure_ascii=False)[:300]}...")
        print()
        return result
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Endpoint: {endpoint}")
        print(f"   Error: {str(e)[:100]}")
        print()
        return None


def explore_user_summary(client):
    """探索用户每日摘要数据"""
    print("=" * 60)
    print("📊 探索用户每日摘要数据")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    # 可能的端点
    endpoints = [
        ("/usersummary-service/usersummary/daily", {"calendarDate": today}, "每日摘要"),
        ("/usersummary-service/usersummary/weekly", {}, "每周摘要"),
        ("/usersummary-service/usersummary/monthly", {}, "每月摘要"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_heart_rate_data(client):
    """探索心率数据接口"""
    print("=" * 60)
    print("❤️ 探索心率数据接口")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 可能的端点
    endpoints = [
        ("/wellness-service/wellness/dailyHeartRate", {"date": today}, "每日心率"),
        ("/wellness-service/wellness/heartRate", {}, "心率数据"),
        ("/wellness-service/wellness/dailyStats", {"date": today}, "每日健康统计"),
        ("/wellness-service/wellness/dailyStress", {"date": today}, "每日压力"),
        ("/wellness-service/wellness/dailySleep", {"date": today}, "每日睡眠"),
        ("/wellness-service/wellness/dailySpo2", {"date": today}, "每日血氧"),
        ("/wellness-service/wellness/dailyRespiration", {"date": today}, "每日呼吸"),
        ("/wellness-service/wellness/dailyBodyBattery", {"date": today}, "每日身体电量"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_resting_hr(client):
    """探索静息心率数据"""
    print("=" * 60)
    print("💓 探索静息心率数据")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    endpoints = [
        ("/userstats-service/statistics/restingHeartRate", {}, "静息心率统计"),
        ("/userstats-service/statistics/heartRate", {}, "心率统计"),
        ("/userstats-service/statistics/daily", {}, "每日统计"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_hrv_data(client):
    """探索 HRV 数据"""
    print("=" * 60)
    print("📈 探索 HRV 数据")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    endpoints = [
        ("/hrv-service/hrv/daily", {"date": today}, "每日 HRV"),
        ("/hrv-service/hrv/stats", {}, "HRV 统计"),
        ("/wellness-service/wellness/dailyHrv", {"date": today}, "每日 HRV (wellness)"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_body_battery(client):
    """探索 Body Battery 数据"""
    print("=" * 60)
    print("🔋 探索 Body Battery 数据")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    endpoints = [
        ("/bodybattery-service/bodybattery/daily", {"date": today}, "每日 Body Battery"),
        ("/bodybattery-service/bodybattery/stats", {}, "Body Battery 统计"),
        ("/bodybattery-service/bodybattery/weekly", {}, "每周 Body Battery"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_sleep_data(client):
    """探索睡眠数据"""
    print("=" * 60)
    print("😴 探索睡眠数据")
    print("=" * 60)

    today = datetime.now().strftime("%Y-%m-%d")

    endpoints = [
        ("/wellness-service/wellness/dailySleepData", {"date": today}, "每日睡眠数据"),
        ("/sleep-service/sleep/daily", {"date": today}, "每日睡眠"),
        ("/sleep-service/sleep/stats", {}, "睡眠统计"),
    ]

    for endpoint, params, desc in endpoints:
        try_endpoint(client, endpoint, params, desc)


def explore_user_profile(client):
    """探索用户资料"""
    print("=" * 60)
    print("👤 探索用户资料")
    print("=" * 60)

    try:
        profile = client.profile
        print(f"✅ 用户资料")
        print(f"   Username: {client.username}")
        print(f"   Profile keys: {list(profile.keys()) if isinstance(profile, dict) else 'N/A'}")
        if isinstance(profile, dict):
            sample = {k: v for k, v in profile.items() if k in ['id', 'username', 'displayName', 'birthdate']}
            print(f"   Sample: {json.dumps(sample, indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"❌ 用户资料")
        print(f"   Error: {e}")
        print()


def main():
    print("🔍 Garmin Connect API 探索工具")
    print("=" * 60)
    print()

    # 读取配置
    print("📖 Reading config...")
    email, password = read_config()

    # 登录
    print("🔐 Logging in to Garmin Connect...")
    client = login_garmin(email, password)
    print(f"✅ Logged in as: {client.username}")
    print()

    # 探索各种数据接口
    explore_user_profile(client)
    explore_user_summary(client)
    explore_heart_rate_data(client)
    explore_resting_hr(client)
    explore_hrv_data(client)
    explore_body_battery(client)
    explore_sleep_data(client)

    print("=" * 60)
    print("✅ 探索完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
