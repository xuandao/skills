# Strava 数据结构分析报告

> 分析时间: 2026-03-28
> 数据来源: xuandaooo w. 的最近5条 Strava 活动
> 设备: Garmin Forerunner 965

---

## 1. 活动概览样本

| # | 日期 | 名称 | 距离 | 配速 | 心率(avg/max) | GPS | 设备 |
|---|------|------|------|------|---------------|-----|------|
| 1 | 03-25 | Morning Run | 6.73 km | 4:59/km | 157/193 bpm | ❌ | Garmin 965 |
| 2 | 03-23 | Morning Run | 5.01 km | 6:16/km | 132/140 bpm | ❌ | Garmin 965 |
| 3 | 03-22 | 无锡半程马拉松 | 21.36 km | 4:44/km | 182/196 bpm | ✅ | Garmin 965 |
| 4 | 03-18 | Morning Run | 5.24 km | 5:13/km | 151/182 bpm | ❌ | Garmin 965 |
| 5 | 03-16 | Afternoon Run | 7.15 km | 5:37/km | 160/173 bpm | ✅ | Garmin 965 |

---

## 2. 可用数据字段详解

### 2.1 基础数据（始终可用）

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| `id` | int | 17848143875 | 活动ID |
| `name` | str | "Morning Run" | 活动名称 |
| `type` | str | "Run" | 活动类型 |
| `distance` | float | 6730.0 | 距离（米） |
| `moving_time` | timedelta | 0:33:34 | 移动时间 |
| `elapsed_time` | timedelta | 0:33:34 | 总用时（含暂停）|
| `start_date_local` | datetime | 2026-03-25 08:22:28 | 本地开始时间 |
| `timezone` | str | "Asia/Shanghai" | 时区 |
| `calories` | float | 450.0 | 卡路里消耗 |
| `has_heartrate` | bool | True | 是否有心率数据 |
| `suffer_score` | int | 85 | 痛苦指数（相对努力程度）|

### 2.2 心率数据（设备支持时）

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| `average_heartrate` | float | 157.0 | 平均心率 (bpm) |
| `max_heartrate` | float | 193.0 | 最大心率 (bpm) |

**注意**: 取决于设备是否支持心率监测。

### 2.3 跑步数据（设备支持时）

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| `average_speed` | float | 3.34 | 平均速度 (m/s) |
| `max_speed` | float | 4.25 | 最大速度 (m/s) |
| `average_cadence` | float | 93.0 | 平均步频 (spm) |

**配速计算**:
```python
pace_sec_per_km = 1000 / average_speed  # 秒/公里
pace_min = int(pace_sec_per_km // 60)
pace_sec = int(pace_sec_per_km % 60)
# 结果: 4:59/km
```

### 2.4 功率数据（Garmin 965 支持）

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| `average_watts` | float | 271.5 | 平均功率 (W) |
| `max_watts` | float | 371.0 | 最大功率 (W) |
| `kilojoules` | float | 580.0 | 能量消耗 (kJ) |

**注意**: 大多数跑步设备不支持功率数据，Garmin 965 支持。

### 2.5 海拔数据（户外跑）

| 字段 | 类型 | 示例值 | 说明 |
|------|------|--------|------|
| `total_elevation_gain` | float | 48.0 | 累计爬升 (米) |

**注意**: 跑步机无此数据，户外跑有。

### 2.6 GPS 数据

```python
# 判断是否有 GPS 数据
has_gps = activity.map is not None and activity.map.summary_polyline is not None

# GPS 数据结构
activity.map = {
    'id': 'a123456789',
    'summary_polyline': 'polyline_encoded_string',
    'resource_state': 2
}
```

**用途**:
- `summary_polyline` 可用于显示地图轨迹
- 为空时表明是跑步机/室内跑

---

## 3. GPS vs 跑步机判断

```python
def is_treadmill_run(activity):
    """判断是否为跑步机/室内跑"""
    return activity.map is None or not activity.map.summary_polyline

# 测试结果:
# - 活动 1, 2, 4: 跑步机 (map = None)
# - 活动 3, 5: 户外跑 (map.summary_polyline 有值)
```

---

## 4. 高级数据结构

### 4.1 最佳成绩 (best_efforts)

系统自动计算的各距离最佳用时：

```python
best_efforts = [
    {'name': '400m', 'elapsed_time': timedelta(seconds=107)},     # 1:47
    {'name': '1/2 mile', 'elapsed_time': timedelta(seconds=219)}, # 3:39
    {'name': '1K', 'elapsed_time': timedelta(seconds=274)},       # 4:34
    {'name': '1 mile', 'elapsed_time': timedelta(seconds=441)},   # 7:21
    {'name': '2 mile', 'elapsed_time': timedelta(seconds=887)},   # 14:47
    # ... 可能还有 5K, 10K, 半程马拉松, 全程马拉松等
]
```

### 4.2 公里分段 (splits_metric)

每公里的详细数据：

```python
splits_metric = [
    {
        'split': 1,                          # 第1公里
        'elapsed_time': timedelta(seconds=324),  # 用时 5:24
        'distance': 1000.0,                  # 距离 1000米
        'elevation_difference': 2.5,         # 海拔变化
        'average_speed': 3.09                # 平均速度 m/s
    },
    # ... 每条记录代表1公里
]
```

**配速计算**:
```python
for split in splits_metric:
    pace_min = int(1000 / split.average_speed / 60)
    pace_sec = int(1000 / split.average_speed % 60)
    print(f"第{split.split}公里: {pace_min}:{pace_sec:02d}/km")
```

### 4.3 计圈数据 (laps)

通过 `client.get_activity_laps(activity_id)` 获取：

```python
laps = [
    {
        'lap_index': 1,
        'distance': 1000.0,                  # 米
        'elapsed_time': timedelta(seconds=300),
        'moving_time': timedelta(seconds=295),
        'average_speed': 3.33,               # m/s
        'average_heartrate': 155.0,
        'max_heartrate': 165.0,
        'average_cadence': 170.0,
        'total_elevation_gain': 10.0,
    },
    # ...
]
```

---

## 5. Streams 时间序列数据

通过 `client.get_activity_streams()` 获取详细时间序列：

```python
streams = client.get_activity_streams(
    activity_id,
    types=['time', 'latlng', 'altitude', 'heartrate', 'distance', 'cadence', 'watts']
)

# 数据结构:
{
    'time': StreamObject(data=[0, 1, 2, 3, ...]),           # 秒偏移
    'latlng': StreamObject(data=[[31.23, 121.47], ...]),    # [纬度, 经度]
    'altitude': StreamObject(data=[15.2, 15.3, ...]),       # 海拔(米)
    'heartrate': StreamObject(data=[145, 146, 148, ...]),   # 心率(bpm)
    'distance': StreamObject(data=[0.0, 3.2, 6.8, ...]),    # 累计距离(米)
    'cadence': StreamObject(data=[168, 170, 172, ...]),     # 步频(spm)
    'watts': StreamObject(data=[250, 255, 260, ...]),       # 功率(W)
}
```

**注意**:
- 所有 stream 数组长度相同，按索引对齐
- 跑步机无 `latlng` 和 `altitude` 数据
- 心率/步频/功率取决于设备支持

---

## 6. 数据对比: 跑步机 vs 户外跑

| 数据类型 | 跑步机 | 户外跑 | 说明 |
|----------|--------|--------|------|
| 基础信息 | ✅ | ✅ | 全部可用 |
| 心率数据 | ✅ | ✅ | 需设备支持 |
| 步频数据 | ✅ | ✅ | 需设备支持 |
| 功率数据 | ✅ | ✅ | 需设备支持 |
| GPS/地图 | ❌ | ✅ | 通过 map 判断 |
| 爬升/海拔 | ❌ | ✅ | 户外才有 |
| 最佳成绩 | ✅ | ✅ | 自动计算 |
| 公里分段 | ✅ | ✅ | 自动计算 |
| Streams | ⚠️ | ⚠️ | 需额外调用 |

---

## 7. 与 Garmin Connect 对比

| 功能 | Garmin | Strava |
|------|--------|--------|
| **间歇训练标记** | ✅ 详细（热身/跑步/休息） | ⚠️ 无，需手动推断 |
| **跑步动态** | ✅ 步长/触地时间/垂直振幅 | ❌ 不支持 |
| **GPX 下载** | ✅ 原生支持 | ⚠️ 需从 streams 生成 |
| **心率区间** | ✅ 详细 | ⚠️ 需自行计算 |
| **设备信息** | ✅ 详细 | ✅ 设备名称 |
| **认证方式** | 邮箱+密码 | OAuth2 |
| **API 限制** | 较严格 | 较宽松 |

---

## 8. 数据满足度评估

| 需求 | 支持度 | 说明 |
|------|--------|------|
| 基础跑步数据 | ✅ | 距离、时间、配速、卡路里 |
| 心率分析 | ✅ | 平均/最大心率 + 区间分析 |
| 步频数据 | ✅ | average_cadence |
| 功率数据 | ✅ | 平均/最大功率（965支持）|
| 跑步机识别 | ✅ | 通过 map == None 判断 |
| 爬升/海拔 | ✅ | 户外跑有数据 |
| GPX 生成 | ✅ | 从 streams 生成（户外）|
| 公里分段 | ✅ | splits_metric |
| 最佳成绩 | ✅ | best_efforts |
| 间歇训练识别 | ⚠️ | 需从名称或用户输入推断 |

---

## 9. 关键代码片段

### 9.1 单位转换

```python
def format_pace(meters_per_second):
    """将 m/s 转换为 min/km"""
    if not meters_per_second:
        return "N/A"
    seconds_per_km = 1000 / meters_per_second
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"

# 处理可能的单位对象
speed = float(activity.average_speed.magnitude if hasattr(activity.average_speed, 'magnitude') else activity.average_speed)
```

### 9.2 判断跑步机

```python
def is_treadmill(activity):
    return activity.map is None or not getattr(activity.map, 'summary_polyline', None)
```

### 9.3 生成 GPX

```python
# 从 streams 生成 GPX
def generate_gpx_from_streams(activity, streams, output_path):
    if not streams.get('latlng'):
        return None  # 跑步机无 GPS

    # 创建 GPX 轨迹...
```

---

## 10. 参考资料

- Strava API 文档: https://developers.strava.com/docs/reference/
- stravalib 库: https://github.com/stravalib/stravalib
- running_page 项目: https://github.com/yihong0618/running_page

---

## 11. 更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-03-28 | 初始版本，基于5条活动数据分析 |
