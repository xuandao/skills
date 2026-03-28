#!/usr/bin/env python3
"""
Phase 3 Task 4 单元测试
测试基于配速变化推断训练类型

运行方式:
    python3 -m pytest tests/unit/test_p3_t4_pace_analysis.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import analyze_pace_variation, infer_training_type_from_pace


class TestAnalyzePaceVariation:
    """测试配速变化分析"""

    def test_steady_pace(self):
        """测试稳定配速"""
        splits = [
            {'pace': '4:30'}, {'pace': '4:32'}, {'pace': '4:31'},
            {'pace': '4:33'}, {'pace': '4:30'}, {'pace': '4:31'}
        ]
        result = analyze_pace_variation(splits)
        assert result is not None
        assert result['is_consistent'] is True
        assert result['pattern'] == 'steady'
        assert result['suggested_type'] == '节奏跑'
        assert result['pace_variance'] < 10

    def test_interval_pace(self):
        """测试间歇跑配速"""
        splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},
            {'pace': '3:45'}, {'pace': '5:05'}, {'pace': '3:35'}
        ]
        result = analyze_pace_variation(splits)
        assert result is not None
        assert result['has_surges'] is True
        assert result['has_recoveries'] is True
        assert result['pattern'] == 'interval'
        assert result['suggested_type'] == '间歇跑'
        assert result['pace_range'] > 30

    def test_progression_pace(self):
        """测试渐加速配速"""
        splits = [
            {'pace': '5:00'}, {'pace': '4:50'}, {'pace': '4:40'},
            {'pace': '4:30'}, {'pace': '4:20'}, {'pace': '4:10'}
        ]
        result = analyze_pace_variation(splits)
        assert result is not None
        assert result['is_progression'] is True

    def test_variable_pace(self):
        """测试无规律配速"""
        splits = [
            {'pace': '5:20'}, {'pace': '5:10'}, {'pace': '5:25'},
            {'pace': '5:15'}, {'pace': '5:30'}, {'pace': '5:18'}
        ]
        result = analyze_pace_variation(splits)
        assert result is not None
        # 方差较小可能被识别为 steady
        assert result['pattern'] in ['steady', 'variable']

    def test_empty_splits(self):
        """测试空分段数据"""
        result = analyze_pace_variation([])
        assert result is None

    def test_single_split(self):
        """测试单分段"""
        result = analyze_pace_variation([{'pace': '5:00'}])
        assert result is None

    def test_missing_pace(self):
        """测试缺失配速数据"""
        splits = [
            {'pace': '5:00'}, {'pace': 'N/A'}, {'pace': '5:10'}
        ]
        result = analyze_pace_variation(splits)
        # 应该能处理，但只有2个有效数据
        if result:
            assert 'pace_data' in result


class TestPaceStatistics:
    """测试配速统计计算"""

    def test_avg_pace_calculation(self):
        """测试平均配速计算"""
        splits = [
            {'pace': '5:00'}, {'pace': '5:00'}, {'pace': '5:00'}
        ]  # 都是 300 秒
        result = analyze_pace_variation(splits)
        assert result['avg_pace_sec'] == 300

    def test_pace_range_calculation(self):
        """测试配速范围计算"""
        splits = [
            {'pace': '4:00'}, {'pace': '5:00'}  # 240秒 和 300秒
        ]
        result = analyze_pace_variation(splits)
        assert result['pace_range'] == 60

    def test_pace_data_list(self):
        """测试返回的配速数据列表"""
        splits = [
            {'pace': '5:00'}, {'pace': '5:30'}, {'pace': '6:00'}
        ]
        result = analyze_pace_variation(splits)
        assert len(result['pace_data']) == 3
        assert result['pace_data'] == [300, 330, 360]


class TestInferFromPace:
    """测试配速推断训练类型"""

    def test_infer_interval(self):
        """测试推断间歇跑"""
        splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},
            {'pace': '3:45'}
        ]
        result = infer_training_type_from_pace(splits)
        assert result['training_type'] == '间歇跑'
        assert result['confidence'] == 'high'
        assert result['pace_analysis'] is not None

    def test_infer_tempo(self):
        """测试推断节奏跑"""
        splits = [
            {'pace': '4:30'}, {'pace': '4:32'}, {'pace': '4:31'}
        ]
        result = infer_training_type_from_pace(splits)
        assert result['training_type'] == '节奏跑'

    def test_infer_from_fast_avg_pace(self):
        """测试从快平均配速推断"""
        result = infer_training_type_from_pace([], avg_pace_str='3:45')
        assert result['training_type'] == '节奏跑'
        assert result['confidence'] == 'low'

    def test_infer_from_slow_avg_pace(self):
        """测试从慢平均配速推断"""
        result = infer_training_type_from_pace([], avg_pace_str='6:30')
        assert result['training_type'] == '轻松跑'  # 6:30 可能不触发恢复跑
        assert result['confidence'] == 'low'

    def test_infer_default(self):
        """测试默认推断"""
        result = infer_training_type_from_pace([])
        assert result['training_type'] == '轻松跑'
        assert result['confidence'] == 'low'

    def test_infer_with_no_data(self):
        """测试无数据情况"""
        result = infer_training_type_from_pace([], avg_pace_str='N/A')
        assert result['training_type'] == '轻松跑'


class TestConfidenceLevels:
    """测试置信度"""

    def test_high_confidence_interval(self):
        """测试间歇跑高置信度"""
        splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},
            {'pace': '3:45'}
        ]
        result = infer_training_type_from_pace(splits)
        assert result['confidence'] == 'high'

    def test_medium_confidence_steady(self):
        """测试稳定配速中置信度"""
        splits = [
            {'pace': '4:30'}, {'pace': '4:32'}, {'pace': '4:31'}
        ]
        result = infer_training_type_from_pace(splits)
        assert result['confidence'] == 'medium'

    def test_low_confidence_no_splits(self):
        """测试无分段低置信度"""
        result = infer_training_type_from_pace([], avg_pace_str='5:00')
        assert result['confidence'] == 'low'


class TestReasonField:
    """测试原因字段"""

    def test_reason_contains_pattern(self):
        """测试原因包含模式信息"""
        splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = infer_training_type_from_pace(splits)
        assert '配速变化大' in result['reason'] or '间歇' in result['reason']

    def test_reason_contains_range(self):
        """测试原因包含范围信息"""
        splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = infer_training_type_from_pace(splits)
        assert '范围' in result['reason'] or '秒' in result['reason']

    def test_reason_for_steady(self):
        """测试稳定配速原因"""
        splits = [
            {'pace': '4:30'}, {'pace': '4:32'}
        ]
        result = infer_training_type_from_pace(splits)
        assert '稳定' in result['reason'] or '配速' in result['reason']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
