# Strava Running Skill 技术方案

> 文档版本: 1.0
> 更新日期: 2026-03-28
> 状态: 设计中

---

## 1. 项目概述

### 1.1 目标

基于 Strava API 实现自动化的跑步数据抓取、分析和 Obsidian 笔记生成功能，与现有的 garmin-running skill 保持一致的用户体验。

### 1.2 核心功能

- 自动获取 Strava 最新跑步活动
- 7种训练类型智能分类（间歇、节奏、轻松、LSD、马拉松配速、恢复、跑步机）
- GPX 轨迹文件生成（从 streams 数据）
- Obsidian 结构化笔记生成
- 训练进度分析和对比

---

## 2. 技术选型

### 2.1 技术栈

| 组件 | 选型 | 版本 | 说明 |
|------|------|------|------|
| 语言 | Python | 3.9+ | 与 garmin-running 保持一致 |
| Strava API 库 | stravalib | 1.x | 官方推荐的 Python SDK |
| GPX 处理 | gpxpy | 1.6+ | 生成标准 GPX 文件 |
| 认证 | OAuth2 | - | refresh_token 机制 |

### 2.2 与 Garmin Skill 对比

| 对比项 | Garmin | Strava |
|--------|--------|--------|
| API 库 | garth | stravalib |
| 认证方式 | 邮箱+密码 | OAuth2 refresh_token |
| GPX 来源 | 原生下载 | 从 streams 生成 |
| 间歇训练 | 原生支持详细分段 | 仅计圈数据 |
| 跑步动态 | 支持步长/触地时间 | 不支持 |

---

## 3. 系统架构

### 3.1 架构图

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   User Input    │────▶│  strava-running      │────▶│  Obsidian       │
│  "节奏跑完了"    │     │     skill            │     │  Notes          │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   Strava API     │
                        │  (stravalib)     │
                        └──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌─────────────┐      ┌─────────────┐
            │   Activity  │      │   Streams   │
            │    Data     │      │    Data     │
            └─────────────┘      └─────────────┘
```

### 3.2 数据流

```
1. 用户输入 → 提取训练类型
2. Strava API → 获取最新活动列表 → 筛选跑步活动
3. 获取活动详情 → 获取 streams 数据
4. 数据转换 → 统一格式（兼容 garmin-running）
5. 生成 GPX（户外跑）
6. 分析数据 → 对比历史
7. 生成 Obsidian 笔记
```

---

## 4. 核心模块设计

### 4.1 模块结构

```
strava-running/
├── scripts/
│   ├── fetch_strava_run.py      # 数据获取主脚本
│   ├── generate_strava_note.py  # 笔记生成脚本
│   ├── oauth_helper.py          # OAuth 授权助手
│   └── export_activity.py       # 数据导出（调试）
├── references/
│   └── strava_config.json       # 配置文件
├── data/
│   └── gpx/                     # GPX 存储
└── docs/
    ├── strava-data-structure.md # 数据结构分析
    ├── technical-design.md      # 本文档
    └── implementation-plan.md   # 实现计划
```

### 4.2 核心类/函数设计

#### fetch_strava_run.py

```python
class StravaActivityFetcher:
    """Strava 活动数据获取器"""

    def __init__(self, config_path: str):
        self.client = self._authenticate()

    def _authenticate(self) -> Client:
        """OAuth2 认证"""
        pass

    def get_latest_run(self) -> Activity:
        """获取最新跑步活动"""
        pass

    def get_activity_streams(self, activity_id: int) -> Dict:
        """获取时间序列数据"""
        pass

    def get_activity_laps(self, activity_id: int) -> List[Lap]:
        """获取计圈数据"""
        pass

    def generate_gpx(self, activity: Activity, streams: Dict, output_dir: str) -> str:
        """生成 GPX 文件"""
        pass

    def analyze_activity(self, activity: Activity, streams: Dict, laps: List) -> Dict:
        """分析活动数据，返回统一格式"""
        pass
```

#### generate_strava_note.py

```python
class NoteGenerator:
    """Obsidian 笔记生成器"""

    TRAINING_TYPES = {
        '间歇跑': {...},
        '节奏跑': {...},
        # ... 7种类型
    }

    def generate_note(self, data: Dict, obsidian_path: str, user_input: str = None) -> str:
        """生成 Markdown 笔记"""
        pass

    def detect_training_type(self, activity_name: str, user_input: str) -> str:
        """智能识别训练类型"""
        pass

    def analyze_progress(self, data: Dict, training_type: str) -> Dict:
        """分析训练进度"""
        pass

    def analyze_hr_zones(self, avg_hr: float, max_hr: float) -> Dict:
        """分析心率区间"""
        pass
```

---

## 5. 数据模型

### 5.1 统一数据格式（兼容 garmin-running）

```python
{
    "activity_id": 17848143875,
    "activity_name": "Morning Run",
    "activity_type": "running",
    "date": "2026-03-25",
    "time": "08:22",
    "distance_km": 6.73,
    "duration": "33:34",
    "duration_seconds": 2014,
    "avg_pace": "4:59",
    "avg_hr": 157,
    "max_hr": 193,
    "calories": 450,
    "elevation_gain": 48.0,
    "avg_cadence": 93,
    "gpx_path": "/path/to/17848143875.gpx",  # 户外跑有，跑步机为 null
    "splits": [
        {
            "lap_number": 1,
            "distance_km": 1.0,
            "duration": "5:24",
            "pace": "5:23",
            "avg_hr": 155,
            "max_hr": 165,
        }
    ],
    "strava_data": {
        "average_watts": 271.5,
        "max_watts": 371,
        "has_heartrate": True,
        "suffer_score": 85,
        "streams_available": ["time", "latlng", "altitude", "heartrate", ...],
    }
}
```

### 5.2 Strava vs Garmin 字段映射

| Garmin 字段 | Strava 字段 | 转换逻辑 |
|-------------|-------------|----------|
| activityId | id | 直接映射 |
| activityName | name | 直接映射 |
| distance | distance | Garmin(m) → Strava(m) 相同 |
| duration | moving_time | timedelta → seconds |
| averageSpeed | average_speed | m/s 相同 |
| averageHR | average_heartrate | 直接映射 |
| maxHR | max_heartrate | 直接映射 |
| averageCadence | average_cadence | 直接映射 |
| calories | calories | 直接映射 |
| elevationGain | total_elevation_gain | 直接映射 |
| splits | splits_metric / laps | 需转换格式 |

---

## 6. 关键算法

### 6.1 配速计算

```python
def calculate_pace(meters_per_second: float) -> str:
    """m/s → min/km"""
    if not meters_per_second:
        return "N/A"
    seconds_per_km = 1000 / meters_per_second
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}"
```

### 6.2 跑步机识别

```python
def is_treadmill_run(activity: Activity) -> bool:
    """判断是否为跑步机/室内跑"""
    return activity.map is None or not activity.map.summary_polyline
```

### 6.3 GPX 生成（从 streams）

```python
def generate_gpx_from_streams(activity, streams):
    """从 Strava streams 生成 GPX"""
    if not streams.get('latlng'):
        return None  # 跑步机无 GPS

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    track.name = activity.name
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    # 按时间索引对齐数据
    for i, latlng in enumerate(streams['latlng'].data):
        point_time = activity.start_date_local + timedelta(
            seconds=streams['time'].data[i]
        )

        point = gpxpy.gpx.GPXTrackPoint(
            latitude=latlng[0],
            longitude=latlng[1],
            time=point_time,
            elevation=streams.get('altitude', {}).data[i]
                     if streams.get('altitude') else None
        )

        # 添加心率扩展
        if streams.get('heartrate'):
            hr = streams['heartrate'].data[i]
            # 添加 GPX 扩展...

        segment.points.append(point)

    return gpx.to_xml()
```

### 6.4 训练类型识别

```python
def detect_training_type(activity_name: str, user_input: str = None) -> str:
    """智能识别训练类型"""

    # 1. 从用户输入检测（优先级最高）
    if user_input:
        for type_name in TRAINING_TYPES.keys():
            if type_name in user_input:
                return type_name

    # 2. 从活动名称检测
    name_lower = activity_name.lower()
    keywords = {
        '间歇跑': ['间歇', 'interval'],
        '节奏跑': ['节奏', 'tempo'],
        'LSD': ['lsd', '长距离'],
        '轻松跑': ['轻松', 'easy'],
        '恢复跑': ['恢复', 'recovery'],
        '跑步机': ['跑步机', 'treadmill'],
        '马拉松配速跑': ['马拉松', 'marathon pace'],
    }

    for type_name, words in keywords.items():
        if any(word in name_lower for word in words):
            return type_name

    # 3. 默认
    return '轻松跑'
```

---

## 7. 错误处理策略

### 7.1 API 错误

| 错误类型 | 处理策略 |
|----------|----------|
| 401 Unauthorized | refresh_token 失效，提示重新授权 |
| 404 Not Found | 活动不存在或无权访问 |
| 429 Rate Limit | 等待 15 分钟后重试 |
| Network Error | 重试 3 次后失败 |

### 7.2 数据缺失

| 缺失类型 | 处理策略 |
|----------|----------|
| 无 GPS (跑步机) | GPX 设为 null，其他数据正常处理 |
| 无心率数据 | 显示 "N/A"，跳过心率分析 |
| 无步频数据 | 显示 "N/A" |
| 无功率数据 | 不显示功率相关字段 |

---

## 8. 配置管理

### 8.1 配置文件格式

```json
{
  "client_id": "75603",
  "client_secret": "c21644951d5f40965f1767658d6197186d47346e",
  "refresh_token": "cb7413daa783e4a2eeb18ae4c8abec94065809d2",
  "obsidian_path": "/Users/xuandao/Library/Mobile Documents/iCloud~md~obsidian/Documents/No.7/Areas/Running"
}
```

### 8.2 配置项说明

| 配置项 | 必填 | 说明 |
|--------|------|------|
| client_id | ✅ | Strava App Client ID |
| client_secret | ✅ | Strava App Client Secret |
| refresh_token | ✅ | OAuth refresh token |
| obsidian_path | ✅ | Obsidian 跑步笔记目录 |

---

## 9. 安全考虑

1. **Token 安全**: refresh_token 存储在本地配置文件，不提交到版本控制
2. **API 限流**: 遵守 Strava API 限流规则（默认 100 requests/15min）
3. **错误日志**: 日志中不输出完整的 token
4. **GPX 文件**: 包含位置敏感信息，仅本地存储

---

## 10. 参考资料

- [Strava API Documentation](https://developers.strava.com/docs/)
- [stravalib GitHub](https://github.com/stravalib/stravalib)
- [running_page 项目](https://github.com/yihong0618/running_page)
- [GPX Specification](https://www.topografix.com/gpx.asp)

---

## 11. 文档更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-28 | 初始版本 |
