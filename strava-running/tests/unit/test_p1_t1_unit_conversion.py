#!/usr/bin/env python3
"""
Phase 1 Task 1 单元测试
测试单位转换相关函数

运行方式:
    python3 -m pytest tests/unit/test_p1_t1_unit_conversion.py -v
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fetch_strava_run import parse_quantity, format_pace


# 模拟带单位的量值类（stravalib 返回的类型）
class MockQuantity:
    """模拟带单位的量值"""
    def __init__(self, magnitude):
        self.magnitude = magnitude


# ==================== 测试用例 ====================

class TestParseSpeed:
    """测试速度解析"""

    def test_parse_speed_with_quantity(self):
        """测试带单位的量值"""
        speed = parse_quantity(MockQuantity(3.34))
        assert speed == 3.34

    def test_parse_speed_with_float(self):
        """测试纯浮点数值"""
        speed = parse_quantity(3.34)
        assert speed == 3.34

    def test_parse_speed_with_int(self):
        """测试整数"""
        speed = parse_quantity(5)
        assert speed == 5.0

    def test_parse_speed_with_none(self):
        """测试空值"""
        speed = parse_quantity(None)
        assert speed == 0.0


class TestParseDistance:
    """测试距离解析"""

    def test_parse_distance_with_quantity(self):
        """测试带单位的量值"""
        distance = parse_quantity(MockQuantity(6730.0))
        assert distance == 6730.0

    def test_parse_distance_with_float(self):
        """测试纯浮点数值"""
        distance = parse_quantity(6730.0)
        assert distance == 6730.0

    def test_parse_distance_with_none(self):
        """测试空值"""
        distance = parse_quantity(None)
        assert distance == 0.0


class TestFormatPace:
    """测试配速格式化"""

    def test_format_pace_normal(self):
        """测试正常配速"""
        # 3.34 m/s ≈ 4:59/km
        pace = format_pace(3.34)
        assert pace == "4:59"

    def test_format_pace_slow(self):
        """测试慢配速"""
        # 2.5 m/s = 6:40/km
        pace = format_pace(2.5)
        assert pace == "6:40"

    def test_format_pace_fast(self):
        """测试快配速"""
        # 5.0 m/s = 3:20/km
        pace = format_pace(5.0)
        assert pace == "3:20"

    def test_format_pace_zero(self):
        """测试零速度"""
        pace = format_pace(0)
        assert pace == "N/A"

    def test_format_pace_negative(self):
        """测试负速度"""
        pace = format_pace(-1)
        assert pace == "N/A"

    def test_format_pace_none(self):
        """测试空值"""
        pace = format_pace(None)
        assert pace == "N/A"


if __name__ == '__main__':
    # 可以直接运行此文件查看测试结果
    pytest.main([__file__, '-v'])
