# Strava Running Skill 测试指南

## 目录结构

```
tests/
├── verification/          # 数据验证脚本（调用真实 Strava API）
│   ├── test_p1_t1_units.py
│   └── ...
├── unit/                  # 单元测试（本地运行，不依赖 API）
│   ├── test_p1_t1_unit_conversion.py
│   └── ...
└── README.md             # 本文件
```

## 开发流程

每个任务必须执行以下三步验证：

### 1. 数据验证（调用 Strava API）

```bash
python3 tests/verification/test_p1_t1_units.py
```

- 使用真实 Strava 数据验证功能
- 验证结果记录在脚本输出中

### 2. 单元测试（本地测试）

```bash
# 运行单个测试文件
python3 -m pytest tests/unit/test_p1_t1_unit_conversion.py -v

# 运行所有单元测试
python3 -m pytest tests/unit/ -v

# 生成覆盖率报告
python3 -m pytest tests/unit/ --cov=scripts --cov-report=html
```

### 3. Git Commit

```bash
# 提交代码

git add .
git commit -m "Phase X Task Y: 任务描述

- 实现内容: XXX
- 数据验证: 通过 Strava API 验证（活动ID: XXX）
- 单元测试: 13个测试用例全部通过
- 验证结果: 正常"
```

## 当前测试任务

### Phase 1: 核心功能修复与测试

| 任务 | 验证脚本 | 单元测试 | 状态 |
|------|----------|----------|------|
| P1-T1: 单位转换修复 | test_p1_t1_units.py | test_p1_t1_unit_conversion.py | ✅ 就绪 |
| P1-T2: 获取最新活动 | test_p1_t2_fetch.py | test_p1_t2_fetch.py | ⏳ 待创建 |
| P1-T3: 笔记生成 | test_p1_t3_note.py | test_p1_t3_note.py | ⏳ 待创建 |
| P1-T4: API 错误处理 | test_p1_t4_errors.py | test_p1_t4_errors.py | ⏳ 待创建 |
| P1-T5: 网络重试 | test_p1_t5_retry.py | test_p1_t5_retry.py | ⏳ 待创建 |
| P1-T6: 端到端测试 | test_p1_t6_e2e.py | test_p1_t6_e2e.py | ⏳ 待创建 |

## 创建新测试模板

### 数据验证脚本模板

```python
#!/usr/bin/env python3
"""
Phase X Task Y 数据验证脚本

运行方式:
    python3 tests/verification/test_px_ty_feature.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stravalib.client import Client


def verify_feature():
    """验证功能"""
    print("=" * 70)
    print("Phase X Task Y: 功能验证")
    print("=" * 70)

    # 读取配置
    config_path = Path(__file__).parent.parent.parent / "references" / "strava_config.json"
    with open(config_path) as f:
        config = json.load(f)

    # 认证
    client = Client()
    refresh = client.refresh_access_token(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        refresh_token=config['refresh_token']
    )
    client.access_token = refresh['access_token']

    # TODO: 实现验证逻辑
    print("验证通过!")
    return True


if __name__ == '__main__':
    success = verify_feature()
    sys.exit(0 if success else 1)
```

### 单元测试模板

```python
#!/usr/bin/env python3
"""
Phase X Task Y 单元测试

运行方式:
    python3 -m pytest tests/unit/test_px_ty_feature.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFeature:
    """测试功能"""

    def test_normal_case(self):
        """测试正常情况"""
        assert True

    def test_edge_case(self):
        """测试边界情况"""
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

## 注意事项

1. **API 限流**: Strava API 有请求限制（默认 100 requests/15min），数据验证脚本应控制请求频率
2. **敏感信息**: 不要将 `references/strava_config.json` 提交到 Git
3. **测试数据**: 单元测试使用模拟数据，不依赖真实 API
4. **验证记录**: 每次数据验证应记录验证的活动 ID 和关键字段值

## 参考文档

- [implementation-plan.md](../docs/implementation-plan.md) - 完整实现计划
- [technical-design.md](../docs/technical-design.md) - 技术设计方案
