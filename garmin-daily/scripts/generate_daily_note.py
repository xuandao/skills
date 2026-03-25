#!/usr/bin/env python3
"""
从 SQLite 数据库生成 Obsidian 日常健康笔记

参考 pbrun 的架构，从数据库查询数据生成 Markdown
"""

import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from db_manager import DatabaseManager


class DailyNoteGenerator:
    """日常健康笔记生成器"""

    def __init__(self, db_path: str = None, output_dir: str = None):
        """
        初始化生成器

        Args:
            db_path: 数据库路径
            output_dir: 输出目录（默认从 config.json 读取）
        """
        self.db = DatabaseManager(db_path)

        if output_dir is None:
            output_dir = self._get_default_output_dir()

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_default_output_dir(self) -> Path:
        """从 config.json 获取默认输出目录"""
        script_dir = Path(__file__).parent.parent
        config_path = script_dir / "config.json"

        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            obsidian_root = config.get("OBSIDIAN_ROOT", "")
            garmin_folder = config.get("GARMIN_DAILY_FOLDER", "Areas/Health/Garmin")

            return Path(obsidian_root) / garmin_folder

        except Exception:
            # 默认输出到当前目录
            return Path.cwd() / "output"

    def _parse_date_arg(self, date_arg: str) -> date:
        """解析日期参数"""
        if date_arg == "today":
            return date.today()
        elif date_arg == "yesterday":
            return date.today() - timedelta(days=1)
        else:
            return datetime.strptime(date_arg, "%Y-%m-%d").date()

    def _format_duration(self, seconds: int) -> str:
        """格式化时长为 xh xm"""
        if not seconds:
            return "N/A"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _format_number(self, value, decimal: int = 1) -> str:
        """格式化数字"""
        if value is None:
            return "N/A"
        if decimal == 0:
            return str(int(value))
        return f"{value:.{decimal}f}"

    def _get_7day_trend(self, target_date: date) -> list:
        """获取7日趋势数据"""
        end_date = target_date
        start_date = target_date - timedelta(days=6)

        data = self.db.get_daily_health_range(
            start_date.isoformat(),
            end_date.isoformat()
        )

        return data

    def generate_markdown(self, target_date: date) -> str:
        """
        生成 Markdown 内容

        Args:
            target_date: 目标日期

        Returns:
            Markdown 字符串
        """
        # 从数据库获取数据
        data = self.db.get_daily_health(target_date.isoformat())

        if not data:
            return f"# Garmin 健康数据 - {target_date}\n\n⚠️ 暂无数据"

        # 获取睡眠阶段
        sleep_stages = self.db.get_sleep_stages(target_date.isoformat())

        # 获取7日趋势
        trend_data = self._get_7day_trend(target_date)

        # 构建 Markdown
        lines = [
            f"# Garmin 健康数据 - {target_date}",
            "",
            f"**记录时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## ❤️ 心率数据",
        ]

        # 心率
        resting_hr = data.get('resting_hr')
        max_hr = data.get('max_hr')
        min_hr = data.get('min_hr')
        avg_hr = data.get('avg_hr')

        lines.append(f"- 静息心率: {resting_hr if resting_hr else 'N/A'} bpm")
        if max_hr:
            lines.append(f"- 全天最高: {max_hr} bpm")
        if min_hr:
            lines.append(f"- 全天最低: {min_hr} bpm")
        if avg_hr:
            lines.append(f"- 全天平均: {avg_hr} bpm")

        # HRV
        lines.append("")
        lines.append("## 📈 HRV")
        hrv_night = data.get('hrv_night_avg')
        hrv_weekly = data.get('hrv_weekly_avg')
        hrv_low = data.get('hrv_baseline_low')
        hrv_high = data.get('hrv_baseline_high')
        hrv_status = data.get('hrv_status')

        lines.append(f"- 夜间平均: {self._format_number(hrv_night, 1)} ms")
        if hrv_weekly:
            lines.append(f"- 周平均: {self._format_number(hrv_weekly, 1)} ms")
        if hrv_low and hrv_high:
            lines.append(f"- 基线范围: {self._format_number(hrv_low, 0)}-{self._format_number(hrv_high, 0)} ms")
        if hrv_status:
            lines.append(f"- 状态: {hrv_status}")

        # 睡眠
        lines.append("")
        lines.append("## 😴 睡眠")
        sleep_score = data.get('sleep_score')
        sleep_duration = data.get('sleep_duration_seconds')
        deep = data.get('deep_sleep_seconds')
        light = data.get('light_sleep_seconds')
        rem = data.get('rem_sleep_seconds')
        awake = data.get('awake_sleep_seconds')
        sleep_start = data.get('sleep_start_time')
        sleep_end = data.get('sleep_end_time')

        lines.append(f"- 睡眠评分: {sleep_score if sleep_score else 'N/A'}")
        lines.append(f"- 睡眠时长: {self._format_duration(sleep_duration)}")
        lines.append(f"- 深睡: {self._format_duration(deep)}")
        lines.append(f"- 浅睡: {self._format_duration(light)}")
        lines.append(f"- REM: {self._format_duration(rem)}")
        lines.append(f"- 清醒: {self._format_duration(awake)}")
        if sleep_start:
            lines.append(f"- 入睡时间: {sleep_start}")
        if sleep_end:
            lines.append(f"- 醒来时间: {sleep_end}")

        # 睡眠阶段详情
        if sleep_stages:
            lines.append("")
            lines.append("### 睡眠阶段详情")
            lines.append("")
            lines.append("| 阶段 | 开始 | 结束 | 时长 |")
            lines.append("|-----|-----|-----|-----|")
            for stage in sleep_stages:
                stage_name = {
                    'deep': '深睡',
                    'light': '浅睡',
                    'rem': 'REM',
                    'awake': '清醒'
                }.get(stage.get('stage'), stage.get('stage'))

                start = stage.get('start_time', '')
                end = stage.get('end_time', '')
                duration = self._format_duration(stage.get('duration_seconds'))

                lines.append(f"| {stage_name} | {start} | {end} | {duration} |")

        # 呼吸与血氧
        lines.append("")
        lines.append("## 🫁 呼吸与血氧")
        spo2_avg = data.get('spo2_avg')
        spo2_min = data.get('spo2_min')
        respiration = data.get('respiration_avg')

        lines.append(f"- 血氧平均: {self._format_number(spo2_avg, 1)}%")
        if spo2_min:
            lines.append(f"- 血氧最低: {self._format_number(spo2_min, 1)}%")
        lines.append(f"- 呼吸频率: {self._format_number(respiration, 1)} 次/分")

        # 身体电量
        lines.append("")
        lines.append("## 🔋 身体电量")
        bb_start = data.get('body_battery_start')
        bb_max = data.get('body_battery_max')
        bb_min = data.get('body_battery_min')
        bb_charged = data.get('body_battery_charged')
        bb_drained = data.get('body_battery_drained')

        lines.append(f"- 晨起: {bb_start if bb_start is not None else 'N/A'}")
        if bb_max is not None:
            lines.append(f"- 最高: {bb_max}")
        if bb_min is not None:
            lines.append(f"- 最低: {bb_min}")
        if bb_charged is not None:
            lines.append(f"- 充电: {bb_charged}")
        if bb_drained is not None:
            lines.append(f"- 消耗: {bb_drained}")

        # 压力与活动
        lines.append("")
        lines.append("## 🧘 压力与活动")
        stress_avg = data.get('stress_avg')
        stress_max = data.get('stress_max')
        steps = data.get('steps')
        steps_goal = data.get('steps_goal')

        lines.append(f"- 压力水平: {stress_avg if stress_avg else 'N/A'}")
        if stress_max:
            lines.append(f"- 压力最高: {stress_max}")

        if steps:
            goal_str = f" / {steps_goal:,}" if steps_goal else ""
            lines.append(f"- 步数: {steps:,}{goal_str}")
        else:
            lines.append(f"- 步数: N/A")

        # 7日趋势
        if trend_data and len(trend_data) > 1:
            lines.append("")
            lines.append("## 📊 7日趋势")
            lines.append("")
            lines.append("| 日期 | 静息心率 | HRV | 睡眠评分 | 步数 |")
            lines.append("|-----|---------|-----|---------|-----|")

            for day_data in reversed(trend_data):
                day_date = day_data.get('date', '')
                day_resting = day_data.get('resting_hr', '') or ''
                day_hrv = self._format_number(day_data.get('hrv_night_avg'), 1) if day_data.get('hrv_night_avg') else ''
                day_sleep = day_data.get('sleep_score', '') or ''
                day_steps = f"{day_data.get('steps', 0):,}" if day_data.get('steps') else ''

                lines.append(f"| {day_date} | {day_resting} | {day_hrv} | {day_sleep} | {day_steps} |")

        # 备注
        lines.append("")
        lines.append("## 📝 备注")
        lines.append("<!-- 手动添加备注 -->")
        lines.append("")

        return "\n".join(lines)

    def generate(self, date_arg: str = "yesterday") -> Path:
        """
        生成笔记文件

        Args:
            date_arg: 日期参数

        Returns:
            生成的文件路径
        """
        target_date = self._parse_date_arg(date_arg)

        print(f"\n📝 生成 {target_date} 的健康笔记...")

        # 生成 Markdown
        markdown = self.generate_markdown(target_date)

        # 保存文件
        output_file = self.output_dir / f"{target_date}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        print(f"✅ 笔记已保存: {output_file}")
        return output_file

    def close(self):
        """关闭资源"""
        self.db.close()


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="从 SQLite 生成 Garmin 健康笔记")
    parser.add_argument("date", nargs="?", default="yesterday",
                        help="日期: today, yesterday, 或 YYYY-MM-DD (默认: yesterday)")
    parser.add_argument("--db", help="数据库路径")
    parser.add_argument("--output", help="输出目录")

    args = parser.parse_args()

    generator = DailyNoteGenerator(db_path=args.db, output_dir=args.output)

    try:
        output_file = generator.generate(date_arg=args.date)
        generator.close()
        print(f"\n✅ 完成: {output_file}")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        generator.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
