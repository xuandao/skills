#!/usr/bin/env python3
"""
Phase 1 Task 6 单元测试
测试端到端流程组件

运行方式:
    python3 -m pytest tests/unit/test_p1_t6_e2e.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import analyze_activity
from scripts.generate_strava_note import generate_note


class MockActivity:
    """模拟 Strava 活动对象"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 12345)
        self.name = kwargs.get('name', 'Test Run')
        self.type = 'Run'
        self.distance = kwargs.get('distance', 5000)  # meters
        self.moving_time = kwargs.get('moving_time', None)
        self.start_date_local = kwargs.get('start_date_local', None)
        self.average_speed = kwargs.get('average_speed', 3.0)  # m/s
        self.max_speed = kwargs.get('max_speed', 4.0)
        self.average_heartrate = kwargs.get('average_heartrate', 150)
        self.max_heartrate = kwargs.get('max_heartrate', 170)
        self.calories = kwargs.get('calories', 300)
        self.total_elevation_gain = kwargs.get('elevation_gain', 0)
        self.average_cadence = kwargs.get('average_cadence', 90)
        self.average_watts = kwargs.get('average_watts', None)
        self.kilojoules = kwargs.get('kilojoules', None)
        self.has_heartrate = kwargs.get('has_heartrate', True)
        self.suffer_score = kwargs.get('suffer_score', None)
        self.map = kwargs.get('map', None)


class MockStream:
    """模拟 Stream 对象"""
    def __init__(self, data):
        self.data = data


class MockLap:
    """模拟 Lap 对象"""
    def __init__(self, **kwargs):
        self.lap_index = kwargs.get('lap_index', 1)
        self.distance = kwargs.get('distance', 1000)
        self.elapsed_time = kwargs.get('elapsed_time', None)
        self.average_speed = kwargs.get('average_speed', 3.0)
        self.average_heartrate = kwargs.get('average_heartrate', 150)
        self.max_heartrate = kwargs.get('max_heartrate', 170)
        self.total_elevation_gain = kwargs.get('elevation_gain', 0)


class TestAnalyzeActivity:
    """测试活动分析"""

    def test_analyze_activity_basic(self):
        """测试基本活动分析"""
        from datetime import datetime

        activity = MockActivity(
            id=12345,
            name='Morning Run',
            distance=5000,
            average_speed=3.0,
            start_date_local=datetime(2026, 3, 25, 8, 0, 0)
        )

        result = analyze_activity(activity, {}, [])

        assert result['activity_id'] == 12345
        assert result['activity_name'] == 'Morning Run'
        assert result['distance_km'] == 5.0
        assert 'avg_pace' in result

    def test_analyze_activity_with_laps(self):
        """测试带计圈的活动分析"""
        from datetime import datetime, timedelta

        activity = MockActivity(
            name='Test Run',
            distance=3000,
            average_speed=3.0,
            start_date_local=datetime(2026, 3, 25, 8, 0, 0)
        )

        laps = [
            MockLap(lap_index=1, distance=1000),
            MockLap(lap_index=2, distance=1000),
            MockLap(lap_index=3, distance=1000),
        ]

        result = analyze_activity(activity, {}, laps)

        assert len(result['splits']) == 3
        assert result['splits'][0]['lap_number'] == 1

    def test_analyze_activity_with_streams(self):
        """测试带 streams 的活动分析"""
        from datetime import datetime

        activity = MockActivity(
            name='Test Run',
            distance=5000,
            start_date_local=datetime(2026, 3, 25, 8, 0, 0)
        )

        streams = {
            'time': MockStream([0, 1, 2]),
            'latlng': MockStream([[31.0, 121.0], [31.1, 121.1], [31.2, 121.2]]),
        }

        result = analyze_activity(activity, streams, [])

        assert 'strava_data' in result
        assert 'streams_available' in result['strava_data']


class TestGenerateNote:
    """测试笔记生成"""

    def test_generate_note_basic(self):
        """测试基本笔记生成"""
        data = {
            'activity_id': 12345,
            'activity_name': 'Test Run',
            'activity_type': 'running',
            'date': '2026-03-25',
            'time': '08:00',
            'distance_km': 5.0,
            'duration': '25:00',
            'duration_seconds': 1500,
            'avg_pace': '5:00',
            'avg_hr': 150,
            'max_hr': 170,
            'calories': 300,
            'elevation_gain': 'N/A',
            'avg_cadence': 90,
            'gpx_path': None,
            'splits': [],
            'strava_data': {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = generate_note(data, tmpdir, training_type='轻松跑')

            assert Path(note_path).exists()

            with open(note_path, 'r') as f:
                content = f.read()

            assert 'Test Run' in content
            assert '2026-03-25' in content
            assert '5.0' in content

    def test_generate_note_with_splits(self):
        """测试带分段的笔记生成"""
        data = {
            'activity_id': 12345,
            'activity_name': 'Test Run',
            'activity_type': 'running',
            'date': '2026-03-25',
            'time': '08:00',
            'distance_km': 3.0,
            'duration': '15:00',
            'duration_seconds': 900,
            'avg_pace': '5:00',
            'avg_hr': 150,
            'max_hr': 170,
            'calories': 200,
            'elevation_gain': 'N/A',
            'avg_cadence': 90,
            'gpx_path': None,
            'splits': [
                {'lap_number': 1, 'distance_km': 1.0, 'duration': '5:00', 'pace': '5:00'},
                {'lap_number': 2, 'distance_km': 1.0, 'duration': '5:00', 'pace': '5:00'},
                {'lap_number': 3, 'distance_km': 1.0, 'duration': '5:00', 'pace': '5:00'},
            ],
            'strava_data': {}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = generate_note(data, tmpdir, training_type='轻松跑')

            with open(note_path, 'r') as f:
                content = f.read()

            # 检查分段表格
            assert '圈数' in content or 'lap' in content.lower()


class TestEndToEnd:
    """测试端到端流程"""

    def test_analyze_and_generate(self):
        """测试分析和生成组合"""
        from datetime import datetime

        # 模拟活动
        activity = MockActivity(
            id=12345,
            name='E2E Test Run',
            distance=5000,
            average_speed=3.0,
            start_date_local=datetime(2026, 3, 25, 8, 0, 0)
        )

        # 分析
        result = analyze_activity(activity, {}, [])

        # 生成笔记
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = generate_note(result, tmpdir)

            # 验证
            assert Path(note_path).exists()

            with open(note_path, 'r') as f:
                content = f.read()

            assert 'E2E Test Run' in content
            assert result['date'] in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
