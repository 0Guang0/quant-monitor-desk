# task-13-job-full-load

> 流水线 **13**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**全量初始化 Job（FullLoadJob）**

## 负责什么（业务视角）

建库或重大重建时的初始化全量：日历、历史日线、基础映射等；非日常默认路径，须与用户确认范围。

## 上下游

| 方向     | 谁                              |
| -------- | ------------------------------- |
| **上游** | **task-10-sync-orchestrator**   |
| **下游** | **task-17**（`data full-load`） |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §12.2

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（FullLoadJobRunner）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
