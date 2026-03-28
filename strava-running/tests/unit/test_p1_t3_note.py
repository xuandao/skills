#!/usr/bin/env python3
"""
Phase 1 Task 3 单元测试
测试笔记生成功能

运行方式:
    python3 -m pytest tests/unit/test_p1_t3_note.py -v
"""

import pytest
import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import (
    get_training_type,
    parse_pace,
    format_pace_from_seconds,
    format_pace_diff,
    analyze_hr_zones,
    TRAINING_TYPES,
)


class TestGetTrainingType:
    """测试训练类型识别"""

    def test_detect_from_user_input(self):
        """测试从用户输入识别"""
        assert get_training_type("Run", "跑了个间歇") == "间歇跑"
        assert get_training_type("Run", "今天节奏跑") == "节奏跑"
        assert get_training_type("Run", "LSD长距离") == "LSD"
        assert get_training_type("Run", "跑步机训练") == "跑步机"

    def test_detect_from_activity_name(self):
        """测试从活动名称识别"""
        assert get_training_type("Morning Interval", None) == "间歇跑"
        assert get_training_type("Tempo Run", None) == "节奏跑"
        assert get_training_type("LSD Long Run", None) == "LSD"
        assert get_training_type("Easy Run", None) == "轻松跑"
        assert get_training_type("Recovery Run", None) == "恢复跑"
        assert get_training_type("Treadmill Run", None) == "跑步机"
        assert get_training_type("Marathon Pace", None) == "马拉松配速跑"

    def test_default_type(self):
        """测试默认类型"""
        assert get_training_type("Random Name", None) == "轻松跑"
        assert get_training_type("Morning Run", None) == "轻松跑"

    def test_user_input_priority(self):
        """测试用户输入优先级高于活动名称"""
        assert get_training_type("Easy Run", "节奏跑训练") == "节奏跑"


class TestParsePace:
    """测试配速解析"""

    def test_parse_normal_pace(self):
        """测试正常配速"""
        assert parse_pace("4:59") == 299  # 4*60 + 59
        assert parse_pace("5:30") == 330  # 5*60 + 30
        assert parse_pace("3:45") == 225  # 3*60 + 45

    def test_parse_invalid_pace(self):
        """测试无效配速"""
        assert parse_pace("N/A") is None
        assert parse_pace("") is None
        assert parse_pace(None) is None
        assert parse_pace("invalid") is None


class TestFormatPaceFromSeconds:
    """测试配速格式化"""

    def test_format_normal(self):
        """测试正常格式化"""
        assert format_pace_from_seconds(299) == "4:59"
        assert format_pace_from_seconds(330) == "5:30"
        assert format_pace_from_seconds(225) == "3:45"

    def test_format_zero(self):
        """测试零值"""
        assert format_pace_from_seconds(0) == "N/A"
        assert format_pace_from_seconds(None) == "N/A"


class TestFormatPaceDiff:
    """测试配速差异格式化"""

    def test_faster_pace(self):
        """测试更快的配速"""
        result = format_pace_diff(300, 330)  # 5:00 vs 5:30
        assert result == "-30秒/km"

    def test_slower_pace(self):
        """测试更慢的配速"""
        result = format_pace_diff(330, 300)  # 5:30 vs 5:00
        assert result == "+30秒/km"

    def test_same_pace(self):
        """测试相同配速"""
        result = format_pace_diff(300, 300)
        assert result == "持平"

    def test_invalid_pace(self):
        """测试无效配速"""
        assert format_pace_diff(None, 300) is None
        assert format_pace_diff(300, None) is None


class TestAnalyzeHrZones:
    """测试心率区间分析"""

    def test_zone1_recovery(self):
        """测试Zone 1恢复区间"""
        result = analyze_hr_zones(100, 190)
        assert result is not None
        assert "Zone 1" in result['avg_zone']

    def test_zone2_easy(self):
        """测试Zone 2轻松区间"""
        result = analyze_hr_zones(125, 190)
        assert result is not None
        assert "Zone 2" in result['avg_zone']

    def test_zone3_marathon(self):
        """测试Zone 3马拉松配速区间"""
        result = analyze_hr_zones(145, 190)
        assert result is not None
        assert "Zone 3" in result['avg_zone']

    def test_zone4_threshold(self):
        """测试Zone 4乳酸阈值区间"""
        result = analyze_hr_zones(165, 190)
        assert result is not None
        assert "Zone 4" in result['avg_zone']

    def test_zone5_max(self):
        """测试Zone 5极限区间"""
        result = analyze_hr_zones(175, 190)
        assert result is not None
        assert "Zone 5" in result['avg_zone']

    def test_invalid_hr(self):
        """测试无效心率"""
        result = analyze_hr_zones("N/A", 190)
        assert result is None
        result = analyze_hr_zones(None, 190)
        assert result is None


class TestTrainingTypes:
    """测试训练类型配置"""

    def test_all_types_have_required_fields(self):
        """测试所有类型都有必需字段"""
        for type_name, type_info in TRAINING_TYPES.items():
            assert 'emoji' in type_info
            assert 'folder' in type_info
            assert 'description' in type_info
            assert 'key_metrics' in type_info

    def test_training_types_count(self):
        """测试训练类型数量"""
        assert len(TRAINING_TYPES) == 7
        expected_types = ['间歇跑', '节奏跑', '轻松跑', 'LSD', '马拉松配速跑', '恢复跑', '跑步机']
        for type_name in expected_types:
            assert type_name in TRAINING_TYPES


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
