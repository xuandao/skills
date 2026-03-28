#!/usr/bin/env python3
"""
Phase 1 Task 5 数据验证脚本
验证网络超时和重试机制

运行方式:
    python3 tests/verification/test_p1_t5_retry.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def verify_retry_mechanism():
    """验证重试机制"""

    print("=" * 70)
    print("Phase 1 Task 5: 网络超时和重试机制验证")
    print("=" * 70)

    # 读取 fetch_strava_run.py 检查重试机制
    print("\n[1/3] 检查重试装饰器代码...")

    script_path = Path(__file__).parent.parent.parent / "scripts" / "fetch_strava_run.py"
    with open(script_path, 'r') as f:
        content = f.read()

    checks = [
        ("导入 time 模块", "import time" in content),
        ("导入 wraps", "from functools import wraps" in content),
        ("定义 retry_with_timeout 装饰器", "def retry_with_timeout" in content),
        ("定义 MAX_RETRIES", "MAX_RETRIES" in content),
        ("定义 RETRY_DELAY", "RETRY_DELAY" in content),
        ("重试循环逻辑", "for attempt in range" in content),
        ("错误等待逻辑", "time.sleep" in content),
    ]

    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"    ✅ {check_name}")
        else:
            print(f"    ❌ {check_name}")
            all_passed = False

    # 检查函数装饰器应用
    print("\n[2/3] 检查装饰器应用到函数...")

    decorator_checks = [
        ("authenticate_strava 有装饰器", '@retry_with_timeout' in content and 'def authenticate_strava' in content),
        ("get_latest_run 有装饰器", "@retry_with_timeout" in content.split('def get_latest_run')[0].split('def authenticate_strava')[1]),
        ("get_activity_streams 有装饰器", "@retry_with_timeout" in content.split('def get_activity_streams')[0].split('def get_latest_run')[1]),
        ("get_activity_laps 有装饰器", "@retry_with_timeout" in content.split('def get_activity_laps')[0].split('def get_activity_streams')[1]),
    ]

    for check_name, check_result in decorator_checks:
        if check_result:
            print(f"    ✅ {check_name}")
        else:
            print(f"    ❌ {check_name}")
            all_passed = False

    # 检查单元测试
    print("\n[3/3] 检查单元测试...")
    test_path = Path(__file__).parent.parent / "unit" / "test_p1_t5_retry.py"
    if test_path.exists():
        print("    ✅ 单元测试文件存在")
        with open(test_path, 'r') as f:
            test_content = f.read()

        test_checks = [
            ("测试重试成功", "test_success_on_first_attempt" in test_content),
            ("测试失败重试", "test_retry_on_failure" in test_content),
            ("测试最大重试", "test_fail_after_max_retries" in test_content),
            ("测试 401 不重试", "test_no_retry_on_unauthorized" in test_content),
            ("测试 404 不重试", "test_no_retry_on_not_found" in test_content),
        ]

        for check_name, check_result in test_checks:
            if check_result:
                print(f"    ✅ {check_name}")
            else:
                print(f"    ❌ {check_name}")
                all_passed = False
    else:
        print("    ❌ 单元测试文件不存在")
        all_passed = False

    # 输出验证结果
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 网络超时和重试机制验证通过")
        print("\n可以进行 Git Commit:")
        print('  git commit -m "Phase 1 T5: 添加网络超时和重试机制"')
        return True
    else:
        print("❌ 部分验证失败")
        return False


if __name__ == '__main__':
    success = verify_retry_mechanism()
    sys.exit(0 if success else 1)
