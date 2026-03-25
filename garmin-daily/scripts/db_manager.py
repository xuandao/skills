#!/usr/bin/env python3
"""Database manager for Garmin daily health data"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


class DatabaseManager:
    """管理 Garmin 日常健康数据的 SQLite 数据库"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径，默认使用 skill 目录下的 data/garmin_health.db
        """
        if db_path is None:
            script_dir = Path(__file__).parent.parent
            db_path = script_dir / "data" / "garmin_health.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        cursor = self.conn.cursor()

        # 每日健康摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_health (
                date TEXT PRIMARY KEY,
                resting_hr INTEGER,
                max_hr INTEGER,
                min_hr INTEGER,
                avg_hr INTEGER,
                hrv_night_avg REAL,
                hrv_weekly_avg REAL,
                hrv_baseline_low REAL,
                hrv_baseline_high REAL,
                hrv_status TEXT,
                sleep_score INTEGER,
                sleep_duration_seconds INTEGER,
                deep_sleep_seconds INTEGER,
                light_sleep_seconds INTEGER,
                rem_sleep_seconds INTEGER,
                awake_sleep_seconds INTEGER,
                sleep_start_time TEXT,
                sleep_end_time TEXT,
                spo2_avg REAL,
                spo2_min REAL,
                respiration_avg REAL,
                body_battery_start INTEGER,
                body_battery_max INTEGER,
                body_battery_min INTEGER,
                body_battery_charged INTEGER,
                body_battery_drained INTEGER,
                stress_avg INTEGER,
                stress_max INTEGER,
                stress_min INTEGER,
                steps INTEGER,
                steps_goal INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 分钟级心率数据
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS heart_rate_intraday (
                timestamp DATETIME PRIMARY KEY,
                bpm INTEGER
            )
        """)

        # 分钟级压力数据
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stress_intraday (
                timestamp DATETIME PRIMARY KEY,
                level INTEGER
            )
        """)

        # 身体电量变化曲线
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS body_battery_intraday (
                timestamp DATETIME PRIMARY KEY,
                value INTEGER
            )
        """)

        # 睡眠阶段详情
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                stage TEXT,
                start_time DATETIME,
                end_time DATETIME,
                duration_seconds INTEGER,
                FOREIGN KEY (date) REFERENCES daily_health(date) ON DELETE CASCADE
            )
        """)

        # 周统计缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_health_stats (
                week_start TEXT PRIMARY KEY,
                avg_resting_hr REAL,
                avg_hrv REAL,
                avg_sleep_score REAL,
                avg_sleep_hours REAL,
                total_steps INTEGER,
                avg_stress REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 月统计缓存表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_health_stats (
                month TEXT PRIMARY KEY,
                avg_resting_hr REAL,
                avg_hrv REAL,
                avg_sleep_score REAL,
                avg_sleep_hours REAL,
                total_steps INTEGER,
                avg_stress REAL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_heart_rate_timestamp
            ON heart_rate_intraday(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stress_timestamp
            ON stress_intraday(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_body_battery_timestamp
            ON body_battery_intraday(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sleep_stages_date
            ON sleep_stages(date)
        """)

        self.conn.commit()

    def upsert_daily_health(self, data: Dict[str, Any]) -> bool:
        """插入或更新每日健康数据"""
        try:
            cursor = self.conn.cursor()
            columns = list(data.keys())
            placeholders = ", ".join(["?"] * len(columns))

            cursor.execute(
                "SELECT date FROM daily_health WHERE date = ?",
                (data.get("date"),)
            )
            exists = cursor.fetchone()

            if exists:
                update_cols = [f"{col} = ?" for col in columns if col != "date"]
                update_cols.append("updated_at = CURRENT_TIMESTAMP")
                values = [data[col] for col in columns if col != "date"]
                values.append(data.get("date"))
                cursor.execute(
                    f"UPDATE daily_health SET {', '.join(update_cols)} WHERE date = ?",
                    values
                )
            else:
                values = [data.get(col) for col in columns]
                cursor.execute(
                    f"INSERT INTO daily_health ({', '.join(columns)}) VALUES ({placeholders})",
                    values
                )

            self.conn.commit()
            return True

        except Exception as e:
            print(f"❌ Error upserting daily health: {e}")
            self.conn.rollback()
            return False

    def insert_heart_rate_records(self, records: List[Dict[str, Any]]) -> bool:
        """批量插入分钟级心率数据"""
        if not records:
            return True
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT OR REPLACE INTO heart_rate_intraday (timestamp, bpm) VALUES (?, ?)",
                [(r["timestamp"], r["bpm"]) for r in records]
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error inserting heart rate records: {e}")
            self.conn.rollback()
            return False

    def insert_stress_records(self, records: List[Dict[str, Any]]) -> bool:
        """批量插入分钟级压力数据"""
        if not records:
            return True
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT OR REPLACE INTO stress_intraday (timestamp, level) VALUES (?, ?)",
                [(r["timestamp"], r["level"]) for r in records]
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error inserting stress records: {e}")
            self.conn.rollback()
            return False

    def insert_body_battery_records(self, records: List[Dict[str, Any]]) -> bool:
        """批量插入身体电量数据"""
        if not records:
            return True
        try:
            cursor = self.conn.cursor()
            cursor.executemany(
                "INSERT OR REPLACE INTO body_battery_intraday (timestamp, value) VALUES (?, ?)",
                [(r["timestamp"], r["value"]) for r in records]
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error inserting body battery records: {e}")
            self.conn.rollback()
            return False

    def insert_sleep_stages(self, date: str, stages: List[Dict[str, Any]]) -> bool:
        """插入睡眠阶段详情"""
        if not stages:
            return True
        try:
            cursor = self.conn.cursor()
            # 先删除旧数据
            cursor.execute("DELETE FROM sleep_stages WHERE date = ?", (date,))
            # 插入新数据
            for stage in stages:
                cursor.execute("""
                    INSERT INTO sleep_stages (date, stage, start_time, end_time, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                """, (date, stage["stage"], stage["start_time"], stage["end_time"], stage["duration_seconds"]))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error inserting sleep stages: {e}")
            self.conn.rollback()
            return False

    def get_daily_health(self, date: str) -> Optional[Dict[str, Any]]:
        """获取指定日期的健康数据"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM daily_health WHERE date = ?", (date,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_daily_health_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取日期范围内的健康数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_health
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
        """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]

    def get_heart_rate_intraday(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """获取指定时间范围的心率数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM heart_rate_intraday
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        """, (start_time, end_time))
        return [dict(row) for row in cursor.fetchall()]

    def get_sleep_stages(self, date: str) -> List[Dict[str, Any]]:
        """获取指定日期的睡眠阶段"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sleep_stages WHERE date = ? ORDER BY start_time
        """, (date,))
        return [dict(row) for row in cursor.fetchall()]

    def delete_old_intraday_data(self, before_date: str) -> int:
        """删除指定日期之前的分钟级数据"""
        try:
            cursor = self.conn.cursor()
            deleted = 0

            tables = ["heart_rate_intraday", "stress_intraday", "body_battery_intraday"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (before_date,))
                deleted += cursor.rowcount

            self.conn.commit()
            return deleted
        except Exception as e:
            print(f"❌ Error deleting old intraday data: {e}")
            self.conn.rollback()
            return 0

    def close(self):
        """关闭数据库连接"""
        self.conn.close()


if __name__ == "__main__":
    # 测试数据库创建
    db = DatabaseManager()
    print(f"✅ Database initialized at: {db.db_path}")

    # 测试插入数据
    test_data = {
        "date": "2026-03-25",
        "resting_hr": 52,
        "sleep_score": 85,
        "steps": 8432
    }
    db.upsert_daily_health(test_data)
    print("✅ Test data inserted")

    # 查询数据
    result = db.get_daily_health("2026-03-25")
    print(f"✅ Retrieved: {result}")

    db.close()
    print("✅ Database test complete")
