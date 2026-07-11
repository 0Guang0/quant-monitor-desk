# task-12-job-backfill

> 流水线 **12**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**回补 Job（BackfillJob）**

## 负责什么（业务视角）

针对缺失日期、网络失败、节假日错位等按分片回补历史；受交易日 cap 约束，支持 resume，空分片不得拖死整单。

## 上下游

| 方向     | 谁                                                                        |
| -------- | ------------------------------------------------------------------------- |
| **上游** | **task-10-sync-orchestrator**                                             |
| **下游** | **task-17**（`data backfill`）· **task-18**（weekly_backfill 等 profile） |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §12.4 · §13.4.3

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（BackfillShardRunner）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
