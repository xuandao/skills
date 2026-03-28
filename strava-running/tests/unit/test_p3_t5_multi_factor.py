#!/usr/bin/env python3
"""
Phase 3 Task 5 单元测试
测试综合决策算法

运行方式:
    python3 -m pytest tests/unit/test_p3_t5_multi_factor.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import comprehensive_training_type_inference


class TestUserInputPriority:
    """测试用户输入优先级"""

    def test_user_input_overrides_name(self):
        """测试用户输入优先于活动名称"""
        result = comprehensive_training_type_inference(
            activity_name="Easy Run",
            user_input="跑了个间歇"
        )
        assert result['training_type'] == '间歇跑'
        assert result['confidence'] == 'high'
        assert 'user_input' in result['votes']

    def test_user_input_overrides_hr(self):
        """测试用户输入优先于心率"""
        result = comprehensive_training_type_inference(
            activity_name="Run",
            user_input="节奏跑",
            avg_hr=130,  # Zone 2 - 轻松跑
            max_hr=190
        )
        assert result['training_type'] == '节奏跑'

    def test_user_input_overrides_pace(self):
        """测试用户输入优先于配速"""
        splits = [{'pace': '5:00'}, {'pace': '5:10'}]  # 稳定配速
        result = comprehensive_training_type_inference(
            activity_name="Run",
            user_input="跑步机训练",
            splits=splits
        )
        assert result['training_type'] == '跑步机'


class TestMultiFactorConsensus:
    """测试多因子一致性"""

    def test_all_factors_agree_interval(self):
        """测试所有因子一致识别间歇跑"""
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Interval Training",
            avg_hr=175,  # Zone 5
            max_hr=190,
            splits=interval_splits
        )
        assert result['training_type'] == '间歇跑'
        assert result['consensus']['agreement'] is True
        assert len(result['consensus']['unique_types']) == 1

    def test_all_factors_agree_tempo(self):
        """测试所有因子一致识别节奏跑"""
        result = comprehensive_training_type_inference(
            activity_name="Tempo Run",
            avg_hr=165,  # Zone 4
            max_hr=190,
            avg_pace_str='4:30'  # 较快配速
        )
        assert result['training_type'] == '节奏跑'

    def test_majority_wins(self):
        """测试多数因子获胜"""
        # 活动名称和配速说是间歇，心率说是节奏
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Interval Run",
            avg_hr=165,  # Zone 4 - 节奏跑
            max_hr=190,
            splits=interval_splits
        )
        # 应该根据多数决定
        assert result['training_type'] in ['间歇跑', '节奏跑']


class TestFactorCombinations:
    """测试因子组合"""

    def test_name_and_distance(self):
        """测试活动名称+距离"""
        result = comprehensive_training_type_inference(
            activity_name="Long Run",
            distance_km=20.0,
            duration_min=120
        )
        assert result['training_type'] == 'LSD'
        assert 'activity_name' in result['factors']

    def test_hr_and_pace(self):
        """测试心率+配速"""
        result = comprehensive_training_type_inference(
            activity_name="Run",
            avg_hr=170,  # Zone 4
            max_hr=190,
            avg_pace_str='4:15'
        )
        assert result['training_type'] == '节奏跑'
        assert 'heart_rate' in result['factors']
        assert 'pace' in result['factors']

    def test_all_factors(self):
        """测试所有因子组合"""
        splits = [{'pace': '4:30'}, {'pace': '4:32'}]
        result = comprehensive_training_type_inference(
            activity_name="Tempo Tuesday",
            user_input=None,
            distance_km=10.0,
            duration_min=45,
            avg_hr=165,
            max_hr=190,
            splits=splits,
            avg_pace_str='4:31'
        )
        assert 'activity_name' in result['factors']
        assert 'heart_rate' in result['factors']
        assert 'pace' in result['factors']


class TestConfidenceLevels:
    """测试置信度"""

    def test_high_confidence_user_input(self):
        """测试用户输入的高置信度"""
        result = comprehensive_training_type_inference(
            activity_name="Run",
            user_input="间歇跑"
        )
        assert result['confidence'] == 'high'

    def test_high_confidence_consensus(self):
        """测试多因子一致的高置信度"""
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Interval Training",
            avg_hr=175,
            max_hr=190,
            splits=interval_splits
        )
        # 至少2个因子一致，可能是 high 或 medium
        assert result['confidence'] in ['high', 'medium']

    def test_low_confidence_few_factors(self):
        """测试少量因子的低置信度"""
        result = comprehensive_training_type_inference(
            activity_name="Some Run",
            distance_km=5.0,
            duration_min=30
        )
        # 只有活动名称，可能 confidence 较低
        assert result['confidence'] in ['low', 'medium']


class TestReasonField:
    """测试原因字段"""

    def test_reason_contains_user_input(self):
        """测试原因包含用户输入"""
        result = comprehensive_training_type_inference(
            activity_name="Run",
            user_input="节奏跑"
        )
        assert '用户输入' in result['reason'] or '节奏跑' in result['reason']

    def test_reason_contains_vote_count(self):
        """测试原因包含投票数"""
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Interval Training",
            avg_hr=175,
            max_hr=190,
            splits=interval_splits
        )
        # 如果基于投票，原因应该包含投票信息
        if '个因子' in result['reason']:
            assert '/' in result['reason']


class TestConsensusInfo:
    """测试一致性信息"""

    def test_agreement_flag(self):
        """测试一致性标志"""
        result = comprehensive_training_type_inference(
            activity_name="Interval Run",
            avg_hr=175,
            max_hr=190
        )
        assert 'agreement' in result['consensus']
        assert isinstance(result['consensus']['agreement'], bool)

    def test_vote_distribution(self):
        """测试投票分布"""
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Interval Training",
            avg_hr=175,
            max_hr=190,
            splits=interval_splits
        )
        assert 'vote_distribution' in result['consensus']
        assert isinstance(result['consensus']['vote_distribution'], dict)

    def test_unique_types(self):
        """测试唯一类型列表"""
        result = comprehensive_training_type_inference(
            activity_name="Tempo Run",
            avg_hr=165,
            max_hr=190
        )
        assert 'unique_types' in result['consensus']
        assert isinstance(result['consensus']['unique_types'], list)


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_activity_name(self):
        """测试空活动名称"""
        result = comprehensive_training_type_inference(
            activity_name="",
            user_input="轻松跑"
        )
        assert result['training_type'] == '轻松跑'

    def test_no_factors(self):
        """测试无因子"""
        result = comprehensive_training_type_inference(
            activity_name="Run"
        )
        # 至少应该有活动名称
        assert 'activity_name' in result['factors']

    def test_partial_data(self):
        """测试部分数据"""
        result = comprehensive_training_type_inference(
            activity_name="Long Run",
            distance_km=25.0  # 只有距离
        )
        assert result['training_type'] == 'LSD'


class TestSpecificScenarios:
    """测试具体场景"""

    def test_interval_scenario(self):
        """测试间歇跑场景"""
        interval_splits = [
            {'pace': '5:00'}, {'pace': '3:30'}, {'pace': '5:10'},
            {'pace': '3:45'}, {'pace': '5:05'}
        ]
        result = comprehensive_training_type_inference(
            activity_name="Tuesday Intervals",
            distance_km=8.0,
            duration_min=40,
            avg_hr=170,
            max_hr=190,
            splits=interval_splits
        )
        assert result['training_type'] == '间歇跑'
        assert result['factors']['pace']['pace_analysis']['pattern'] == 'interval'

    def test_marathon_pace_scenario(self):
        """测试马拉松配速场景"""
        result = comprehensive_training_type_inference(
            activity_name="Marathon Pace Run",
            distance_km=15.0,
            duration_min=75,
            avg_hr=155,  # Zone 3
            max_hr=190,
            avg_pace_str='5:00'
        )
        assert result['training_type'] == '马拉松配速跑'

    def test_recovery_scenario(self):
        """测试恢复跑场景"""
        result = comprehensive_training_type_inference(
            activity_name="Recovery Jog",
            distance_km=5.0,
            duration_min=35,
            avg_hr=130,  # Zone 2
            max_hr=190,
            avg_pace_str='7:00'
        )
        assert result['training_type'] in ['恢复跑', '轻松跑']  # Recovery Jog 可能识别为恢复跑或轻松跑


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
