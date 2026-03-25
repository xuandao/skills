#!/usr/bin/env python3
"""
获取 Garmin 日常健康数据（非运动状态）
包括：静息心率、HRV、睡眠、压力、身体电量等
"""

import os
import sys
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional

try:
    from garth import Client
    from garth.stats import DailyHRV, DailySleep, DailyStress, DailySteps
    from garth.data import HRVData, SleepData
except ImportError:
    print("❌ Please install garth: pip3 install garth", file=sys.stderr)
    sys.exit(1)


def read_config():
    """Read Garmin credentials from config file"""
    # Try garmin-running skill config first
    script_dir = Path(__file__).parent.parent.parent / "garmin-running"
    config_file = script_dir / "references" / "garmin_config.json"

    if not config_file.exists():
        # Try daily-summary skill config
        script_dir = Path(__file__).parent.parent
        config_file = script_dir / "references" / "garmin_config.json"

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    with open(config_file, 'r') as f:
        config = json.load(f)

    return config.get('email'), config.get('password')


def login_garmin(email, password):
    """Login to Garmin Connect using garth"""
    try:
        client = Client()
        client.login(email, password)
        return client
    except Exception as e:
        print(f"❌ Login failed: {e}", file=sys.stderr)
        sys.exit(1)


def get_resting_heart_rate(client, target_date: date) -> Optional[Dict]:
    """
    获取静息心率数据
    通过 wellness-service API 获取
    """
    try:
        date_str = target_date.strftime("%Y-%m-%d")

        # 尝试获取每日健康统计数据
        result = client.connectapi(
            "/wellness-service/wellness/dailyStats",
            params={"date": date_str}
        )

        if result and isinstance(result, dict):
            return {
                "date": date_str,
                "resting_hr": result.get("restingHeartRate"),
                "max_hr": result.get("maxHeartRate"),
                "min_hr": result.get("minHeartRate"),
                "avg_hr": result.get("averageHeartRate"),
                "source": "dailyStats"
            }

        # 备选：尝试用户摘要 API
        result = client.connectapi(
            "/usersummary-service/usersummary/daily",
            params={"calendarDate": date_str}
        )

        if result and isinstance(result, dict):
            wellness = result.get("wellness", {})
            return {
                "date": date_str,
                "resting_hr": wellness.get("restingHeartRate"),
                "max_hr": wellness.get("maxHeartRate"),
                "min_hr": wellness.get("minHeartRate"),
                "avg_hr": wellness.get("averageHeartRate"),
                "source": "userSummary"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch resting HR: {e}", file=sys.stderr)
        return None


def get_heart_rate_intraday(client, target_date: date) -> Optional[Dict]:
    """
    获取全天候心率数据（日内详细数据）
    """
    try:
        date_str = target_date.strftime("%Y-%m-%d")

        # 获取日内心率数据
        result = client.connectapi(
            "/wellness-service/wellness/dailyHeartRate",
            params={"date": date_str}
        )

        if result and isinstance(result, dict):
            heart_rate_values = result.get("heartRateValues", [])

            if heart_rate_values:
                # 计算统计数据
                hr_values = [v[1] for v in heart_rate_values if len(v) > 1 and v[1] > 0]

                if hr_values:
                    return {
                        "date": date_str,
                        "data_points": len(hr_values),
                        "min_hr": min(hr_values),
                        "max_hr": max(hr_values),
                        "avg_hr": round(sum(hr_values) / len(hr_values), 1),
                        "samples": heart_rate_values[:10],  # 前10个样本
                        "source": "intraday"
                    }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch intraday HR: {e}", file=sys.stderr)
        return None


def get_hrv_data(client, target_date: date) -> Optional[Dict]:
    """
    获取 HRV 数据（使用 garth 的 HRVData）
    """
    try:
        hrv = HRVData.get(target_date, client=client)

        if hrv:
            summary = hrv.hrv_summary
            return {
                "date": summary.calendar_date.isoformat(),
                "weekly_avg": summary.weekly_avg,
                "last_night_avg": summary.last_night_avg,
                "last_night_5_min_high": summary.last_night_5_min_high,
                "baseline_low_upper": summary.baseline.low_upper,
                "baseline_balanced_low": summary.baseline.balanced_low,
                "baseline_balanced_upper": summary.baseline.balanced_upper,
                "baseline_marker": summary.baseline.marker_value,
                "status": summary.status,
                "feedback": summary.feedback_phrase,
                "readings_count": len(hrv.hrv_readings) if hrv.hrv_readings else 0,
                "source": "hrvService"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch HRV: {e}", file=sys.stderr)
        return None


def get_sleep_data(client, target_date: date) -> Optional[Dict]:
    """
    获取睡眠数据（使用 garth 的 SleepData）
    """
    try:
        sleep = SleepData.get(target_date, client=client)

        if sleep and sleep.daily_sleep_dto:
            dto = sleep.daily_sleep_dto

            # 计算睡眠时长（小时）
            sleep_hours = dto.sleep_time_seconds / 3600 if dto.sleep_time_seconds else 0

            # 获取血氧数据
            spo2_avg = dto.average_sp_o2_value
            spo2_low = dto.lowest_sp_o2_value
            spo2_high = dto.highest_sp_o2_value

            # 获取呼吸频率
            resp_avg = dto.average_respiration_value
            resp_low = dto.lowest_respiration_value
            resp_high = dto.highest_respiration_value

            # 获取睡眠评分
            sleep_score = None
            if dto.sleep_scores and dto.sleep_scores.overall:
                sleep_score = dto.sleep_scores.overall.value

            return {
                "date": dto.calendar_date.isoformat(),
                "sleep_duration_hours": round(sleep_hours, 2),
                "sleep_start": dto.sleep_start.isoformat() if dto.sleep_start else None,
                "sleep_end": dto.sleep_end.isoformat() if dto.sleep_end else None,
                "deep_sleep_seconds": dto.deep_sleep_seconds,
                "light_sleep_seconds": dto.light_sleep_seconds,
                "rem_sleep_seconds": dto.rem_sleep_seconds,
                "awake_sleep_seconds": dto.awake_sleep_seconds,
                "awake_count": dto.awake_count,
                "sleep_score": sleep_score,
                "spo2_avg": spo2_avg,
                "spo2_low": spo2_low,
                "spo2_high": spo2_high,
                "respiration_avg": resp_avg,
                "respiration_low": resp_low,
                "respiration_high": resp_high,
                "avg_sleep_stress": dto.avg_sleep_stress,
                "source": "sleepService"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch sleep: {e}", file=sys.stderr)
        return None


def get_body_battery(client, target_date: date) -> Optional[Dict]:
    """
    获取 Body Battery（身体电量）数据
    """
    try:
        date_str = target_date.strftime("%Y-%m-%d")

        result = client.connectapi(
            "/bodybattery-service/bodybattery/daily",
            params={"date": date_str}
        )

        if result and isinstance(result, dict):
            return {
                "date": date_str,
                "charged": result.get("chargedValue"),
                "drained": result.get("drainedValue"),
                "highest": result.get("highestValue"),
                "lowest": result.get("lowestValue"),
                "ending": result.get("endingValue"),
                "source": "bodyBattery"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch body battery: {e}", file=sys.stderr)
        return None


def get_stress_data(client, target_date: date) -> Optional[Dict]:
    """
    获取压力数据
    """
    try:
        # 使用 garth 的 DailyStress
        stresses = DailyStress.list(end=target_date, period=1, client=client)

        if stresses and len(stresses) > 0:
            stress = stresses[0]
            return {
                "date": stress.calendar_date.isoformat(),
                "overall_stress_level": stress.overall_stress_level,
                "rest_stress_duration": stress.rest_stress_duration,
                "low_stress_duration": stress.low_stress_duration,
                "medium_stress_duration": stress.medium_stress_duration,
                "high_stress_duration": stress.high_stress_duration,
                "source": "stressService"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch stress: {e}", file=sys.stderr)
        return None


def get_steps_data(client, target_date: date) -> Optional[Dict]:
    """
    获取步数数据
    """
    try:
        # 使用 garth 的 DailySteps
        steps = DailySteps.list(end=target_date, period=1, client=client)

        if steps and len(steps) > 0:
            step = steps[0]
            return {
                "date": step.calendar_date.isoformat(),
                "steps": step.value,
                "source": "stepsService"
            }

        return None

    except Exception as e:
        print(f"⚠️ Failed to fetch steps: {e}", file=sys.stderr)
        return None


def fetch_daily_health_data(client, target_date: date) -> Dict:
    """
    获取指定日期的所有日常健康数据
    """
    print(f"📅 Fetching health data for {target_date}...")

    result = {
        "date": target_date.isoformat(),
        "fetch_time": datetime.now().isoformat(),
        "data": {}
    }

    # 1. 静息心率
    print("  💓 Resting heart rate...")
    resting_hr = get_resting_heart_rate(client, target_date)
    if resting_hr:
        result["data"]["resting_hr"] = resting_hr

    # 2. 全天候心率
    print("  📊 Intraday heart rate...")
    intraday_hr = get_heart_rate_intraday(client, target_date)
    if intraday_hr:
        result["data"]["intraday_hr"] = intraday_hr

    # 3. HRV 数据
    print("  📈 HRV...")
    hrv = get_hrv_data(client, target_date)
    if hrv:
        result["data"]["hrv"] = hrv

    # 4. 睡眠数据
    print("  😴 Sleep...")
    sleep = get_sleep_data(client, target_date)
    if sleep:
        result["data"]["sleep"] = sleep

    # 5. Body Battery
    print("  🔋 Body battery...")
    battery = get_body_battery(client, target_date)
    if battery:
        result["data"]["body_battery"] = battery

    # 6. 压力数据
    print("  🧘 Stress...")
    stress = get_stress_data(client, target_date)
    if stress:
        result["data"]["stress"] = stress

    # 7. 步数数据
    print("  👟 Steps...")
    steps = get_steps_data(client, target_date)
    if steps:
        result["data"]["steps"] = steps

    # 统计成功获取的数据项
    result["data_sources_count"] = len(result["data"])
    result["data_sources"] = list(result["data"].keys())

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: fetch_garmin_daily_health.py <date> [output_file]", file=sys.stderr)
        print("  date: YYYY-MM-DD or 'today' or 'yesterday'", file=sys.stderr)
        sys.exit(1)

    date_arg = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    # 解析日期
    if date_arg == "today":
        target_date = date.today()
    elif date_arg == "yesterday":
        target_date = date.today() - timedelta(days=1)
    else:
        try:
            target_date = datetime.strptime(date_arg, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format: {date_arg}", file=sys.stderr)
            sys.exit(1)

    print("📖 Reading config...")
    email, password = read_config()

    print("🔐 Logging in to Garmin Connect...")
    client = login_garmin(email, password)
    print(f"✅ Logged in as: {client.username}")

    # 获取数据
    result = fetch_daily_health_data(client, target_date)

    # 输出结果
    json_output = json.dumps(result, indent=2, ensure_ascii=False)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"\n✅ Data saved to: {output_file}")
    else:
        print("\n" + "=" * 60)
        print(json_output)


if __name__ == "__main__":
    main()
