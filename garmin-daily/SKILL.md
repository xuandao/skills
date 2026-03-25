---
name: garmin-daily
description: 自动从 Garmin Connect 获取日常健康数据（静息心率、HRV、睡眠、血氧、呼吸频率、身体电量等），存入 SQLite 数据库，并生成 Obsidian 笔记。
---

# Garmin 日常数据获取技能

自动从 Garmin Connect 获取日常健康数据，存入 SQLite 数据库，并生成结构化的 Obsidian 笔记。

参考 pbrun 项目的架构设计，采用"数据库存储 + 笔记生成"的分层架构。

## 架构设计（参考 pbrun）

```
garmin-daily/
├── data/
│   └── garmin_health.db          # SQLite 数据库
├── scripts/
│   ├── db_manager.py             # 数据库管理（类似 pbrun/db-manager.js）
│   ├── garmin_client.py          # Garmin API 客户端（基于 garth）
│   ├── sync_health_data.py       # 主同步脚本（类似 pbrun/sync-garmin.js）
│   └── generate_daily_note.py    # 从 DB 生成 Obsidian 笔记
├── config.json                   # 技能配置（包含账号信息）
└── SKILL.md                      # 本文件
```

## 数据库设计

### 表结构

```sql
-- 每日健康摘要表（日级聚合数据）
daily_health (
    date TEXT PRIMARY KEY,              -- 日期 (YYYY-MM-DD)
    
    -- 心率数据
    resting_hr INTEGER,                 -- 静息心率 (bpm)
    max_hr INTEGER,                     -- 全天最高心率
    min_hr INTEGER,                     -- 全天最低心率
    avg_hr INTEGER,                     -- 全天平均心率
    
    -- HRV 数据
    hrv_night_avg REAL,                 -- 夜间平均 HRV (ms)
    hrv_weekly_avg REAL,                -- 周平均 HRV
    hrv_baseline_low REAL,              -- HRV 基线下限
    hrv_baseline_high REAL,             -- HRV 基线上限
    hrv_status TEXT,                    -- HRV 状态 (BALANCED/UNBALANCED/...)
    
    -- 睡眠数据
    sleep_score INTEGER,                -- 睡眠评分 (0-100)
    sleep_duration_seconds INTEGER,     -- 睡眠总时长 (秒)
    deep_sleep_seconds INTEGER,         -- 深睡时长
    light_sleep_seconds INTEGER,        -- 浅睡时长
    rem_sleep_seconds INTEGER,          -- REM 时长
    awake_sleep_seconds INTEGER,        -- 清醒时长
    sleep_start_time TEXT,              -- 入睡时间 (HH:MM)
    sleep_end_time TEXT,                -- 醒来时间 (HH:MM)
    
    -- 呼吸与血氧
    spo2_avg REAL,                      -- 平均血氧 (%)
    spo2_min REAL,                      -- 最低血氧
    respiration_avg REAL,               -- 平均呼吸频率 (次/分)
    
    -- 身体电量
    body_battery_start INTEGER,         -- 晨起电量
    body_battery_max INTEGER,           -- 最高电量
    body_battery_min INTEGER,           -- 最低电量
    body_battery_charged INTEGER,       -- 充电值
    body_battery_drained INTEGER,       -- 消耗值
    
    -- 压力与活动
    stress_avg INTEGER,                 -- 平均压力水平
    stress_max INTEGER,                 -- 最高压力
    stress_min INTEGER,                 -- 最低压力
    steps INTEGER,                      -- 步数
    steps_goal INTEGER,                 -- 步数目标
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 分钟级心率数据（用于趋势分析）
heart_rate_intraday (
    timestamp DATETIME PRIMARY KEY,     -- 精确到分钟的时间戳
    bpm INTEGER                         -- 心率值
);

-- 分钟级压力数据
stress_intraday (
    timestamp DATETIME PRIMARY KEY,
    level INTEGER                       -- 压力值 (0-100)
);

-- 身体电量变化曲线
body_battery_intraday (
    timestamp DATETIME PRIMARY KEY,
    value INTEGER                       -- 电量值 (0-100)
);

-- 睡眠阶段详情
sleep_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,                          -- 关联的日期
    stage TEXT,                         -- 阶段: deep/light/rem/awake
    start_time DATETIME,                -- 阶段开始时间
    end_time DATETIME,                  -- 阶段结束时间
    duration_seconds INTEGER,           -- 阶段持续时间
    FOREIGN KEY (date) REFERENCES daily_health(date) ON DELETE CASCADE
);

-- 统计缓存表（用于快速查询周/月趋势）
weekly_health_stats (
    week_start TEXT PRIMARY KEY,        -- 周开始日期 (周一)
    avg_resting_hr REAL,
    avg_hrv REAL,
    avg_sleep_score REAL,
    avg_sleep_hours REAL,
    total_steps INTEGER,
    avg_stress REAL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

monthly_health_stats (
    month TEXT PRIMARY KEY,             -- 月份 (YYYY-MM)
    avg_resting_hr REAL,
    avg_hrv REAL,
    avg_sleep_score REAL,
    avg_sleep_hours REAL,
    total_steps INTEGER,
    avg_stress REAL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 索引设计

```sql
-- 时间范围查询优化
CREATE INDEX idx_heart_rate_timestamp ON heart_rate_intraday(timestamp);
CREATE INDEX idx_stress_timestamp ON stress_intraday(timestamp);
CREATE INDEX idx_body_battery_timestamp ON body_battery_intraday(timestamp);
CREATE INDEX idx_sleep_stages_date ON sleep_stages(date);
```

## 运行方式

### 触发指令
- "获取 Garmin 日常数据"
- "同步 Garmin 健康数据"
- "fetch garmin daily"

### 手动执行

```bash
# 同步最近 24 小时数据到 SQLite
python3 scripts/sync_health_data.py

# 生成指定日期的 Obsidian 笔记
python3 scripts/generate_daily_note.py 2026-03-25

# 同步并生成笔记（组合命令）
python3 scripts/sync_health_data.py && python3 scripts/generate_daily_note.py yesterday
```

### 参数说明

**sync_health_data.py:**
- `--date`: `today` (默认), `yesterday`, 或 `YYYY-MM-DD`
- `--db`: 数据库路径（默认 `data/garmin_health.db`）
- `--full-sync`: 全量同步（获取分钟级数据）
- `--summary-only`: 仅同步日级摘要（更快）

**generate_daily_note.py:**
- `date`: 日期参数（`today`, `yesterday`, 或 `YYYY-MM-DD`）
- `--db`: 数据库路径
- `--output`: 输出目录（默认从 config.json 读取）

## 获取的数据项

| 数据类型 | API 端点 | 存储粒度 | 说明 |
|---------|---------|---------|------|
| 静息心率 | `/wellness-service/wellness/dailyStats` | 日级 | 全天静息心率 |
| 全天候心率 | `/wellness-service/wellness/dailyHeartRate` | 分钟级 | 每分钟心率 |
| HRV | `/hrv-service/hrv/{date}` | 日级 | 夜间平均、周平均、基线 |
| 睡眠 | `/wellness-service/wellness/dailySleepData` | 日级+阶段 | 睡眠评分、时长、阶段 |
| 血氧 | Sleep API | 日级 | 睡眠期间血氧数据 |
| 呼吸频率 | Sleep API | 日级 | 睡眠期间呼吸频率 |
| Body Battery | `/bodybattery-service/bodybattery/daily` | 日级+小时级 | 身体电量变化 |
| 压力 | `/usersummary-service/stats/stress` | 日级+分钟级 | 压力水平统计 |
| 步数 | `/usersummary-service/stats/steps` | 日级 | 每日步数 |

## 输出格式

生成的 Markdown 文件格式：

```markdown
# Garmin 健康数据 - 2026-03-25

## 📊 基础指标
- **记录日期**: 2026-03-25
- **数据更新时间**: 2026-03-25 07:30:00

## ❤️ 心率数据
- 静息心率: 52 bpm
- 全天最高: 145 bpm
- 全天最低: 42 bpm
- 全天平均: 68 bpm

## 📈 HRV
- 夜间平均: 72 ms
- 周平均: 68 ms
- 基线范围: 65-85 ms
- 状态: BALANCED

## 😴 睡眠
- 睡眠评分: 85
- 睡眠时长: 7h 23m
- 深睡: 1h 45m
- 浅睡: 4h 12m
- REM: 1h 26m
- 清醒: 20m
- 入睡时间: 23:15
- 醒来时间: 06:38

## 🫁 呼吸与血氧
- 血氧平均: 98.5%
- 血氧最低: 95%
- 呼吸频率: 14.2 次/分

## 🔋 身体电量
- 晨起: 65
- 最高: 95
- 最低: 30
- 充电: 85
- 消耗: 65

## 🧘 压力与活动
- 压力水平: 35
- 步数: 8,432

## 📊 7日趋势
<!-- 从 SQLite 查询生成 -->
| 日期 | 静息心率 | HRV | 睡眠评分 | 步数 |
|-----|---------|-----|---------|-----|
| 03-19 | 53 | 70 | 82 | 8234 |
| ... | ... | ... | ... | ... |

## 📝 备注
<!-- 手动添加备注 -->
```

## 配置说明

### config.json
```json
{
  "OBSIDIAN_ROOT": "/path/to/obsidian/vault",
  "GARMIN_DAILY_FOLDER": "Areas/Health/Garmin",
  "GARMIN_EMAIL": "your@email.com",
  "GARMIN_PASSWORD": "yourpassword"
}
```

## 自动化建议

### Cron 定时任务
建议每天上午 7:30 自动执行：
```bash
openclaw cron add --name "garmin-daily-sync" \
  --schedule "30 7 * * *" \
  --command "cd ~/.openclaw/workspace/skills/garmin-daily && python3 scripts/sync_health_data.py && python3 scripts/generate_daily_note.py today"
```

## 开发任务拆分

### Phase 1: 数据库层 ✅
- [x] 创建 `db_manager.py` - 数据库连接、表创建、基础 CRUD
- [x] 设计表结构（daily_health, intraday 表, 统计缓存表）
- [x] 实现数据插入/更新逻辑（UPSERT）

### Phase 2: Garmin 客户端 ✅
- [x] 封装 `garmin_client.py` - 基于 garth 的 API 调用
- [x] 实现各数据类型的获取方法
- [x] 添加错误处理和重试机制

### Phase 3: 同步逻辑 ✅
- [x] 实现 `sync_health_data.py` 主脚本
- [x] 处理"最近 24 小时"逻辑（睡眠取昨晚，其他取昨天）
- [x] 支持全量同步和摘要同步两种模式

### Phase 4: 笔记生成 ✅
- [x] 实现 `generate_daily_note.py`
- [x] 从 SQLite 查询数据生成 Markdown
- [x] 添加 7 日趋势表格

### Phase 5: 优化（TODO）
- [ ] 统计缓存更新（周/月聚合）
- [ ] 数据清理（保留 N 天分钟级数据）
- [ ] 增量同步优化
- [ ] 分钟级 intraday 数据同步
- [x] 配置合并到 config.json

## 注意事项
- Garmin 数据通常有 15-30 分钟延迟
- 确保设备已同步到 Garmin Connect
- API 有频率限制，避免频繁调用
- 分钟级数据占用空间大，建议定期清理或归档
