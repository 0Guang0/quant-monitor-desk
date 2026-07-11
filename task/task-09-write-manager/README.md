# task-09-write-manager

> 流水线 **09**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**写库总管（WriteManager / DuckDBWriteManager）**

## 负责什么（业务视角）

系统**唯一** clean/snapshot/audit 正式写入口：staging 过闸后短事务写入 DuckDB，维护 write_audit_log、primary vs degraded clean、单写锁。入库流水线在本步完成。

## 上下游

| 方向     | 谁                                                                           |
| -------- | ---------------------------------------------------------------------------- |
| **上游** | **task-07** 质量校验 · **task-08** 冲突校验（均 PASS 或已处理）              |
| **下游** | **task-10-sync-orchestrator**（编排调用写口）· Layer/API 只读消费 clean 数据 |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/write_manager.md`、`docs/ops/design/lock_and_concurrency_policy.md`、`docs/modules/design/duckdb_and_parquet.md`、`docs/modules/design/data_validation_and_conflict.md`、`docs/architecture/design/04_data_architecture.md`、`docs/modules/design/data_sources.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/ops/design/logs_health_audit.md`、`specs/contracts/design/log_audit_contract.yaml`、`docs/architecture/design/module_boundary_matrix.md`、`docs/architecture/design/03_runtime_flows.md`、`docs/ops/design/migration_recovery_policy.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据存储域 文件4 + 运维域 文件3/6 → 全文）：本票管 **系统唯一 clean / snapshot / audit 写入口**（DuckDBWriteManager）：ValidationGate → MergePlanner → TransactionRunner → `write_audit_log`；**primary-grade** vs **degraded clean**（`source_role` / `quality_flags` / `stale_reason`）；单写锁 `data/duckdb/.write.lock` 与崩溃恢复（QM-AUD-009）。staging 写入归 task-06；质量/冲突报告归 task-07/08；编排调用归 task-10。

## 运行时文件

> 非 design 路径：本模块**落库、锁文件与表结构对照**所用；设计口径以上节权威文件为准。

| 文件                                | 作用                                                               |
| ----------------------------------- | ------------------------------------------------------------------ |
| `specs/schema/schema.sql`           | **表结构依赖/产出对照**：`write_audit_log` 及 clean 目标表建表定义 |
| `data/duckdb/quant_monitor.duckdb`  | **运行时依赖/产出**：DuckDB 主库（单写连接持有方）                 |
| `data/duckdb/.write.lock`           | **运行时产出/依赖**：跨进程写锁文件                                |
| `data/audit/write_audit_log.ndjson` | **运行时产出**：写入审计 NDJSON                                    |

## 代码主区（实现时收窄）

```text
backend/app/db/write_manager（或项目内 DuckDBWriteManager 路径）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
