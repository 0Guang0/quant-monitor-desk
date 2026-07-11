# task-08-source-conflict-validator

> 流水线 **08**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**多源冲突校验（SourceConflictValidator）**

## 负责什么（业务视角）

当多个数据源对同一客观字段给出不同值时，按规则判定 warning/severe，写入 `source_conflict`，严重冲突阻塞 clean 写或触发 reconcile。

## 上下游

| 方向     | 谁                                                                |
| -------- | ----------------------------------------------------------------- |
| **上游** | **task-06-staging**（多源可比字段）                               |
| **下游** | **task-09-write-manager** · **task-14-job-reconcile**（冲突重抓） |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_validation_and_conflict.md`、`specs/contracts/design/source_conflict_rules.yaml`、`docs/modules/design/data_sources.md`、`docs/modules/design/write_manager.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/architecture/design/04_data_architecture.md`、`docs/architecture/design/03_runtime_flows.md`、`docs/ops/design/idempotency_retry_dlq_policy.md`、`docs/ops/design/logs_health_audit.md`、`specs/contracts/design/log_audit_contract.yaml`、`docs/ops/design/ERROR_CODE_GUIDE.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据同步域 文件5/7 + 数据源域 文件1 §4.3–4.4 → 全文）：本票管 **SourceConflictValidator**：客观事实字段多源比较、容忍阈值（`source_conflict_rules.yaml` design 版）、`source_conflict` 表与 severity 分级；口径差异类字段分源保存、**不**创建 severe conflict（`data_sources.md` §4.4.2）。ReconcileJob **执行**归 task-14；本票只产出 `conflict_report` 并标记 `needs_reconcile` / `manual_review_required`。

## 运行时文件

> 非 design 路径：本模块**读取、落库产出与验收**所用；设计口径以上节权威文件为准。

| 文件                                         | 作用                                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `specs/contracts/source_conflict_rules.yaml` | **验收契约/配置依赖**：阈值与可比字段机器 SSOT（由 `design/` 版 promote 的运行副本，pytest 对照） |
| `specs/schema/schema.sql`                    | **表结构依赖/产出对照**：`source_conflict` 建表定义                                               |
| `data/audit/source_conflict_log.ndjson`      | **运行时产出**：冲突事件审计 NDJSON                                                               |

## 代码主区（实现时收窄）

```text
backend/app/validators/（SourceConflictValidator）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
