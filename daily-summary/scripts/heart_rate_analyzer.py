#!/usr/bin/env python3
"""
心率数据分析脚本 - 基于 Garmin 数据（运动+日常）
分析紧急信号、早期预警和长期趋势
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), "config.json")


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_obsidian_root() -> str:
    return load_config().get("OBSIDIAN_ROOT", "")


def parse_running_notes_for_hr(obsidian_root: str, days: int = 7) -> Dict:
    """从跑步笔记中解析运动心率数据"""
    running_path = os.path.join(obsidian_root, "Areas/Running")
    hr_data = {"max_hr_records": [], "avg_hr_records": [], "abnormal_events": []}

    if not os.path.exists(running_path):
        return hr_data

    cutoff_date = datetime.now() - timedelta(days=days)

    for training_type in os.listdir(running_path):
        type_path = os.path.join(running_path, training_type)
        if not os.path.isdir(type_path):
            continue

        for filename in os.listdir(type_path):
            if not filename.endswith(".md"):
                continue

            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if not date_match:
                continue

            file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            if file_date < cutoff_date:
                continue

            try:
                with open(os.path.join(type_path, filename), 'r', encoding='utf-8') as f:
                    content = f.read()

                avg_hr_match = re.search(r'平均心率[:：\*]+\s*(\d+(?:\.\d+)?)', content)
                max_hr_match = re.search(r'最大心率[:：\*]+\s*(\d+(?:\.\d+)?)', content)

                record = {"date": date_match.group(1), "training_type": training_type}

                if avg_hr_match:
                    record["avg_hr"] = int(float(avg_hr_match.group(1)))
                    hr_data["avg_hr_records"].append(record.copy())

                if max_hr_match:
                    record["max_hr"] = int(float(max_hr_match.group(1)))
                    hr_data["max_hr_records"].append(record.copy())

                    if record["max_hr"] > 200:
                        hr_data["abnormal_events"].append({
                            "type": "运动中极高心率", "severity": "🔴 紧急",
                            "date": record["date"], "value": record["max_hr"],
                            "description": f"运动时心率飙升至 {record['max_hr']} bpm",
                            "action": "立即停止运动，坐下休息，如不缓解立即就医"
                        })
                    elif record["max_hr"] > 190:
                        hr_data["abnormal_events"].append({
                            "type": "运动中高心率", "severity": "🟡 预警",
                            "date": record["date"], "value": record["max_hr"],
                            "description": f"运动时心率较高 {record['max_hr']} bpm",
                            "action": "监控身体反应，如伴随胸痛/头晕应立即停止"
                        })

                    if record["max_hr"] < 50:
                        hr_data["abnormal_events"].append({
                            "type": "运动中极低心率", "severity": "🔴 紧急",
                            "date": record["date"], "value": record["max_hr"],
                            "description": f"运动时心率异常低至 {record['max_hr']} bpm",
                            "action": "立即停止运动，就医检查"
                        })
            except Exception:
                continue

    return hr_data


def parse_garmin_daily_health(obsidian_root: str, days: int = 30) -> Dict:
    """解析 Garmin 日常健康数据"""
    garmin_data = {
        "resting_hr_records": [], "hrv_records": [], "sleep_hr_records": [],
        "spo2_records": [], "respiratory_records": [], "body_battery_records": []
    }

    garmin_path = os.path.join(obsidian_root, "Areas/Health/Garmin")
    if not os.path.exists(garmin_path):
        return garmin_data

    cutoff_date = datetime.now() - timedelta(days=days)

    for filename in os.listdir(garmin_path):
        if not filename.endswith(".md"):
            continue

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if not date_match:
            continue

        file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
        if file_date < cutoff_date:
            continue

        try:
            with open(os.path.join(garmin_path, filename), 'r', encoding='utf-8') as f:
                content = f.read()

            record = {"date": date_match.group(1)}

            resting_hr = re.search(r'静息心率[:：\*]+\s*(\d+(?:\.\d+)?)', content)
            if resting_hr:
                record["resting_hr"] = int(float(resting_hr.group(1)))
                garmin_data["resting_hr_records"].append(record.copy())

            sleep_hr = re.search(r'睡眠平均心率[:：\*]+\s*(\d+(?:\.\d+)?)', content)
            if sleep_hr:
                record["sleep_hr"] = int(float(sleep_hr.group(1)))
                garmin_data["sleep_hr_records"].append(record.copy())

            hrv = re.search(r'夜间平均[:：\*]+\s*(\d+)', content)
            if hrv:
                record["hrv"] = int(hrv.group(1))
                garmin_data["hrv_records"].append(record.copy())

            spo2 = re.search(r'血氧平均[:：\*]+\s*(\d+(?:\.\d+)?)', content)
            if spo2:
                record["spo2"] = float(spo2.group(1))
                garmin_data["spo2_records"].append(record.copy())

            resp = re.search(r'呼吸频率[:：\*]+\s*(\d+\.?\d*)', content)
            if resp:
                record["respiratory_rate"] = float(resp.group(1))
                garmin_data["respiratory_records"].append(record.copy())

            battery = re.search(r'晨起[:：\*]+\s*(\d+)', content)
            if battery:
                record["body_battery"] = int(battery.group(1))
                garmin_data["body_battery_records"].append(record.copy())
        except Exception:
            continue

    return garmin_data


def analyze_hrv_trend(hrv_records: List[Dict]) -> List[Dict]:
    """分析 HRV 趋势"""
    alerts = []
    if len(hrv_records) < 3:
        return alerts

    sorted_records = sorted(hrv_records, key=lambda x: x["date"])
    for i in range(len(sorted_records) - 2):
        day1, day3 = sorted_records[i], sorted_records[i+2]
        if "hrv" not in day1 or "hrv" not in day3 or day1["hrv"] == 0:
            continue

        drop = (day1["hrv"] - day3["hrv"]) / day1["hrv"] * 100
        if drop > 30:
            alerts.append({
                "type": "HRV连续暴跌", "severity": "🟡 预警",
                "start_date": day1["date"], "end_date": day3["date"],
                "from_value": day1["hrv"], "to_value": day3["hrv"], "drop_percent": round(drop, 1),
                "description": f"HRV 从 {day1['hrv']}ms 连续3天降至 {day3['hrv']}ms，跌幅 {round(drop, 1)}%",
                "action": "尽快安排心脏检查，关注自主神经功能"
            })
    return alerts


def analyze_resting_hr_abnormal(resting_hr_records: List[Dict]) -> List[Dict]:
    """分析静息心率异常"""
    alerts = []
    if len(resting_hr_records) < 3:
        return alerts

    sorted_records = sorted(resting_hr_records, key=lambda x: x["date"])
    high_streak, low_streak = 0, 0
    high_start, low_start = None, None

    for record in sorted_records:
        if "resting_hr" not in record:
            continue

        hr = record["resting_hr"]

        if hr > 100:
            if high_streak == 0:
                high_start = record["date"]
            high_streak += 1
            low_streak = 0
        elif hr < 40:
            if low_streak == 0:
                low_start = record["date"]
            low_streak += 1
            high_streak = 0
        else:
            if high_streak >= 3:
                alerts.append({
                    "type": "静息心动过速", "severity": "🟡 预警",
                    "start_date": high_start, "end_date": record["date"], "value": hr,
                    "description": f"静息心率连续 {high_streak} 天 >100 bpm",
                    "action": "建议就医检查，排除甲亢、贫血、心脏疾病等"
                })
            if low_streak >= 3:
                alerts.append({
                    "type": "静息心动过缓", "severity": "🟡 预警",
                    "start_date": low_start, "end_date": record["date"], "value": hr,
                    "description": f"静息心率连续 {low_streak} 天 <40 bpm",
                    "action": "建议就医检查，排除窦房结功能异常、药物影响等"
                })
            high_streak, low_streak = 0, 0

    return alerts


def analyze_spo2_abnormal(spo2_records: List[Dict]) -> List[Dict]:
    """分析血氧异常"""
    alerts = []
    for record in spo2_records:
        if "spo2" in record and record["spo2"] < 90:
            alerts.append({
                "type": "血氧过低", "severity": "🟡 预警",
                "date": record["date"], "value": record["spo2"],
                "description": f"血氧均值 {record['spo2']}% (<90%)",
                "action": "夜间心律失常风险大增，建议就医检查"
            })
    return alerts


def analyze_respiratory_trend(respiratory_records: List[Dict]) -> List[Dict]:
    """分析呼吸频率趋势"""
    alerts = []
    if len(respiratory_records) < 7:
        return alerts

    sorted_records = sorted(respiratory_records, key=lambda x: x["date"])
    high_streak, high_start = 0, None

    for record in sorted_records:
        if "respiratory_rate" not in record:
            continue

        rr = record["respiratory_rate"]
        if rr > 18:
            if high_streak == 0:
                high_start = record["date"]
            high_streak += 1
        else:
            if high_streak >= 7:
                alerts.append({
                    "type": "呼吸频率持续升高", "severity": "🟢 趋势",
                    "start_date": high_start, "end_date": record["date"], "value": rr,
                    "description": f"呼吸频率连续 {high_streak} 天 >18 次/分",
                    "action": "可能提示心功能下降，建议关注并就医检查"
                })
            high_streak = 0

    return alerts


def generate_heart_rate_report(obsidian_root: str) -> Dict:
    """生成完整的心率分析报告"""
    running_hr = parse_running_notes_for_hr(obsidian_root, days=7)
    garmin_data = parse_garmin_daily_health(obsidian_root, days=30)

    all_alerts = []
    all_alerts.extend(running_hr["abnormal_events"])
    all_alerts.extend(analyze_hrv_trend(garmin_data["hrv_records"]))
    all_alerts.extend(analyze_resting_hr_abnormal(garmin_data["resting_hr_records"]))
    all_alerts.extend(analyze_spo2_abnormal(garmin_data["spo2_records"]))
    all_alerts.extend(analyze_respiratory_trend(garmin_data["respiratory_records"]))

    severity_order = {"🔴 紧急": 0, "🟡 预警": 1, "🟢 趋势": 2}
    all_alerts.sort(key=lambda x: severity_order.get(x.get("severity", ""), 3))

    summary = {
        "total_alerts": len(all_alerts),
        "emergency_count": sum(1 for a in all_alerts if a.get("severity") == "🔴 紧急"),
        "warning_count": sum(1 for a in all_alerts if a.get("severity") == "🟡 预警"),
        "trend_count": sum(1 for a in all_alerts if a.get("severity") == "🟢 趋势"),
        "data_sources": {
            "running_records": len(running_hr["max_hr_records"]),
            "garmin_resting_hr": len(garmin_data["resting_hr_records"]),
            "garmin_hrv": len(garmin_data["hrv_records"]),
            "garmin_spo2": len(garmin_data["spo2_records"])
        }
    }

    return {
        "summary": summary,
        "alerts": all_alerts,
        "raw_data": {"running_hr": running_hr, "garmin": garmin_data}
    }


def format_alert_for_markdown(alert: Dict) -> str:
    """格式化单个警报为 Markdown"""
    lines = [
        f"### {alert.get('severity', '')} {alert.get('type', '未知')}",
        f"- **时间**: {alert.get('date') or alert.get('start_date', '未知')}",
        f"- **描述**: {alert.get('description', '')}",
        f"- **建议行动**: {alert.get('action', '')}"
    ]
    if "value" in alert:
        lines.insert(2, f"- **数值**: {alert['value']}")
    if "from_value" in alert and "to_value" in alert:
        lines.insert(2, f"- **变化**: {alert['from_value']} → {alert['to_value']}")
    if "drop_percent" in alert:
        lines.insert(2, f"- **跌幅**: {alert['drop_percent']}%")
    return "\n".join(lines)


def generate_markdown_report(report: Dict) -> str:
    """生成 Markdown 格式的完整报告"""
    summary = report["summary"]
    alerts = report["alerts"]

    lines = [
        "## ❤️ 心率健康分析",
        "",
        f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**数据来源**: Garmin 运动 ({summary['data_sources']['running_records']} 条) | Garmin 日常 ({summary['data_sources']['garmin_resting_hr']} 天)",
        "",
        "### 📊 警报统计",
        f"- 🔴 紧急信号: {summary['emergency_count']} 项",
        f"- 🟡 早期预警: {summary['warning_count']} 项",
        f"- 🟢 长期趋势: {summary['trend_count']} 项",
        ""
    ]

    if not alerts:
        lines.extend(["### ✅ 健康状况", "未发现异常心率信号，继续保持良好的健康习惯！", ""])
    else:
        emergency = [a for a in alerts if a.get("severity") == "🔴 紧急"]
        warning = [a for a in alerts if a.get("severity") == "🟡 预警"]
        trend = [a for a in alerts if a.get("severity") == "🟢 趋势"]

        if emergency:
            lines.extend(["### 🔴 紧急信号（需立即关注）", ""])
            for alert in emergency:
                lines.extend([format_alert_for_markdown(alert), ""])

        if warning:
            lines.extend(["### 🟡 早期预警（建议尽快检查）", ""])
            for alert in warning:
                lines.extend([format_alert_for_markdown(alert), ""])

        if trend:
            lines.extend(["### 🟢 长期趋势（定期关注）", ""])
            for alert in trend:
                lines.extend([format_alert_for_markdown(alert), ""])

    lines.extend([
        "### 📋 健康参考指标",
        "",
        "| 指标 | 正常范围 | 预警阈值 | 紧急阈值 |",
        "|------|----------|----------|----------|",
        "| 运动时最大心率 | 150-170 bpm | >190 | >200 或 <50 |",
        "| 静息心率 | 50-80 bpm | 连续3天 >100 或 <40 | - |",
        "| HRV | 60-100 ms | 连续3天下降 >30% | - |",
        "| 血氧 | 95-100% | <90% | - |",
        "| 呼吸频率 | 12-16 次/分 | 持续 >18 次/分 | - |",
        ""
    ])

    return "\n".join(lines)


def main():
    obsidian_root = get_obsidian_root()
    if not obsidian_root:
        print(json.dumps({"error": "无法获取 Obsidian 根目录"}, ensure_ascii=False))
        sys.exit(1)

    report = generate_heart_rate_report(obsidian_root)

    print(json.dumps({
        "status": "success",
        "markdown_report": generate_markdown_report(report),
        "summary": report["summary"],
        "alerts_count": len(report["alerts"]),
        "has_emergency": report["summary"]["emergency_count"] > 0,
        "has_warning": report["summary"]["warning_count"] > 0
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
