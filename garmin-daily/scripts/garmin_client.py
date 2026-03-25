#!/usr/bin/env python3
"""Garmin Connect API 客户端"""

import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

try:
    from garth import Client
    from garth.stats import DailyStress, DailySteps
    from garth.data import HRVData, SleepData
except ImportError:
    raise ImportError("请安装 garth: pip3 install garth")


class GarminClient:
    """Garmin Connect API 客户端封装"""

    def __init__(self, config_path: str = None):
        """初始化 Garmin 客户端"""
        if config_path is None:
            script_dir = Path(__file__).parent.parent
            config_path = script_dir / "config.json"

        self.config = self._load_config(config_path)
        self.client: Optional[Client] = None

    def _load_config(self, config_path: Path) -> Dict[str, str]:
        """加载配置文件（从 config.json 读取）"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 兼容旧格式：支持 GARMIN_EMAIL/PASSWORD 或 email/password
        return {
            'email': config.get('GARMIN_EMAIL') or config.get('email', ''),
            'password': config.get('GARMIN_PASSWORD') or config.get('password', '')
        }

    def login(self) -> bool:
        """登录 Garmin Connect"""
        try:
            email = self.config.get('email')
            password = self.config.get('password')

            if not email or not password:
                print("❌ 请在 config.json 中配置 GARMIN_EMAIL 和 GARMIN_PASSWORD")
                return False

            self.client = Client()
            self.client.login(email, password)
            print(f"✅ 登录成功: {self.client.username}")
            return True

        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return False

    def _ensure_login(self):
        """确保已登录"""
        if self.client is None:
            if not self.login():
                raise RuntimeError("Garmin 未登录")

    def fetch_daily_stats(self, target_date: date) -> Dict[str, Any]:
        """获取每日统计数据（静息心率、最大/最小心率）"""
        self._ensure_login()
        try:
            response = self.client.connectapi(
                "/wellness-service/wellness/dailyStats",
                params={"date": target_date.strftime("%Y-%m-%d")}
            )
            if not response:
                return {}
            return {
                "resting_hr": response.get("restingHeartRate"),
                "max_hr": response.get("maxHeartRate"),
                "min_hr": response.get("minHeartRate"),
                "avg_hr": response.get("averageHeartRate"),
            }
        except Exception as e:
            print(f"⚠️ 获取每日统计失败: {e}")
            return {}

    def fetch_hrv_data(self, target_date: date) -> Dict[str, Any]:
        """获取 HRV 数据"""
        self._ensure_login()
        try:
            hrv = HRVData.get(target_date, client=self.client)
            if not hrv or not hrv.hrv_summary:
                return {}
            s = hrv.hrv_summary
            return {
                "hrv_night_avg": s.last_night_avg,
                "hrv_weekly_avg": s.weekly_avg,
                "hrv_baseline_low": s.baseline_low,
                "hrv_baseline_high": s.baseline_high,
                "hrv_status": s.status,
            }
        except Exception as e:
            print(f"⚠️ 获取 HRV 失败: {e}")
            return {}

    def fetch_sleep_data(self, target_date: date) -> Dict[str, Any]:
        """获取睡眠数据"""
        self._ensure_login()
        try:
            sleep = SleepData.get(target_date, client=self.client)
            if not sleep or not sleep.daily_sleep_dto:
                return {}
            dto = sleep.daily_sleep_dto
            result = {
                "sleep_duration_seconds": dto.sleep_time_seconds,
                "deep_sleep_seconds": dto.deep_sleep_seconds,
                "light_sleep_seconds": dto.light_sleep_seconds,
                "rem_sleep_seconds": dto.rem_sleep_seconds,
                "awake_sleep_seconds": dto.awake_sleep_seconds,
                "sleep_start_time": dto.sleep_start.strftime("%H:%M") if dto.sleep_start else None,
                "sleep_end_time": dto.sleep_end.strftime("%H:%M") if dto.sleep_end else None,
                "spo2_avg": dto.average_sp_o2_value,
                "spo2_min": getattr(dto, 'min_sp_o2_value', None),
                "respiration_avg": dto.average_respiration_value,
            }
            if hasattr(dto, 'sleep_score') and dto.sleep_score:
                result["sleep_score"] = dto.sleep_score
            elif hasattr(sleep, 'sleep_score'):
                result["sleep_score"] = sleep.sleep_score
            return result
        except Exception as e:
            print(f"⚠️ 获取睡眠数据失败: {e}")
            return {}

    def fetch_sleep_stages(self, target_date: date) -> List[Dict[str, Any]]:
        """获取睡眠阶段详情"""
        self._ensure_login()
        try:
            sleep = SleepData.get(target_date, client=self.client)
            if not sleep or not hasattr(sleep, 'sleep_levels') or not sleep.sleep_levels:
                return []
            stages = []
            for level in sleep.sleep_levels:
                stages.append({
                    "stage": level.activity_level,
                    "start_time": level.start_datetime.isoformat() if hasattr(level, 'start_datetime') else None,
                    "end_time": level.end_datetime.isoformat() if hasattr(level, 'end_datetime') else None,
                    "duration_seconds": level.duration_in_seconds if hasattr(level, 'duration_in_seconds') else None,
                })
            return stages
        except Exception as e:
            print(f"⚠️ 获取睡眠阶段失败: {e}")
            return []

    def fetch_body_battery(self, target_date: date) -> Dict[str, Any]:
        """获取身体电量数据"""
        self._ensure_login()
        try:
            response = self.client.connectapi(
                "/bodybattery-service/bodybattery/daily",
                params={"date": target_date.strftime("%Y-%m-%d")}
            )
            if not response:
                return {}
            return {
                "body_battery_start": response.get("endingValue"),
                "body_battery_max": response.get("highestValue"),
                "body_battery_min": response.get("lowestValue"),
                "body_battery_charged": response.get("chargedValue"),
                "body_battery_drained": response.get("drainedValue"),
            }
        except Exception as e:
            print(f"⚠️ 获取身体电量失败: {e}")
            return {}

    def fetch_stress(self, target_date: date) -> Dict[str, Any]:
        """获取压力数据"""
        self._ensure_login()
        try:
            stresses = DailyStress.list(end=target_date, period=1, client=self.client)
            if not stresses:
                return {}
            stress = stresses[0]
            return {
                "stress_avg": stress.overall_stress_level,
                "stress_max": getattr(stress, 'max_stress_level', None),
                "stress_min": getattr(stress, 'min_stress_level', None),
            }
        except Exception as e:
            print(f"⚠️ 获取压力数据失败: {e}")
            return {}

    def fetch_steps(self, target_date: date) -> Dict[str, Any]:
        """获取步数数据"""
        self._ensure_login()
        try:
            steps = DailySteps.list(end=target_date, period=1, client=self.client)
            if not steps:
                return {}
            step = steps[0]
            return {
                "steps": step.total_steps,
                "steps_goal": step.step_goal,
            }
        except Exception as e:
            print(f"⚠️ 获取步数失败: {e}")
            return {}

    def fetch_all_daily_data(self, target_date: date) -> Dict[str, Any]:
        """
        获取指定日期的所有日级数据

        Args:
            target_date: 目标日期

        Returns:
            包含所有数据的字典
        """
        print(f"📅 获取 {target_date} 的数据...")

        data = {"date": target_date.isoformat()}

        # 获取各类数据
        data.update(self.fetch_daily_stats(target_date))
        data.update(self.fetch_hrv_data(target_date))
        data.update(self.fetch_sleep_data(target_date))
        data.update(self.fetch_body_battery(target_date))
        data.update(self.fetch_stress(target_date))
        data.update(self.fetch_steps(target_date))

        return data


if __name__ == "__main__":
    # 测试客户端
    client = GarminClient()

    if client.login():
        print("✅ 客户端测试成功")

        # 测试获取昨天数据
        yesterday = date.today() - timedelta(days=1)
        data = client.fetch_all_daily_data(yesterday)

        print(f"\n📊 昨天 ({yesterday}) 的数据摘要:")
        for key, value in data.items():
            if value is not None:
                print(f"  {key}: {value}")
    else:
        print("❌ 客户端测试失败，请检查配置")
