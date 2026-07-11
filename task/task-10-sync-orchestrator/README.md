# task-10-sync-orchestrator

> 流水线 **10**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据同步编排核心（DataSyncOrchestrator）**

## 负责什么（业务视角）

后台任务总控：创建 job、维护 CREATED→COMPLETED 状态机、把 task-04～09 的管线步骤串成一次同步运行，写 `data_sync_job` 与 job 事件。不负责具体 vendor 解析，也不直接写 clean（委托 WriteManager）。

## 上下游

| 方向     | 谁                                                        |
| -------- | --------------------------------------------------------- |
| **上游** | **task-04～09** 全部流水线组件（已各自 R4）               |
| **下游** | **task-11～16** 六类 Job Runner · **task-17/18** 正式入口 |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_sync_orchestrator.md`、`docs/ops/design/idempotency_retry_dlq_policy.md`、`docs/ops/design/lock_and_concurrency_policy.md`、`docs/architecture/design/03_runtime_flows.md`、`specs/contracts/design/runtime_flow_contract.yaml`、`docs/modules/design/write_manager.md`、`docs/modules/design/data_validation_and_conflict.md`、`docs/modules/design/duckdb_and_parquet.md`、`docs/modules/design/data_sources.md`、`docs/architecture/design/04_data_architecture.md`、`docs/architecture/design/module_boundary_matrix.md`、`docs/modules/design/ops_and_performance.md`、`docs/ops/design/logs_health_audit.md`、`docs/ops/design/ERROR_CODE_GUIDE.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据同步域 文件1/2/3/4/6 → 全文）：本票管 **DataSyncOrchestrator 核心**：job 创建、`CREATED→COMPLETED` 状态机、`data_sync_job` / `job_event_log`、断点续跑（§13.9）、幂等键与重试（`idempotency_retry_dlq_policy.md`）；串联 task-04～09，**不**直接写 clean（委托 WriteManager）、**不**解析 vendor 细节。**六类 Job Runner 实现细节归 task-11～16**；CLI/调度正式入口归 task-17/18。

## 运行时文件

> 非 design 路径：本模块**落库产出与表结构对照**所用；设计口径以上节权威文件为准。

| 文件                                          | 作用                                                               |
| --------------------------------------------- | ------------------------------------------------------------------ |
| `specs/schema/schema.sql`                     | **表结构依赖/产出对照**：`data_sync_job`、`job_event_log` 建表定义 |
| DuckDB `data_sync_job` · `job_event_log` 表行 | **运行时产出**：任务状态与事件流水（由 orchestrator 写入）         |

## 代码主区（实现时收窄）

```text
backend/app/sync/orchestrator.py
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
