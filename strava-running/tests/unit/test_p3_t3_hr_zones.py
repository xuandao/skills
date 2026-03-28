#!/usr/bin/env python3
"""
Phase 3 Task 3 单元测试
测试基于心率区间推断训练强度

运行方式:
    python3 -m pytest tests/unit/test_p3_t3_hr_zones.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import analyze_hr_zones, infer_training_type_from_hr


class TestHeartRateZones:
    """测试心率区间计算"""

    def test_zone_1_recovery(self):
        """测试 Zone 1 恢复区间"""
        result = analyze_hr_zones(100, 190)
        assert result is not None
        assert result['zone_num'] == 1
        assert "Zone 1" in result['avg_zone']
        assert result['suggested_type'] == '恢复跑'
        assert result['intensity'] == '低'

    def test_zone_2_easy(self):
        """测试 Zone 2 轻松区间"""
        result = analyze_hr_zones(125, 190)
        assert result is not None
        assert result['zone_num'] == 2
        assert "Zone 2" in result['avg_zone']
        assert result['suggested_type'] == '轻松跑'
        assert result['intensity'] == '低-中'

    def test_zone_3_marathon(self):
        """测试 Zone 3 马拉松配速区间"""
        result = analyze_hr_zones(145, 190)
        assert result is not None
        assert result['zone_num'] == 3
        assert "Zone 3" in result['avg_zone']
        assert result['suggested_type'] == '马拉松配速跑'
        assert result['intensity'] == '中'

    def test_zone_4_threshold(self):
        """测试 Zone 4 乳酸阈值区间"""
        result = analyze_hr_zones(165, 190)
        assert result is not None
        assert result['zone_num'] == 4
        assert "Zone 4" in result['avg_zone']
        assert result['suggested_type'] == '节奏跑'
        assert result['intensity'] == '高'

    def test_zone_5_max(self):
        """测试 Zone 5 极限区间"""
        result = analyze_hr_zones(175, 190)
        assert result is not None
        assert result['zone_num'] == 5
        assert "Zone 5" in result['avg_zone']
        assert result['suggested_type'] == '间歇跑'
        assert result['intensity'] == '极高'


class TestZoneBoundaries:
    """测试心率区间边界"""

    def test_zone_1_boundary(self):
        """测试 Zone 1 边界"""
        # 最大心率 190 时，Zone 2 开始于 114 (190*0.6)
        result = analyze_hr_zones(110, 190)
        assert result['zone_num'] == 1

    def test_zone_2_boundary(self):
        """测试 Zone 2 边界"""
        # Zone 2: 114-133, Zone 3: 133-152
        result = analyze_hr_zones(120, 190)
        assert result['zone_num'] == 2

    def test_zone_3_boundary(self):
        """测试 Zone 3 边界"""
        result = analyze_hr_zones(140, 190)
        assert result['zone_num'] == 3

    def test_zone_4_boundary(self):
        """测试 Zone 4 边界"""
        result = analyze_hr_zones(160, 190)
        assert result['zone_num'] == 4

    def test_zone_5_boundary(self):
        """测试 Zone 5 边界"""
        # Zone 5 开始于 171 (190*0.9)
        result = analyze_hr_zones(175, 190)
        assert result['zone_num'] == 5


class TestHRInference:
    """测试心率推断训练类型"""

    def test_infer_from_zone_1(self):
        """测试从 Zone 1 推断恢复跑"""
        result = infer_training_type_from_hr(100, 190)
        assert result['training_type'] == '恢复跑'
        assert result['zone_info']['zone_num'] == 1

    def test_infer_from_zone_5(self):
        """测试从 Zone 5 推断间歇跑"""
        result = infer_training_type_from_hr(180, 190)
        assert result['training_type'] == '间歇跑'
        assert result['zone_info']['zone_num'] == 5

    def test_infer_with_short_duration_high_hr(self):
        """测试高心率+短时长推断节奏跑(Zone 4)"""
        result = infer_training_type_from_hr(170, 190, duration_min=20)
        assert result['training_type'] == '节奏跑'  # Zone 4
        assert '时长' in result['reason']

    def test_infer_with_long_duration_medium_hr(self):
        """测试中心率+长时长推断 LSD"""
        result = infer_training_type_from_hr(145, 190, duration_min=120)
        assert result['training_type'] == 'LSD'
        assert 'LSD' in result['reason'] or '长时长' in result['reason']

    def test_infer_with_moderate_duration(self):
        """测试中等时长"""
        result = infer_training_type_from_hr(150, 190, duration_min=60)
        # Zone 3 + 60分钟
        assert result['training_type'] == '马拉松配速跑'

    def test_infer_no_duration(self):
        """测试无时长的推断"""
        result = infer_training_type_from_hr(160, 190)
        # Zone 4
        assert result['training_type'] == '节奏跑'
        assert result['confidence'] == 'medium'

    def test_infer_no_hr_data(self):
        """测试无心率数据的情况"""
        result = infer_training_type_from_hr(None, 190)
        assert result['training_type'] == '轻松跑'
        assert result['zone_info'] is None
        assert result['confidence'] == 'low'

    def test_infer_invalid_hr(self):
        """测试无效心率数据"""
        result = infer_training_type_from_hr('N/A', 190)
        assert result['training_type'] == '轻松跑'
        assert result['zone_info'] is None


class TestConfidenceLevels:
    """测试置信度级别"""

    def test_high_confidence_interval(self):
        """测试高置信度判断"""
        # 高心率+短时长是高置信度的间歇跑
        result = infer_training_type_from_hr(170, 190, duration_min=25)
        assert result['confidence'] == 'high'

    def test_medium_confidence_normal(self):
        """测试中置信度判断"""
        result = infer_training_type_from_hr(145, 190)
        assert result['confidence'] == 'medium'

    def test_low_confidence_no_hr(self):
        """测试低置信度判断（无心率）"""
        result = infer_training_type_from_hr(None, 190)
        assert result['confidence'] == 'low'


class TestReasonField:
    """测试原因字段"""

    def test_zone_in_reason(self):
        """测试原因中包含区间信息"""
        result = infer_training_type_from_hr(150, 190)
        assert 'Z3' in result['reason'] or '心率区间' in result['reason'] or 'Zone' in result['reason']

    def test_duration_in_reason(self):
        """测试原因中包含时长信息"""
        result = infer_training_type_from_hr(150, 190, duration_min=120)
        assert '分钟' in result['reason'] or '时长' in result['reason']

    def test_intensity_in_reason(self):
        """测试原因中包含强度信息"""
        result = infer_training_type_from_hr(170, 190)
        assert '高' in result['reason'] or '极高' in result['reason']


class TestZonesBreakdown:
    """测试区间边界输出"""

    def test_zones_breakdown_format(self):
        """测试区间边界格式"""
        result = analyze_hr_zones(150, 190)
        assert 'zones_breakdown' in result
        breakdown = result['zones_breakdown']
        assert 'Z1' in breakdown
        assert 'Z5' in breakdown

    def test_calculated_boundaries(self):
        """测试计算的边界值"""
        result = analyze_hr_zones(150, 190)
        # 最大心率 190 时，边界应该是：
        # Z1: >95, Z2: >114, Z3: >133, Z4: >152, Z5: >171
        breakdown = result['zones_breakdown']
        assert 'Z1(>95)' in breakdown
        assert 'Z2(>114)' in breakdown


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
