# 长桥证券月结单定时任务

## ✅ 已配置（OpenClaw Cron）

**定时任务**: 每月6号上午9:00自动拉取上月月结单并分析

**任务ID**: `aba551ff-db17-4567-af33-a70ff73f2710`

**管理界面**: http://localhost:18789/cron

**配置详情**:
```json
{
  "name": "长桥月结单分析",
  "description": "每月6号自动拉取上月月结单并分析",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 6 * *",
    "tz": "Asia/Shanghai"
  },
  "delivery": {
    "mode": "announce",
    "channel": "last"
  }
}
```

## 📅 运行时间

- **频率**: 每月6号
- **时间**: 上午9:00
- **原因**: 长桥通常在每月5号发送上月月结单，6号拉取确保邮件已到达

## 📊 自动化流程

1. **9:00** - Cron 触发脚本
2. **搜索邮件** - 从 Gmail 搜索最新月结单
3. **下载解密** - 下载 PDF 并解密
4. **分析数据** - 提取持仓、盈亏等信息
5. **生成报告** - 保存到 Obsidian `Areas/理财/长桥/YYYYMM-长桥月度结单分析.md`
6. **记录日志** - 输出到 `~/Library/Logs/longbridge-monthly.log`

## 📝 查看和管理

### Web UI（推荐）
```
http://localhost:18789/cron
```

### 命令行
```bash
# 查看所有任务
openclaw cron list

# 查看任务详情
openclaw cron list --json | jq '.[] | select(.name == "长桥月结单分析")'

# 手动运行一次（测试）
openclaw cron run aba551ff-db17-4567-af33-a70ff73f2710

# 查看运行历史
openclaw cron runs aba551ff-db17-4567-af33-a70ff73f2710

# 禁用任务
openclaw cron disable aba551ff-db17-4567-af33-a70ff73f2710

# 启用任务
openclaw cron enable aba551ff-db17-4567-af33-a70ff73f2710

# 删除任务
openclaw cron rm aba551ff-db17-4567-af33-a70ff73f2710
```

## 🧪 测试定时任务

```bash
# 手动运行一次（通过 OpenClaw）
openclaw cron run aba551ff-db17-4567-af33-a70ff73f2710

# 或直接运行脚本
python3 ~/.openclaw/workspace/skills/longbridge-statement/scripts/longbridge-monthly-analysis.py
```

## 🔧 管理定时任务

### 查看任务
```bash
openclaw cron list
# 或访问 http://localhost:18789/cron
```

### 编辑任务
```bash
openclaw cron edit aba551ff-db17-4567-af33-a70ff73f2710 --description "新的描述"
```

### 禁用/启用
```bash
# 临时禁用
openclaw cron disable aba551ff-db17-4567-af33-a70ff73f2710

# 重新启用
openclaw cron enable aba551ff-db17-4567-af33-a70ff73f2710
```

### 删除任务
```bash
openclaw cron rm aba551ff-db17-4567-af33-a70ff73f2710
```

## ⚠️ 注意事项

1. **OpenClaw Gateway 必须运行**
   - 确保 Gateway 服务正在运行：`openclaw gateway status`
   - 如果未运行：`openclaw gateway start`

2. **通知方式**
   - 任务完成后会通过 `--channel last` 发送通知
   - 可以在 Web UI 查看运行历史

3. **时区**
   - 使用 Asia/Shanghai 时区
   - 9:00 AM = 北京时间上午9点

4. **邮件延迟**
   - 如果6号9点邮件还未到达，任务会失败
   - 可以手动运行或等待下月自动重试

5. **错误处理**
   - 查看运行历史：`openclaw cron runs <task-id>`
   - 查看详细日志：Web UI 中点击任务查看

## 📊 预期输出

每月6号运行后，会在 Obsidian 中生成：

```
Areas/理财/长桥/202603-长桥月度结单分析.md
Areas/理财/长桥/202604-长桥月度结单分析.md
...
```

报告格式与 202602 完全一致，包含：
- 账户概况
- 持仓明细
- 月度资金流水
- 风险分析
- 操作建议

## 🎯 下次运行

- **2026年4月6日 09:00** - 分析2026年3月月结单
- **2026年5月6日 09:00** - 分析2026年4月月结单
- ...

---

**配置时间**: 2026-03-07 20:20  
**配置人**: DaoBot (OpenClaw)
