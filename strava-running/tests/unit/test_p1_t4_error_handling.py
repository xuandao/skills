#!/usr/bin/env python3
"""
Phase 1 Task 4 单元测试
测试 API 错误处理

运行方式:
    python3 -m pytest tests/unit/test_p1_t4_error_handling.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import (
    authenticate_strava,
    get_latest_run,
    get_activity_streams,
    get_activity_laps,
)


class TestAuthenticateErrorHandling:
    """测试认证错误处理"""

    def test_401_unauthorized(self):
        """测试 401 未授权错误"""
        from stravalib.exc import AccessUnauthorized

        mock_client = Mock()
        mock_client.refresh_access_token.side_effect = AccessUnauthorized("Invalid token")

        config = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'refresh_token': 'invalid_token'
        }

        with patch('scripts.fetch_strava_run.Client', return_value=mock_client):
            with pytest.raises(SystemExit) as exc_info:
                authenticate_strava(config)
            assert exc_info.value.code == 1

    def test_network_error_during_auth(self):
        """测试认证时网络错误"""
        mock_client = Mock()
        mock_client.refresh_access_token.side_effect = Exception("Connection timeout")

        config = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'refresh_token': 'test_token'
        }

        with patch('scripts.fetch_strava_run.Client', return_value=mock_client):
            with pytest.raises(SystemExit) as exc_info:
                authenticate_strava(config)
            assert exc_info.value.code == 1


class TestGetLatestRunErrorHandling:
    """测试获取活动错误处理"""

    def test_404_not_found(self):
        """测试 404 活动不存在"""
        from stravalib.exc import ObjectNotFound

        mock_client = Mock()
        mock_client.get_activities.side_effect = ObjectNotFound("Activity not found")

        with pytest.raises(SystemExit) as exc_info:
            get_latest_run(mock_client)
        assert exc_info.value.code == 1

    def test_rate_limit_error(self):
        """测试 429 限流错误"""
        mock_client = Mock()
        mock_client.get_activities.side_effect = Exception("Rate limit exceeded")

        with pytest.raises(SystemExit) as exc_info:
            get_latest_run(mock_client)
        assert exc_info.value.code == 1

    def test_network_error(self):
        """测试网络错误"""
        mock_client = Mock()
        mock_client.get_activities.side_effect = Exception("Network error")

        with pytest.raises(SystemExit) as exc_info:
            get_latest_run(mock_client)
        assert exc_info.value.code == 1


class TestGetActivityStreamsErrorHandling:
    """测试获取 streams 错误处理"""

    def test_object_not_found(self):
        """测试活动不存在时返回空字典"""
        from stravalib.exc import ObjectNotFound

        mock_client = Mock()
        mock_client.get_activity_streams.side_effect = ObjectNotFound("Activity not found")

        result = get_activity_streams(mock_client, 12345)
        assert result == {}

    def test_rate_limit(self):
        """测试限流错误时返回空字典"""
        mock_client = Mock()
        mock_client.get_activity_streams.side_effect = Exception("Rate limit")

        result = get_activity_streams(mock_client, 12345)
        assert result == {}

    def test_network_error(self):
        """测试网络错误时返回空字典"""
        mock_client = Mock()
        mock_client.get_activity_streams.side_effect = Exception("Network error")

        result = get_activity_streams(mock_client, 12345)
        assert result == {}


class TestGetActivityLapsErrorHandling:
    """测试获取 laps 错误处理"""

    def test_object_not_found(self):
        """测试活动不存在时返回空列表"""
        from stravalib.exc import ObjectNotFound

        mock_client = Mock()
        mock_client.get_activity_laps.side_effect = ObjectNotFound("Activity not found")

        result = get_activity_laps(mock_client, 12345)
        assert result == []

    def test_rate_limit(self):
        """测试限流错误时返回空列表"""
        mock_client = Mock()
        mock_client.get_activity_laps.side_effect = Exception("Rate limit")

        result = get_activity_laps(mock_client, 12345)
        assert result == []

    def test_network_error(self):
        """测试网络错误时返回空列表"""
        mock_client = Mock()
        mock_client.get_activity_laps.side_effect = Exception("Network error")

        result = get_activity_laps(mock_client, 12345)
        assert result == []


class TestErrorMessages:
    """测试错误消息"""

    def test_error_output_to_stderr(self):
        """测试错误消息输出到 stderr"""
        import io

        mock_client = Mock()
        mock_client.get_activities.side_effect = Exception("Test error")

        stderr_capture = io.StringIO()
        with patch('sys.stderr', stderr_capture):
            with pytest.raises(SystemExit):
                get_latest_run(mock_client)

        stderr_output = stderr_capture.getvalue()
        assert "Test error" in stderr_output


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
