# task-15-job-revision-audit

> 流水线 **15**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**历史修订审计 Job（RevisionAuditJob）**

## 负责什么（业务视角）

检测数据源对历史观测的修订（content_hash/revision_id 变化），写 revision log，触发局部 backfill 与「需重算」标记（Phase 1 步骤 6 标记，不执行 feature 重算）。

## 上下游

| 方向     | 谁                                                                               |
| -------- | -------------------------------------------------------------------------------- |
| **上游** | **task-05-raw-store**（历史 hash）· **task-10** 编排                             |
| **下游** | **task-12-job-backfill**（局部回补）· **task-18**（daily_close revision 子任务） |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §12.5 · §13.4.4

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（QualityJobRunner revision 路径）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
