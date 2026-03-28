#!/usr/bin/env python3
"""
Phase 3 Task 1 单元测试
测试用户输入识别功能

运行方式:
    python3 -m pytest tests/unit/test_p3_t1_input_detection.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.generate_strava_note import get_training_type


class TestIntervalTrainingDetection:
    """测试间歇跑识别"""

    def test_basic_interval(self):
        """测试基本间歇跑"""
        assert get_training_type("Run", "跑了个间歇") == "间歇跑"
        assert get_training_type("Run", "间歇训练") == "间歇跑"

    def test_hiit(self):
        """测试 HIIT"""
        assert get_training_type("Run", "HIIT训练") == "间歇跑"
        assert get_training_type("Run", "高强度训练") == "间歇跑"

    def test_fartlek(self):
        """测试法特莱克"""
        assert get_training_type("Run", "法特莱克跑") == "间歇跑"
        assert get_training_type("Run", "fartlek训练") == "间歇跑"

    def test_interval_english(self):
        """测试英文 interval"""
        assert get_training_type("Run", "interval training") == "间歇跑"
        assert get_training_type("Run", "run interval") == "间歇跑"

    def test_speed_variation(self):
        """测试变速跑"""
        assert get_training_type("Run", "变速跑") == "间歇跑"


class TestTempoDetection:
    """测试节奏跑识别"""

    def test_basic_tempo(self):
        """测试基本节奏跑"""
        assert get_training_type("Run", "节奏跑") == "节奏跑"
        assert get_training_type("Run", "跑节奏") == "节奏跑"

    def test_tempo_english(self):
        """测试英文 tempo"""
        assert get_training_type("Run", "tempo run") == "节奏跑"
        assert get_training_type("Run", "tempo training") == "节奏跑"

    def test_threshold(self):
        """测试乳酸阈值"""
        assert get_training_type("Run", "乳酸阈值训练") == "节奏跑"
        assert get_training_type("Run", "threshold run") == "节奏跑"


class TestLSDDetection:
    """测试 LSD 识别"""

    def test_basic_lsd(self):
        """测试基本 LSD"""
        assert get_training_type("Run", "LSD") == "LSD"
        assert get_training_type("Run", "lsd训练") == "LSD"

    def test_long_distance(self):
        """测试长距离"""
        assert get_training_type("Run", "长距离慢跑") == "LSD"
        assert get_training_type("Run", "周末长距离") == "LSD"

    def test_long_run(self):
        """测试 long run"""
        assert get_training_type("Run", "long run") == "LSD"


class TestEasyRunDetection:
    """测试轻松跑识别"""

    def test_basic_easy(self):
        """测试基本轻松跑"""
        assert get_training_type("Run", "轻松跑") == "轻松跑"
        assert get_training_type("Run", "轻松训练") == "轻松跑"

    def test_easy_english(self):
        """测试英文 easy"""
        assert get_training_type("Run", "easy run") == "轻松跑"
        assert get_training_type("Run", "easy jog") == "轻松跑"

    def test_aerobic(self):
        """测试有氧跑"""
        assert get_training_type("Run", "有氧跑") == "轻松跑"
        assert get_training_type("Run", "有氧基础跑") == "轻松跑"


class TestRecoveryDetection:
    """测试恢复跑识别"""

    def test_basic_recovery(self):
        """测试基本恢复跑"""
        assert get_training_type("Run", "恢复跑") == "恢复跑"
        assert get_training_type("Run", "恢复训练") == "恢复跑"

    def test_recovery_english(self):
        """测试英文 recovery"""
        assert get_training_type("Run", "recovery run") == "恢复跑"
        assert get_training_type("Run", "recovery jog") == "恢复跑"

    def test_relax(self):
        """测试放松跑"""
        assert get_training_type("Run", "放松跑") == "恢复跑"
        assert get_training_type("Run", "放松慢跑") == "恢复跑"


class TestTreadmillDetection:
    """测试跑步机识别"""

    def test_basic_treadmill(self):
        """测试基本跑步机"""
        assert get_training_type("Run", "跑步机") == "跑步机"
        assert get_training_type("Run", "跑跑步机") == "跑步机"

    def test_treadmill_english(self):
        """测试英文 treadmill"""
        assert get_training_type("Run", "treadmill run") == "跑步机"

    def test_indoor(self):
        """测试室内跑"""
        assert get_training_type("Run", "室内跑") == "跑步机"
        assert get_training_type("Run", "gym跑步") == "跑步机"


class TestMarathonPaceDetection:
    """测试马拉松配速跑识别"""

    def test_basic_marathon_pace(self):
        """测试基本马拉松配速"""
        assert get_training_type("Run", "马拉松配速") == "马拉松配速跑"
        assert get_training_type("Run", "马配跑") == "马拉松配速跑"

    def test_mp(self):
        """测试 MP"""
        assert get_training_type("Run", "MP训练") == "马拉松配速跑"

    def test_marathon_english(self):
        """测试英文 marathon pace"""
        assert get_training_type("Run", "marathon pace") == "马拉松配速跑"

    def test_race_pace(self):
        """测试比赛配速"""
        assert get_training_type("Run", "比赛配速") == "马拉松配速跑"


class TestDefaultBehavior:
    """测试默认行为"""

    def test_default_easy_run(self):
        """测试无匹配时默认轻松跑"""
        assert get_training_type("Run", "随便跑跑") == "轻松跑"
        assert get_training_type("Run", "日常跑步") == "轻松跑"
        assert get_training_type("Run", "") == "轻松跑"
        assert get_training_type("Run", None) == "轻松跑"

    def test_activity_name_fallback(self):
        """测试从活动名称识别"""
        assert get_training_type("Morning Interval", None) == "间歇跑"
        assert get_training_type("Tempo Run", None) == "节奏跑"
        assert get_training_type("Easy Jog", None) == "轻松跑"

    def test_user_input_priority(self):
        """测试用户输入优先级高于活动名称"""
        # 活动名称是 Interval，但用户说是 Tempo
        assert get_training_type("Interval Run", "今天跑tempo") == "节奏跑"
        # 活动名称是 Easy，但用户说是 Recovery
        assert get_training_type("Easy Run", "恢复跑") == "恢复跑"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
