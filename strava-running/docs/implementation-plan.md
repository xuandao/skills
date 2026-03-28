# Strava Running Skill 实现计划

> 文档版本: 2.0
> 更新日期: 2026-03-28
> 状态: 进行中

---

## 0. 开发规范（重要）

### 0.1 每个任务的必须要求

**所有任务必须满足以下三点要求：**

1. **数据验证** - 调用真实 Strava API 拉取数据进行验证
2. **单元测试** - 实现对应的单元测试
3. **Git 提交** - 完成后执行 git commit，方便后续回滚

### 0.2 任务执行流程模板

每个任务按以下流程执行：

```bash
# 1. 开始任务前，基于上一个任务的 commit 创建分支（可选）
git checkout -b phase1-task1-fix-units

# 2. 开发实现...
# 编辑代码

# 3. 调用 Strava API 进行数据验证
python3 scripts/test_task_name.py --verify-with-strava

# 4. 运行单元测试
python3 -m pytest tests/test_task_name.py -v

# 5. 全部通过后，提交代码
git add .
git commit -m "Phase X: 任务描述

- 实现功能: XXX
- 数据验证: 通过 Strava API 验证
- 单元测试: 覆盖 XX%
- 验证结果: 正常/问题说明"

# 6. 合并到主分支（可选）
git checkout master
git merge phase1-task1-fix-units
```

### 0.3 数据验证要求

- 必须使用真实 Strava API 调用进行验证
- 验证脚本需记录：活动ID、返回数据结构、关键字段值
- 跑步机活动和户外跑活动都需要验证
- 验证结果需保存在 `tests/verification/` 目录

### 0.4 单元测试要求

- 每个核心函数至少一个测试用例
- 包含正常情况和异常情况测试
- 测试覆盖率目标：70%+
- 使用 pytest 框架

### 0.5 Git Commit 规范

```
<Phase>: <任务简述>

- 实现内容: <详细描述>
- 数据验证: <验证结果摘要>
- 单元测试: <测试通过情况>
- 备注: <其他说明>
```

---

## 1. 开发阶段概览

```
Phase 1: 核心功能修复与测试 (1-2天)
Phase 2: GPX 生成实现 (2-3天)
Phase 3: 智能识别增强 (3-4天)
Phase 4: 进度分析功能 (2-3天)
Phase 5: 集成与优化 (2-3天)
─────────────────────────────────
总计: 10-15天
```

---

## 2. Phase 1: 核心功能修复与测试

**时间**: 第1-2天
**目标**: 完成端到端基础功能，可正常获取数据并生成笔记

### 2.1 任务清单

| 任务ID | 任务描述 | 数据验证 | 单元测试 | 状态 | 预计工时 |
|--------|----------|----------|----------|------|----------|
| P1-T1 | 修复 fetch_strava_run.py 单位转换问题 | ✅ 获取2条活动验证数值 | ✅ test_unit_conversion.py | ⏳ 待开始 | 2h |
| P1-T2 | 测试获取最新活动功能 | ✅ 获取最新5条活动 | ✅ test_fetch_latest.py | ⏳ 待开始 | 1h |
| P1-T3 | 测试 generate_strava_note.py 笔记生成 | ✅ 生成2条测试笔记 | ✅ test_note_generation.py | ⏳ 待开始 | 2h |
| P1-T4 | 添加 API 错误处理（401, 404, 429） | ✅ 模拟各错误场景 | ✅ test_error_handling.py | ⏳ 待开始 | 2h |
| P1-T5 | 添加网络超时和重试机制 | ✅ 模拟网络异常 | ✅ test_retry_mechanism.py | ⏳ 待开始 | 1h |
| P1-T6 | 端到端流程测试（获取→生成笔记） | ✅ 完整流程验证 | ✅ test_end_to_end.py | ⏳ 待开始 | 2h |

### 2.2 验收标准

- [ ] `fetch_strava_run.py` 可成功获取活动数据并输出 JSON
- [ ] `generate_strava_note.py` 可成功生成 Obsidian 笔记
- [ ] 401 错误时提示重新授权
- [ ] 网络错误时自动重试 3 次
- [ ] 跑步机活动正常处理（无 GPS）
- [ ] 户外跑活动正常处理（有 GPS）
- [ ] **所有任务都有对应的验证记录和单元测试**
- [ ] **每个任务完成后都有独立的 git commit**

### 2.3 数据验证脚本示例

```python
# tests/verification/test_p1_t1_units.py
"""P1-T1 数据验证：单位转换"""

from stravalib.client import Client
import json

def verify_unit_conversion():
    # 读取配置
    with open('references/strava_config.json') as f:
        config = json.load(f)

    # 认证
    client = Client()
    refresh = client.refresh_access_token(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        refresh_token=config['refresh_token']
    )
    client.access_token = refresh['access_token']

    # 获取最近2条活动验证
    activities = list(client.get_activities(limit=2))

    for act in activities:
        print(f"\n活动: {act.name}")
        print(f"  distance: {act.distance} (类型: {type(act.distance)})")
        print(f"  average_speed: {act.average_speed} (类型: {type(act.average_speed)})")

        # 测试转换
        speed = float(act.average_speed.magnitude
                      if hasattr(act.average_speed, 'magnitude')
                      else act.average_speed)
        print(f"  转换后速度: {speed} m/s")

if __name__ == '__main__':
    verify_unit_conversion()
```

### 2.4 单元测试示例

```python
# tests/unit/test_unit_conversion.py
import pytest
from scripts.fetch_strava_run import parse_speed

def test_parse_speed_with_units():
    """测试带单位的速度解析"""
    # 模拟带单位的对象
    class Quantity:
        magnitude = 3.34
    speed = parse_speed(Quantity())
    assert speed == 3.34

def test_parse_speed_float():
    """测试纯数值速度"""
    speed = parse_speed(3.34)
    assert speed == 3.34

def test_parse_speed_none():
    """测试空值处理"""
    speed = parse_speed(None)
    assert speed == 0.0
```

### 2.5 技术要点

**单位转换修复**:
```python
# 问题: stravalib 返回带单位的对象
# 解决: 提取原始数值
speed = float(activity.average_speed.magnitude
              if hasattr(activity.average_speed, 'magnitude')
              else activity.average_speed)
```

---

## 3. Phase 2: GPX 生成实现

**时间**: 第3-5天
**目标**: 从 Strava streams 数据生成标准 GPX 文件

### 3.1 任务清单

| 任务ID | 任务描述 | 数据验证 | 单元测试 | 状态 | 预计工时 |
|--------|----------|----------|----------|------|----------|
| P2-T1 | 实现 generate_gpx() 函数 | ✅ 生成2个活动GPX | ✅ test_gpx_generation.py | ⏳ 待开始 | 3h |
| P2-T2 | 支持心率数据写入 GPX 扩展 | ✅ 验证GPX包含心率 | ✅ test_gpx_hr_extension.py | ⏳ 待开始 | 2h |
| P2-T3 | 测试户外跑 GPX 生成质量 | ✅ 对比原数据 | ✅ test_gpx_quality.py | ⏳ 待开始 | 2h |
| P2-T4 | 验证 GPX 可被其他软件读取 | ✅ 导入Garmin/Strava | ✅ test_gpx_compatibility.py | ⏳ 待开始 | 1h |
| P2-T5 | 处理无 GPS 情况（跑步机） | ✅ 跑步机活动测试 | ✅ test_treadmill_handling.py | ⏳ 待开始 | 1h |

### 3.2 验收标准

- [ ] 户外跑活动可生成标准 GPX 文件
- [ ] GPX 文件包含时间、坐标、海拔、心率数据
- [ ] GPX 可被 Garmin Connect、Strava、Keep 等软件导入
- [ ] 跑步机活动不生成 GPX，但正常记录其他数据
- [ ] GPX 文件命名规范: `{activity_id}.gpx`
- [ ] **所有任务都有对应的验证记录和单元测试**
- [ ] **每个任务完成后都有独立的 git commit**

### 3.3 技术要点

**GPX 结构**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1"
     xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk>
    <name>Morning Run</name>
    <trkseg>
      <trkpt lat="31.2304" lon="121.4737">
        <ele>15.2</ele>
        <time>2026-03-25T08:22:28Z</time>
        <extensions>
          <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>145</gpxtpx:hr>
          </gpxtpx:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
```

---

## 4. Phase 3: 智能识别增强

**时间**: 第6-9天
**目标**: 提升训练类型识别的准确性

### 4.1 任务清单

| 任务ID | 任务描述 | 数据验证 | 单元测试 | 状态 | 预计工时 |
|--------|----------|----------|----------|------|----------|
| P3-T1 | 优化用户输入识别（支持更多关键词） | ✅ 多组输入测试 | ✅ test_input_detection.py | ⏳ 待开始 | 2h |
| P3-T2 | 实现活动名称智能推断 | ✅ 获取活动名称分析 | ✅ test_name_inference.py | ⏳ 待开始 | 2h |
| P3-T3 | 基于心率区间推断训练强度 | ✅ 分析历史心率数据 | ✅ test_hr_zone_analysis.py | ⏳ 待开始 | 3h |
| P3-T4 | 基于配速变化推断训练类型 | ✅ 获取splits分析 | ✅ test_pace_analysis.py | ⏳ 待开始 | 3h |
| P3-T5 | 综合决策算法（多因子判断） | ✅ 综合多组活动测试 | ✅ test_multi_factor_decision.py | ⏳ 待开始 | 4h |

### 4.2 验收标准

- [ ] 用户输入 "节奏跑完了" 正确识别为节奏跑
- [ ] 用户输入 "跑了个间歇" 正确识别为间歇跑
- [ ] 活动名称包含 "LSD" 正确识别为 LSD
- [ ] 心率高+配速快 识别为间歇跑
- [ ] 心率低+配速慢 识别为恢复跑
- [ ] **所有任务都有对应的验证记录和单元测试**
- [ ] **每个任务完成后都有独立的 git commit**

### 4.3 心率区间算法

```python
def analyze_hr_zones(avg_hr, max_hr):
    """基于心率区间判断训练强度"""
    # 假设最大心率 190
    hr_max = max_hr or 190

    zones = {
        'zone1': (0.5 * hr_max, 0.6 * hr_max),  # 恢复
        'zone2': (0.6 * hr_max, 0.7 * hr_max),  # 轻松
        'zone3': (0.7 * hr_max, 0.8 * hr_max),  # 马拉松配速
        'zone4': (0.8 * hr_max, 0.9 * hr_max),  # 乳酸阈值
        'zone5': (0.9 * hr_max, hr_max),        # 无氧
    }

    # 根据平均心率判断主要训练区间
    # 返回对应的训练类型建议
```

---

## 5. Phase 4: 进度分析功能

**时间**: 第10-12天
**目标**: 实现与 garmin-running 一致的进度分析

### 5.1 任务清单

| 任务ID | 任务描述 | 数据验证 | 单元测试 | 状态 | 预计工时 |
|--------|----------|----------|----------|------|----------|
| P4-T1 | 实现历史数据读取 | ✅ 读取现有笔记 | ✅ test_history_read.py | ⏳ 待开始 | 2h |
| P4-T2 | 实现同类型训练对比 | ✅ 对比2次活动 | ✅ test_same_type_compare.py | ⏳ 待开始 | 2h |
| P4-T3 | 添加配速趋势分析 | ✅ 分析趋势数据 | ✅ test_pace_trend.py | ⏳ 待开始 | 2h |
| P4-T4 | 添加心率趋势分析 | ✅ 分析心率趋势 | ✅ test_hr_trend.py | ⏳ 待开始 | 2h |
| P4-T5 | 生成本月训练统计 | ✅ 统计本月数据 | ✅ test_monthly_stats.py | ⏳ 待开始 | 3h |

### 5.2 验收标准

- [ ] 可与上次同类型训练对比配速
- [ ] 可与上次同类型训练对比心率
- [ ] 可统计本月总距离、总时间、训练次数
- [ ] 可统计各训练类型分布
- [ ] 可识别个人最佳成绩（PB）
- [ ] **所有任务都有对应的验证记录和单元测试**
- [ ] **每个任务完成后都有独立的 git commit**

### 5.3 数据结构

```python
# 历史数据读取
history = []
for filename in os.listdir(type_folder):
    if filename.endswith('.md'):
        # 解析 frontmatter
        record = parse_frontmatter(filepath)
        history.append(record)

# 对比逻辑
last_run = history[-1]
pace_diff = current_pace - last_run['pace']
distance_diff = current_distance - last_run['distance']
```

---

## 6. Phase 5: 集成与优化

**时间**: 第13-15天
**目标**: 与 garmin-running 保持一致体验，完成文档

### 6.1 任务清单

| 任务ID | 任务描述 | 数据验证 | 单元测试 | 状态 | 预计工时 |
|--------|----------|----------|----------|------|----------|
| P5-T1 | 与 garmin-running 数据格式对比 | ✅ 对比2个活动 | ✅ test_format_compat.py | ⏳ 待开始 | 2h |
| P5-T2 | 统一笔记模板格式 | ✅ 生成对比笔记 | ✅ test_note_template.py | ⏳ 待开始 | 2h |
| P5-T3 | 批量导入历史活动功能 | ✅ 批量导入5条 | ✅ test_batch_import.py | ⏳ 待开始 | 4h |
| P5-T4 | 添加单元测试 | ✅ 测试覆盖70%+ | ✅ test_suite.py | ⏳ 待开始 | 3h |
| P5-T5 | 完善 SKILL.md 文档 | - | - | ⏳ 待开始 | 2h |
| P5-T6 | 添加使用示例 | - | - | ⏳ 待开始 | 1h |

### 6.2 验收标准

- [ ] strava-running 和 garmin-running 生成的笔记格式一致
- [ ] 支持批量导入历史活动
- [ ] 核心函数有单元测试覆盖
- [ ] SKILL.md 文档完整，包含使用示例
- [ ] 通过完整功能测试
- [ ] **所有任务都有对应的验证记录和单元测试**
- [ ] **每个任务完成后都有独立的 git commit**

---

## 7. 当前进度

### 7.1 已完成

| 任务 | 完成时间 | 备注 | Commit |
|------|----------|------|--------|
| 基础目录结构 | 2026-03-28 | ✅ | - |
| 配置文件模板 | 2026-03-28 | ✅ | - |
| OAuth 授权流程 | 2026-03-28 | ✅ 已获取有效 token | - |
| 数据获取脚本框架 | 2026-03-28 | ✅ 待修复单位转换 | - |
| 笔记生成脚本框架 | 2026-03-28 | ✅ | - |
| 数据结构分析文档 | 2026-03-28 | ✅ | - |
| 技术方案文档 | 2026-03-28 | ✅ | - |
| SKILL.md 中文描述 | 2026-03-28 | ✅ | - |
| 实现计划文档 v2.0 | 2026-03-28 | ✅ | - |

### 7.2 进行中

| 任务 | 开始时间 | 预计完成 | 阻塞项 | Commit |
|------|----------|----------|--------|--------|
| P1-T1: 修复单位转换 | - | - | 待开始 | - |

### 7.3 待开始

- Phase 1 其他任务
- Phase 2-5 全部任务

---

## 8. 风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| Strava API 限流 | 高 | 中 | 添加请求间隔，缓存数据 |
| refresh_token 过期 | 高 | 中 | 提供重新授权脚本 |
| GPS 数据不完整 | 中 | 低 | 优雅降级，跳过 GPX 生成 |
| 与 garmin 数据差异大 | 中 | 中 | 统一数据转换层 |

---

## 9. 下一步行动

**建议立即开始**: Phase 1 - 修复单位转换问题

具体任务:
1. 修复 `fetch_strava_run.py` 中的 pint 单位转换
2. **数据验证**: 获取2条活动验证数值转换正确
3. **单元测试**: 实现 test_unit_conversion.py
4. **Git Commit**: 提交代码并记录验证结果

预计耗时: **半天**
阻塞后续: **是**

---

## 10. 附录

### 10.1 文件清单

```
strava-running/
├── SKILL.md                              # Skill 定义
├── references/
│   └── strava_config.json                # 配置文件（敏感）
├── scripts/
│   ├── fetch_strava_run.py               # 数据获取（待修复）
│   ├── generate_strava_note.py           # 笔记生成
│   ├── oauth_helper.py                   # OAuth 助手
│   ├── export_activity.py                # 数据导出
│   └── analyze_strava_activities.py      # 活动分析
├── data/
│   └── gpx/                              # GPX 存储（待实现）
├── tests/
│   ├── verification/                     # 数据验证脚本
│   │   ├── test_p1_t1_units.py
│   │   ├── test_p1_t2_fetch.py
│   │   └── ...
│   └── unit/                             # 单元测试
│       ├── test_unit_conversion.py
│       ├── test_fetch.py
│       └── ...
└── docs/
    ├── strava-data-structure.md          # 数据结构分析 ✅
    ├── technical-design.md               # 技术方案 ✅
    └── implementation-plan.md            # 本文件 ✅
```

### 10.2 目录结构创建命令

```bash
mkdir -p strava-running/tests/{verification,unit}
```

### 10.3 参考文档

- [strava-data-structure.md](./strava-data-structure.md) - 数据结构详细分析
- [technical-design.md](./technical-design.md) - 技术设计方案

---

## 11. 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.0 | 2026-03-28 | 增加数据验证、单元测试、Git Commit 要求；更新 SKILL.md 为中文描述 |
| 1.0 | 2026-03-28 | 初始版本，规划 Phase 1-5 |
