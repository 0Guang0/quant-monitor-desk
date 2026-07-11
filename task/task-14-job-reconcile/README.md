# task-14-job-reconcile

> 流水线 **14**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**冲突重抓 Job（ReconcileJob）**

## 负责什么（业务视角）

当 `source_conflict` 严重级别触发时，对主源/备源重新抓取并再比较；仍无法解决则 escalation 到人工确认，禁止悄悄写 clean。

## 上下游

| 方向     | 谁                                                                  |
| -------- | ------------------------------------------------------------------- |
| **上游** | **task-08-source-conflict-validator**（冲突记录）· **task-10** 编排 |
| **下游** | 回到 **task-06～09** 管线重跑 · **task-18** 调度触发                |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §12.6

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（ReconcileJobRunner）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
