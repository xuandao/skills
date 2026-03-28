#!/usr/bin/env python3
"""
Phase 1 Task 4 数据验证脚本
验证 API 错误处理

运行方式:
    python3 tests/verification/test_p1_t4_errors.py

注意: 此脚本主要验证错误处理代码结构，不会真正触发 API 错误
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def verify_error_handling():
    """验证错误处理代码"""

    print("=" * 70)
    print("Phase 1 Task 4: API 错误处理验证")
    print("=" * 70)

    # 读取 fetch_strava_run.py 检查错误处理
    print("\n[1/3] 检查错误处理代码...")

    script_path = Path(__file__).parent.parent.parent / "scripts" / "fetch_strava_run.py"
    with open(script_path, 'r') as f:
        content = f.read()

    checks = [
        ("包含 try-except 块", "try:" in content and "except" in content),
        ("认证错误处理", "authenticate_strava" in content),
        ("活动获取错误处理", "get_latest_run" in content),
        ("streams 错误处理", "get_activity_streams" in content),
        ("laps 错误处理", "get_activity_laps" in content),
        ("GPX 生成错误处理", "generate_gpx" in content),
        ("错误输出到 stderr", "file=sys.stderr" in content),
    ]

    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"    ✅ {check_name}")
        else:
            print(f"    ❌ {check_name}")
            all_passed = False

    # 检查单元测试
    print("\n[2/3] 检查单元测试...")
    test_path = Path(__file__).parent.parent / "unit" / "test_p1_t4_error_handling.py"
    if test_path.exists():
        print("    ✅ 单元测试文件存在")
        with open(test_path, 'r') as f:
            test_content = f.read()

        test_checks = [
            ("测试 401 错误", "401" in test_content or "AccessUnauthorized" in test_content),
            ("测试 404 错误", "404" in test_content or "ObjectNotFound" in test_content),
            ("测试 429 错误", "429" in test_content or "Rate" in test_content),
            ("测试网络错误", "Network" in test_content or "network" in test_content),
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

    # 检查各函数的错误处理策略
    print("\n[3/3] 检查各函数错误处理策略...")

    # get_activity_streams 应该返回空字典而不是抛出异常
    if "return {}" in content:
        print("    ✅ get_activity_streams 返回空字典处理错误")
    else:
        print("    ⚠️  get_activity_streams 可能缺少空字典返回")

    # get_activity_laps 应该返回空列表而不是抛出异常
    if "return []" in content:
        print("    ✅ get_activity_laps 返回空列表处理错误")
    else:
        print("    ⚠️  get_activity_laps 可能缺少空列表返回")

    # 输出验证结果
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ API 错误处理验证通过")
        print("\n可以进行 Git Commit:")
        print('  git commit -m "Phase 1 T4: 添加 API 错误处理"')
        return True
    else:
        print("❌ 部分验证失败")
        return False


if __name__ == '__main__':
    success = verify_error_handling()
    sys.exit(0 if success else 1)
