# task-07-data-quality-validator

> 流水线 **07**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据质量校验（DataQualityValidator）**

## 负责什么（业务视角）

对 staging 数据做质量检查（如 high<low、缺字段、schema 漂移等），产出 ValidationReport 与 quality 标记；未通过不得进入 clean 写。

## 上下游

| 方向     | 谁                                                                                             |
| -------- | ---------------------------------------------------------------------------------------------- |
| **上游** | **task-06-staging**（待检数据）                                                                |
| **下游** | **task-09-write-manager**（通过后写入）· **task-16-job-data-quality**（巡检 Job 须调用本模块） |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_validation_and_conflict.md`、`docs/architecture/design/04_data_architecture.md`、`docs/modules/design/duckdb_and_parquet.md`、`docs/modules/design/write_manager.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/modules/design/data_sources.md`、`docs/ops/design/logs_health_audit.md`、`specs/contracts/design/log_audit_contract.yaml`、`docs/architecture/design/03_runtime_flows.md`、`docs/ops/design/daily_weekly_monthly_checklist.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据同步域 文件5 → 全文）：本票管 **DataQualityValidator**（单份数据内部质量）：`validation_request` → `validation_report`（PASSED / WARNING / FAILED）、`data_quality_log` 与通用/行情/五轴/Layer3 规则（§3–4）。**不含** SourceConflictValidator 与多源比较（→ task-08）；`write_manager.md` ValidationGate 只读本票报告决定是否可写 clean；job 状态 **VALIDATING** 由 orchestrator（→ task-10）驱动。

## 运行时文件

> 非 design 路径：本模块**落库产出与表结构对照**所用；设计口径以上节权威文件为准。

| 文件                                 | 作用                                                                        |
| ------------------------------------ | --------------------------------------------------------------------------- |
| `specs/schema/schema.sql`            | **表结构依赖/产出对照**：`validation_report`、`data_quality_log` 建表定义   |
| `data/audit/data_quality_log.ndjson` | **运行时产出**：行级质量事件审计 NDJSON（路径由 `log_audit_contract` 规定） |

## 代码主区（实现时收窄）

```text
backend/app/validators/（DataQualityValidator）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
