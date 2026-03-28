#!/usr/bin/env python3
"""
Phase 3 Task 2 单元测试
测试活动名称智能推断

运行方式:
    python3 -m pytest tests/unit/test_p3_t2_name_inference.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import analyze_activity_name


class TestKeywordMatching:
    """测试关键词匹配"""

    def test_interval_by_keyword(self):
        """测试间歇跑关键词"""
        result = analyze_activity_name("Morning Interval Run")
        assert result['training_type'] == '间歇跑'
        assert result['confidence'] == 'high'

    def test_tempo_by_keyword(self):
        """测试节奏跑关键词"""
        result = analyze_activity_name("Tempo Tuesday")
        assert result['training_type'] == '节奏跑'
        assert result['confidence'] == 'high'

    def test_lsd_by_keyword(self):
        """测试 LSD 关键词"""
        result = analyze_activity_name("Sunday LSD")
        assert result['training_type'] == 'LSD'
        assert result['confidence'] == 'high'

    def test_easy_by_keyword(self):
        """测试轻松跑关键词"""
        result = analyze_activity_name("Easy Recovery Run")
        assert result['training_type'] == '轻松跑'
        assert result['confidence'] == 'high'

    def test_treadmill_by_keyword(self):
        """测试跑步机关键词"""
        result = analyze_activity_name("Treadmill Session")
        assert result['training_type'] == '跑步机'
        assert result['confidence'] == 'high'

    def test_marathon_by_keyword(self):
        """测试马拉松配速跑关键词"""
        result = analyze_activity_name("Marathon Pace Practice")
        assert result['training_type'] == '马拉松配速跑'
        assert result['confidence'] == 'high'


class TestChineseKeywords:
    """测试中文关键词"""

    def test_chinese_interval(self):
        """测试中文间歇跑"""
        result = analyze_activity_name("间歇训练")
        assert result['training_type'] == '间歇跑'

    def test_chinese_tempo(self):
        """测试中文节奏跑"""
        result = analyze_activity_name("节奏跑")
        assert result['training_type'] == '节奏跑'

    def test_chinese_lsd(self):
        """测试中文长距离"""
        result = analyze_activity_name("周末长距离")
        assert result['training_type'] == 'LSD'

    def test_chinese_marathon(self):
        """测试中文马拉松"""
        result = analyze_activity_name("无锡马拉松")
        assert result['training_type'] == '马拉松配速跑'


class TestHeuristicInference:
    """测试启发式推断"""

    def test_lsd_by_distance(self):
        """测试基于距离推断 LSD"""
        result = analyze_activity_name("周日常规训练", distance_km=21.0, duration_min=120)
        assert result['training_type'] == 'LSD'
        assert result['confidence'] == 'medium'
        assert '21.0km' in result['reason'] or '120分钟' in result['reason']

    def test_lsd_by_duration(self):
        """测试基于时长推断 LSD"""
        result = analyze_activity_name("周末跑步", distance_km=16.0, duration_min=90)
        assert result['training_type'] == 'LSD'
        assert result['confidence'] == 'medium'

    def test_easy_by_short_distance(self):
        """测试基于短距离推断轻松跑"""
        result = analyze_activity_name("傍晚跑步", distance_km=3.0, duration_min=20)
        assert result['training_type'] == '轻松跑'
        assert result['confidence'] == 'low'

    def test_easy_by_slow_pace(self):
        """测试基于慢配速推断轻松跑"""
        result = analyze_activity_name("短距离跑步", distance_km=4.0, duration_min=25)
        assert result['training_type'] == '轻松跑'
        # 配速 = 25/4 = 6.25 min/km >= 6.0
        assert '6.' in result['reason'] or '配速' in result['reason'] or '距离' in result['reason']


class TestDefaultBehavior:
    """测试默认行为"""

    def test_default_easy_run(self):
        """测试无特征时默认轻松跑"""
        result = analyze_activity_name("Just Run")
        assert result['training_type'] == '轻松跑'
        assert result['confidence'] == 'low'
        assert '默认' in result['reason']

    def test_default_with_data(self):
        """测试有数据但无关键词"""
        result = analyze_activity_name("Running", distance_km=10.0, duration_min=50)
        assert result['training_type'] == '轻松跑'
        # 配速 = 5 min/km，不触发 LSD 也不触发慢配速


class TestConfidenceLevels:
    """测试置信度级别"""

    def test_high_confidence_for_keyword(self):
        """测试关键词匹配返回高置信度"""
        result = analyze_activity_name("Interval Training")
        assert result['confidence'] == 'high'

    def test_medium_confidence_for_heuristic(self):
        """测试启发式推断返回中置信度"""
        result = analyze_activity_name("Run", distance_km=20.0, duration_min=100)
        assert result['confidence'] == 'medium'

    def test_low_confidence_for_default(self):
        """测试默认返回低置信度"""
        result = analyze_activity_name("Unknown Run")
        assert result['confidence'] == 'low'


class TestReasonField:
    """测试原因字段"""

    def test_keyword_reason(self):
        """测试关键词原因"""
        result = analyze_activity_name("Tempo Run")
        assert '关键词' in result['reason']

    def test_distance_reason(self):
        """测试距离原因"""
        result = analyze_activity_name("Run", distance_km=21.0, duration_min=120)
        assert 'km' in result['reason'] or '距离' in result['reason']

    def test_pace_reason(self):
        """测试配速原因"""
        result = analyze_activity_name("Run", distance_km=3.0, duration_min=20)
        assert 'min/km' in result['reason'] or '配速' in result['reason'] or '距离' in result['reason']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
