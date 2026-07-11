# task-11-job-incremental

> 流水线 **11**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**增量同步 Job（IncrementalUpdateJob）**

## 负责什么（业务视角）

日常默认路径：按 cursor/watermark 只补新增或变化的数据，禁止每天无差别全量重抓；重复运行不产生重复主键。

## 上下游

| 方向     | 谁                                                                                        |
| -------- | ----------------------------------------------------------------------------------------- |
| **上游** | **task-10-sync-orchestrator**（状态机与管线接缝）                                         |
| **下游** | **task-17-cli-data-commands**（`data sync`）· **task-18-scheduler**（daily_close 子任务） |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §12.3

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（IncrementalJobRunner）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
