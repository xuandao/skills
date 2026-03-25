# Garmin Connect API 调研报告 - 日常健康数据

## 调研目标
获取 Garmin 设备记录的日常态心率数据（非运动状态），包括：
- 静息心率 (Resting Heart Rate)
- 全天候心率趋势
- HRV (心率变异性)
- 睡眠心率
- 压力相关心率数据

## 可用 API 端点

### 1. 静息心率与基础健康数据

**Endpoint**: `/wellness-service/wellness/dailyStats`
**Method**: GET
**Parameters**: `date=YYYY-MM-DD`

**返回数据**:
```json
{
  "restingHeartRate": 52,
  "maxHeartRate": 175,
  "minHeartRate": 42,
  "averageHeartRate": 68
}
```

**说明**: 这是获取日常静息心率的主要接口。

### 2. 全天候心率详细数据

**Endpoint**: `/wellness-service/wellness/dailyHeartRate`
**Method**: GET
**Parameters**: `date=YYYY-MM-DD`

**返回数据**:
```json
{
  "heartRateValues": [
    [timestamp, hr_value],
    [1742803200000, 68],
    [1742803260000, 69],
    ...
  ]
}
```

**说明**: 提供日内每分钟的心率数据，可用于分析日常心率趋势。

### 3. HRV 数据（心率变异性）

**Endpoint**: `/hrv-service/hrv/YYYY-MM-DD`
**Method**: GET

**返回数据**:
```json
{
  "hrvSummary": {
    "calendarDate": "2026-03-25",
    "weeklyAvg": 65,
    "lastNightAvg": 72,
    "lastNight5MinHigh": 85,
    "baseline": {
      "lowUpper": 55,
      "balancedLow": 65,
      "balancedUpper": 85,
      "markerValue": 70
    },
    "status": "BALANCED",
    "feedbackPhrase": "Your HRV is within your normal range."
  },
  "hrvReadings": [
    {
      "hrvValue": 72,
      "readingTimeGmt": "2026-03-25T02:30:00Z",
      "readingTimeLocal": "2026-03-25T10:30:00+08:00"
    }
  ]
}
```

**说明**: 
- `lastNightAvg`: 夜间睡眠期间平均 HRV
- `weeklyAvg`: 最近7天平均 HRV
- `baseline`: 个人基线范围
- `status`: BALANCED/DETRAINED/UNBALANCED/LOW

### 4. 睡眠数据（含睡眠心率、血氧、呼吸）

**Endpoint**: `/wellness-service/wellness/dailySleepData/{username}`
**Method**: GET
**Parameters**: `date=YYYY-MM-DD&nonSleepBufferMinutes=60`

**返回数据**:
```json
{
  "dailySleepDTO": {
    "calendarDate": "2026-03-25",
    "sleepTimeSeconds": 28800,
    "deepSleepSeconds": 7200,
    "lightSleepSeconds": 14400,
    "remSleepSeconds": 7200,
    "awakeSleepSeconds": 1800,
    "averageSpO2Value": 98.5,
    "lowestSpO2Value": 95,
    "highestSpO2Value": 100,
    "averageRespirationValue": 14.2,
    "lowestRespirationValue": 12.0,
    "highestRespirationValue": 16.5,
    "avgSleepStress": 25.5
  }
}
```

**说明**: 
- 包含睡眠期间的血氧 (SpO2)
- 包含睡眠期间的呼吸频率
- 包含睡眠压力指数

### 5. Body Battery（身体电量）

**Endpoint**: `/bodybattery-service/bodybattery/daily`
**Method**: GET
**Parameters**: `date=YYYY-MM-DD`

**返回数据**:
```json
{
  "chargedValue": 85,
  "drainedValue": 65,
  "highestValue": 95,
  "lowestValue": 30,
  "endingValue": 65
}
```

**说明**: 反映身体能量储备，与心率变异性相关。

### 6. 压力数据

**Endpoint**: `/usersummary-service/stats/stress/daily/{start}/{end}`
**Method**: GET

**返回数据**:
```json
{
  "calendarDate": "2026-03-25",
  "overallStressLevel": 35,
  "restStressDuration": 480,
  "lowStressDuration": 600,
  "mediumStressDuration": 240,
  "highStressDuration": 60
}
```

**说明**: 压力数据基于心率变异性计算。

## garth 库支持情况

### 已封装的数据类型

| 数据类型 | 类名 | 方法 |
|---------|------|------|
| HRV 统计 | `DailyHRV` | `DailyHRV.list(end, period)` |
| HRV 详细 | `HRVData` | `HRVData.get(day)` |
| 睡眠 | `DailySleep` | `DailySleep.list(end, period)` |
| 睡眠详细 | `SleepData` | `SleepData.get(day)` |
| 压力 | `DailyStress` | `DailyStress.list(end, period)` |
| 步数 | `DailySteps` | `DailySteps.list(end, period)` |

### 需要直接调用 API 的数据

| 数据类型 | API Endpoint |
|---------|-------------|
| 静息心率 | `/wellness-service/wellness/dailyStats` |
| 全天候心率 | `/wellness-service/wellness/dailyHeartRate` |
| Body Battery | `/bodybattery-service/bodybattery/daily` |

## 心率数据分析建议

### 日常态心率指标

1. **静息心率 (Resting HR)**
   - 来源: `/wellness-service/wellness/dailyStats`
   - 正常范围: 50-80 bpm
   - 预警阈值: >100 或 <40

2. **夜间平均心率**
   - 来源: 睡眠数据中的心率统计
   - 正常范围: 比静息心率低 5-10 bpm
   - 可用于评估恢复状态

3. **HRV (心率变异性)**
   - 来源: `/hrv-service/hrv/{date}`
   - 关键指标: `lastNightAvg`（夜间平均）
   - 预警条件: 连续3天下降 >30%

4. **全天候心率趋势**
   - 来源: `/wellness-service/wellness/dailyHeartRate`
   - 可用于识别异常心率事件

### 数据整合建议

对于心率健康分析，建议整合以下数据：

```python
{
  "date": "2026-03-25",
  "resting_hr": 52,           # 静息心率
  "sleep_hr_avg": 48,         # 睡眠平均心率
  "hrv_last_night": 72,       # 夜间 HRV
  "hrv_status": "BALANCED",   # HRV 状态
  "body_battery_end": 65,     # 身体电量（晨起）
  "stress_level": 35,         # 压力水平
  "spo2_avg": 98.5,           # 睡眠血氧
  "respiration_avg": 14.2     # 睡眠呼吸频率
}
```

## 实现方案

### 脚本: `fetch_garmin_daily_health.py`

已创建脚本，支持获取：
1. 静息心率
2. 全天候心率趋势
3. HRV 数据
4. 睡眠数据（含血氧、呼吸）
5. Body Battery
6. 压力数据
7. 步数数据

### 使用方式

```bash
# 获取今日数据
python3 fetch_garmin_daily_health.py today

# 获取指定日期数据
python3 fetch_garmin_daily_health.py 2026-03-25

# 保存到文件
python3 fetch_garmin_daily_health.py today /path/to/output.json
```

### 数据存储建议

建议将数据存储到 Obsidian：

```
Areas/
  Health/
    Garmin/
      2026-03-25.md
```

文件格式：
```markdown
# Garmin 健康数据 - 2026-03-25

## 心率数据
- 静息心率: 52 bpm
- 睡眠平均心率: 48 bpm
- 全天最高心率: 145 bpm
- 全天最低心率: 42 bpm

## HRV
- 夜间平均: 72 ms
- 周平均: 68 ms
- 状态: BALANCED

## 睡眠
- 时长: 7.5 小时
- 血氧平均: 98.5%
- 呼吸频率: 14.2 次/分

## 身体电量
- 晨起: 65
- 最高: 95
- 最低: 30
```

## 限制与注意事项

1. **API 限流**: Garmin 对 API 调用有频率限制，建议缓存数据避免重复请求
2. **数据同步**: 确保 Garmin 设备已同步到 Connect 应用
3. **数据延迟**: 部分数据（如睡眠）可能有 15-30 分钟延迟
4. **权限**: 需要完整的 Garmin Connect 账号权限

## 后续优化建议

1. 添加数据缓存机制，避免重复请求
2. 支持批量获取历史数据
3. 与心率分析脚本集成，自动检测异常
4. 添加数据可视化（心率趋势图）
