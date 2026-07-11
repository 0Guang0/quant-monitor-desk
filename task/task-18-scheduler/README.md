# task-18-scheduler

> 流水线 **18**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**调度器（Scheduler / sync_scheduler_profiles）**

## 负责什么（业务视角）

按 profile（`daily_close` · `weekly_backfill`）展开子 job，parent 诚实聚合 child 的 AcceptanceReport；禁止 synthetic PASS。

## 上下游

| 方向     | 谁                                                                |
| -------- | ----------------------------------------------------------------- |
| **上游** | **task-17-cli-data-commands**（命令语义）· **task-11～16** 各 Job |
| **下游** | **task-19-phase1-gate**（整单 `daily_close` 关账复验）            |

## 权威设计

- `MIGRATION_MAP.md` → specs/layer1_axes/sync_scheduler_profiles.yaml · data_sync_orchestrator.md §13.6

## 代码主区（实现时收窄）

```text
backend/app/sync/scheduler.py · data_commands.scheduler_run
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
