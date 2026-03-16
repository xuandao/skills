# skills-sync

自动将 workspace skills 同步到远程仓库。

## 功能

1. 将 `/Users/xuandao/.openclaw/workspace/skills` 全量复制到 `/Users/xuandao/work/xuandao/skills`
2. 提交并推送到远程仓库

## 触发方式

- Cron 定时任务调用
- 手动执行：说"执行 skills 同步"

## 实现

使用 rsync 全量覆盖复制，然后执行 git 提交推送。
