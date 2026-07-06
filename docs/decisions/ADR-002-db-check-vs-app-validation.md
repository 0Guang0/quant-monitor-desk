# ADR-002：数据库 CHECK 与应用层校验的分工

## 状态

已接受（2026-06-19）

## 背景

DuckDB 对已存在表难以安全执行 `ALTER TABLE ADD CONSTRAINT`。Round2 审计发现若干状态字段（`fetch_log.status`、`manual_review_queue.status`、`source_conflict.reconcile_status`、`source_registry.source_type`）此前仅在 Python 层约束。

## 决策

1. **应用层仍是主门禁：** Pydantic 模型（`FetchResult`）、`FetchLogWriter._validate_for_persist`、各类 validator、`SyncJobStateMachine` 在写入时执行业务规则。
2. **Migration 009：** 重建相关表并内联 `CHECK` 约束，作为防御纵深，防止直连 SQL 或脚本绕过应用层。
3. **新增枚举值：** 须同时更新契约 YAML / Python **并** 通过前向 migration 扩展 CHECK 列表。

## 仅应用层约束的列（R2-RISK-4 / R3F-MIG-02）

`manual_review_queue.priority` **仅由应用层约束**。`SourceConflictValidator` 等写入方提供已知取值（如 `HIGH`）；数据库对 `priority` **不设 CHECK**，以便日后优先级体系演进时不必每个枚举都发 migration。详见 `docs/schema/MIGRATION_COVERAGE.md` §Round 3F routing。

## 后果

- 非法直连 INSERT 在测试中于 DB 层失败（如 `test_dbRejectsInvalidFetchStatus`）。
- Schema 迁移采用「整表重建」模式（见 migration 007/009/012）。
- `priority` 非法值在应用代码拒绝，而非 DB CHECK（相关行为见 `tests/test_ingestion_validation_migration.py`、`tests/test_audit_remediation.py`）。
