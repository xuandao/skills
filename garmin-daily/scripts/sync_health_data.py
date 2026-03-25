#!/usr/bin/env python3
"""Garmin 日常健康数据同步脚本"""

import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from db_manager import DatabaseManager
from garmin_client import GarminClient


class HealthDataSync:
    """健康数据同步器"""

    def __init__(self, db_path: str = None, config_path: str = None):
        self.db = DatabaseManager(db_path)
        self.client = GarminClient(config_path)

    def _parse_date_arg(self, date_arg: str) -> date:
        """解析日期参数"""
        if date_arg == "today":
            return date.today()
        elif date_arg == "yesterday":
            return date.today() - timedelta(days=1)
        else:
            return datetime.strptime(date_arg, "%Y-%m-%d").date()

    def _get_target_dates(self, date_arg: str) -> tuple:
        """
        确定需要同步的日期
        - 睡眠数据：取昨晚的
        - 其他数据：取当天
        """
        base_date = self._parse_date_arg(date_arg)
        sleep_date = base_date - timedelta(days=1)
        stats_date = base_date
        return sleep_date, stats_date

    def sync_daily_summary(self, target_date: date) -> bool:
        """同步日级摘要数据"""
        print(f"\n🔄 同步 {target_date} 的日级摘要数据...")
        try:
            data = self.client.fetch_all_daily_data(target_date)
            if not data or len(data) <= 1:
                print(f"⚠️ 未获取到 {target_date} 的有效数据")
                return False

            success = self.db.upsert_daily_health(data)
            if success:
                print(f"✅ {target_date} 数据已保存")
                self._print_summary(data)
            else:
                print(f"❌ {target_date} 数据保存失败")
            return success

        except Exception as e:
            print(f"❌ 同步 {target_date} 失败: {e}")
            return False

    def sync_sleep_details(self, sleep_date: date) -> bool:
        """同步睡眠阶段详情"""
        print(f"\n🔄 同步 {sleep_date} 的睡眠阶段详情...")
        try:
            stages = self.client.fetch_sleep_stages(sleep_date)
            if not stages:
                print(f"⚠️ 未获取到 {sleep_date} 的睡眠阶段数据")
                return False

            success = self.db.insert_sleep_stages(sleep_date.isoformat(), stages)
            if success:
                print(f"✅ {sleep_date} 睡眠阶段已保存 ({len(stages)} 个阶段)")
            else:
                print(f"❌ {sleep_date} 睡眠阶段保存失败")
            return success

        except Exception as e:
            print(f"❌ 同步睡眠阶段失败: {e}")
            return False

    def _print_summary(self, data: dict):
        """打印数据摘要"""
        print("\n📊 关键指标:")
        if data.get('resting_hr'):
            print(f"  ❤️ 静息心率: {data['resting_hr']} bpm")
        if data.get('hrv_night_avg'):
            status = data.get('hrv_status', '')
            print(f"  📈 HRV: {data['hrv_night_avg']:.1f} ms ({status})")
        if data.get('sleep_duration_seconds'):
            hours = data['sleep_duration_seconds'] / 3600
            score = data.get('sleep_score', 'N/A')
            print(f"  😴 睡眠: {hours:.1f}h (评分: {score})")
        if data.get('body_battery_start') is not None:
            print(f"  🔋 身体电量: {data['body_battery_start']} → {data.get('body_battery_max', 'N/A')}")
        if data.get('stress_avg'):
            print(f"  🧘 压力: {data['stress_avg']}")
        if data.get('steps'):
            goal = data.get('steps_goal')
            goal_str = f" / {goal:,}" if goal else ""
            print(f"  👟 步数: {data['steps']:,}{goal_str}")

    def sync(self, date_arg: str = "yesterday", full_sync: bool = False) -> dict:
        """执行同步"""
        print("=" * 50)
        print("🚀 Garmin 健康数据同步")
        print("=" * 50)

        print("\n🔐 登录 Garmin Connect...")
        if not self.client.login():
            return {"success": False, "error": "登录失败"}

        sleep_date, stats_date = self._get_target_dates(date_arg)

        print(f"\n📅 同步计划:")
        print(f"  - 睡眠数据: {sleep_date} (昨晚)")
        print(f"  - 统计数据: {stats_date}")

        results = {
            "success": True,
            "sleep_date": sleep_date.isoformat(),
            "stats_date": stats_date.isoformat(),
            "daily_summary": False,
            "sleep_stages": False,
        }

        results["daily_summary"] = self.sync_daily_summary(stats_date)
        results["sleep_stages"] = self.sync_sleep_details(sleep_date)

        print("\n" + "=" * 50)
        print("📋 同步完成")
        print("=" * 50)

        success_count = sum([results["daily_summary"], results["sleep_stages"]])
        print(f"✅ 成功: {success_count}/2")

        return results

    def close(self):
        """关闭资源"""
        self.db.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="同步 Garmin 日常健康数据到 SQLite")
    parser.add_argument("date", nargs="?", default="yesterday",
                        help="日期: today, yesterday, 或 YYYY-MM-DD (默认: yesterday)")
    parser.add_argument("--db", help="数据库路径")
    parser.add_argument("--config", help="Garmin 配置文件路径")
    parser.add_argument("--full-sync", action="store_true", help="同步分钟级数据")

    args = parser.parse_args()

    syncer = HealthDataSync(db_path=args.db, config_path=args.config)

    try:
        results = syncer.sync(date_arg=args.date, full_sync=args.full_sync)
        syncer.close()
        sys.exit(0 if results["success"] else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 同步被用户中断")
        syncer.close()
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        syncer.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
