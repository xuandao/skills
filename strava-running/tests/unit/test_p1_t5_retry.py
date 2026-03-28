#!/usr/bin/env python3
"""
Phase 1 Task 5 单元测试
测试网络超时和重试机制

运行方式:
    python3 -m pytest tests/unit/test_p1_t5_retry.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import (
    retry_with_timeout,
    MAX_RETRIES,
    RETRY_DELAY,
)


class TestRetryWithTimeout:
    """测试重试装饰器"""

    def test_success_on_first_attempt(self):
        """测试第一次就成功"""
        call_count = 0

        @retry_with_timeout(max_retries=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """测试失败时重试"""
        call_count = 0

        @retry_with_timeout(max_retries=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3

    def test_fail_after_max_retries(self):
        """测试最大重试后失败"""
        call_count = 0

        @retry_with_timeout(max_retries=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")

        with pytest.raises(Exception, match="Persistent error"):
            test_func()
        assert call_count == 3

    def test_no_retry_on_unauthorized(self):
        """测试 401 错误不重试"""
        call_count = 0

        @retry_with_timeout(max_retries=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("unauthorized: Invalid token")

        with pytest.raises(Exception):
            test_func()
        assert call_count == 1  # 不重试

    def test_no_retry_on_not_found(self):
        """测试 404 错误不重试"""
        call_count = 0

        @retry_with_timeout(max_retries=3, delay=0.1)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("not found: Activity not found")

        with pytest.raises(Exception):
            test_func()
        assert call_count == 1  # 不重试


class TestRetryConfig:
    """测试重试配置"""

    def test_default_retry_count(self):
        """测试默认重试次数"""
        assert MAX_RETRIES == 3

    def test_default_retry_delay(self):
        """测试默认重试延迟"""
        assert RETRY_DELAY == 2


class TestDecoratedFunctions:
    """测试已装饰的函数"""

    def test_authenticate_has_retry(self):
        """测试认证函数有重试装饰器"""
        from scripts.fetch_strava_run import authenticate_strava
        # 函数应该有 __wrapped__ 属性（被装饰器包装）
        assert hasattr(authenticate_strava, '__wrapped__')

    def test_get_latest_run_has_retry(self):
        """测试获取活动函数有重试装饰器"""
        from scripts.fetch_strava_run import get_latest_run
        assert hasattr(get_latest_run, '__wrapped__')

    def test_get_streams_has_retry(self):
        """测试获取 streams 函数有重试装饰器"""
        from scripts.fetch_strava_run import get_activity_streams
        assert hasattr(get_activity_streams, '__wrapped__')

    def test_get_laps_has_retry(self):
        """测试获取 laps 函数有重试装饰器"""
        from scripts.fetch_strava_run import get_activity_laps
        assert hasattr(get_activity_laps, '__wrapped__')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
