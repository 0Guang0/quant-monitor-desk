# task-06-staging

> 流水线 **06**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**Staging 暂存层**

## 负责什么（业务视角）

把 raw/normalized 数据写入 staging 表，对应 job 状态机中的 **STAGED**。是「可质检的待入库草稿」，还不是 clean 标准表。

## 上下游

| 方向     | 谁                                                                         |
| -------- | -------------------------------------------------------------------------- |
| **上游** | **task-05-raw-store**（原始/normalized 输入）                              |
| **下游** | **task-07-data-quality-validator** · **task-08-source-conflict-validator** |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/duckdb_and_parquet.md`、`docs/architecture/design/04_data_architecture.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/modules/design/write_manager.md`、`docs/modules/design/data_sources.md`、`docs/modules/design/local_file_system.md`、`docs/architecture/design/03_runtime_flows.md`、`docs/ops/design/idempotency_retry_dlq_policy.md`、`docs/ops/design/logs_health_audit.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据存储域 文件1/2/3 + 数据同步域 文件4 §13.2 → 全文）：本票管 **staging 表族（`stg_*`）、temp parquet、批次元数据（batch_id / run_id / source_id）** 与 job 状态 **STAGED**；staging 可重建、不作前端/Agent 数据源，保留期默认 7–30 天（`duckdb_and_parquet.md` §4.1）。`04_data_architecture.md` §4 规定 staging「允许重复、缺字段须标记」。`write_manager.md` 的 StagingWriter 是本票落地组件；**clean 写入与 ValidationGate 归 task-09**；质量/冲突规则归 task-07/08。

## 运行时文件

> 非 design 路径：本模块**落库与表结构对照**所用；设计口径以上节权威文件为准。

| 文件                                  | 作用                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------ |
| `specs/schema/schema.sql`             | **表结构依赖/产出对照**：`stg_*` staging 表建表定义                      |
| DuckDB `stg_*` 表 · temp parquet 路径 | **运行时产出**：待检批次数据（表名/路径由 design 规定，非 specs 内文件） |

## 代码主区（实现时收窄）

```text
backend/app/sync/runners.py（staging 步骤）· staging 表族
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
