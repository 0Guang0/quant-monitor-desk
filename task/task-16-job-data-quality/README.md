# task-16-job-data-quality

> 流水线 **16**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据质量巡检 Job（DataQualityJob）**

## 负责什么（业务视角）

按 domain/profile 对已入库或 staging 数据做巡检，必须调用 **task-07** 的 DataQualityValidator，禁止 COUNT 行假完成。

## 上下游

| 方向     | 谁                                                                 |
| -------- | ------------------------------------------------------------------ |
| **上游** | **task-07-data-quality-validator**（校验器本体）· **task-10** 编排 |
| **下游** | **task-18-scheduler**（daily_close data_quality 子任务）           |

## 权威设计

- `MIGRATION_MAP.md` → data_sync_orchestrator.md §13.4.6 · PHASE1_PRD §162

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（QualityJobRunner data_quality 路径）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
