#!/usr/bin/env python3
"""
Phase 1 Task 2 单元测试
测试获取最新活动功能

运行方式:
    python3 -m pytest tests/unit/test_p1_t2_fetch.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import (
    get_latest_run,
    get_activity_streams,
    get_activity_laps,
    format_duration,
    format_pace,
)


class MockActivity:
    """模拟 Strava 活动对象"""
    def __init__(self, id, name, type, distance, moving_time):
        self.id = id
        self.name = name
        self.type = type
        self.distance = distance
        self.moving_time = moving_time


class TestGetLatestRun:
    """测试获取最新跑步活动"""

    def test_get_latest_run_filters_running(self):
        """测试只返回跑步活动"""
        mock_client = Mock()

        # 模拟返回混合类型活动
        run_activity = MockActivity(1, "Morning Run", "Run", 5000, None)
        ride_activity = MockActivity(2, "Evening Ride", "Ride", 20000, None)
        run_activity2 = MockActivity(3, "Lunch Run", "Run", 8000, None)

        mock_client.get_activities.return_value = [run_activity, ride_activity, run_activity2]
        mock_client.get_activity.return_value = run_activity

        result = get_latest_run(mock_client)

        # 应该返回第一个跑步活动
        assert result.id == 1
        assert result.type == "Run"

    def test_get_latest_run_no_activities(self):
        """测试无活动时的处理"""
        mock_client = Mock()
        mock_client.get_activities.return_value = []

        with pytest.raises(SystemExit):
            get_latest_run(mock_client)

    def test_get_latest_run_no_running(self):
        """测试无跑步活动时的处理"""
        mock_client = Mock()
        ride_activity = MockActivity(1, "Ride", "Ride", 20000, None)
        mock_client.get_activities.return_value = [ride_activity]

        with pytest.raises(SystemExit):
            get_latest_run(mock_client)


class TestGetActivityStreams:
    """测试获取活动 streams"""

    def test_get_streams_success(self):
        """测试成功获取 streams"""
        mock_client = Mock()
        mock_streams = {
            'time': Mock(data=[0, 1, 2]),
            'latlng': Mock(data=[[31.0, 121.0], [31.1, 121.1]]),
        }
        mock_client.get_activity_streams.return_value = mock_streams

        result = get_activity_streams(mock_client, 12345)

        assert 'time' in result
        assert 'latlng' in result

    def test_get_streams_failure(self):
        """测试获取 streams 失败时的处理"""
        mock_client = Mock()
        mock_client.get_activity_streams.side_effect = Exception("API Error")

        result = get_activity_streams(mock_client, 12345)

        # 应该返回空字典而不是抛出异常
        assert result == {}


class TestGetActivityLaps:
    """测试获取活动 laps"""

    def test_get_laps_success(self):
        """测试成功获取 laps"""
        mock_client = Mock()
        mock_laps = [
            Mock(lap_index=1, distance=1000),
            Mock(lap_index=2, distance=1000),
        ]
        mock_client.get_activity_laps.return_value = mock_laps

        result = get_activity_laps(mock_client, 12345)

        assert len(result) == 2
        assert result[0].lap_index == 1

    def test_get_laps_failure(self):
        """测试获取 laps 失败时的处理"""
        mock_client = Mock()
        mock_client.get_activity_laps.side_effect = Exception("API Error")

        result = get_activity_laps(mock_client, 12345)

        # 应该返回空列表而不是抛出异常
        assert result == []


class TestFormatDuration:
    """测试时间格式化"""

    def test_format_duration_with_hours(self):
        """测试带小时的时间"""
        from datetime import timedelta
        duration = timedelta(hours=1, minutes=30, seconds=45)
        result = format_duration(duration)
        assert result == "1:30:45"

    def test_format_duration_without_hours(self):
        """测试不带小时的时间"""
        from datetime import timedelta
        duration = timedelta(minutes=33, seconds=34)
        result = format_duration(duration)
        assert result == "33:34"

    def test_format_duration_zero(self):
        """测试零时间 - 实际实现返回 N/A"""
        from datetime import timedelta
        duration = timedelta()
        result = format_duration(duration)
        # 零时间被视为无效，返回 N/A
        assert result == "N/A"

    def test_format_duration_none(self):
        """测试 None"""
        result = format_duration(None)
        assert result == "N/A"


class TestFormatPace:
    """测试配速格式化"""

    def test_format_pace_normal(self):
        """测试正常配速"""
        # 3.34 m/s ≈ 4:59/km
        result = format_pace(3.34)
        assert result == "4:59"

    def test_format_pace_slow(self):
        """测试慢配速"""
        # 2.5 m/s = 6:40/km
        result = format_pace(2.5)
        assert result == "6:40"

    def test_format_pace_zero(self):
        """测试零速度"""
        result = format_pace(0)
        assert result == "N/A"

    def test_format_pace_none(self):
        """测试 None"""
        result = format_pace(None)
        assert result == "N/A"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
