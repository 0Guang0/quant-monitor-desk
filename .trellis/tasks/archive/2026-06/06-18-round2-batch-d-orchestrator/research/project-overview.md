# Project Overview — Round 2 Batch D（≤1 页）

> GitNexus Phase 1a · 2026-06-18 · index fresh

## 当前仓库 ingestion 底座（Batch A–C 已交付）

| 层 | 模块 | 路径 |
|----|------|------|
| Registry | SourceRegistry | `backend/app/datasources/source_registry.py` |
| Contract | BaseDataAdapter / FetchPort | `backend/app/datasources/` |
| Audit | FetchLogWriter | `backend/app/datasources/fetch_log.py` |
| Quality | DataQualityValidator | `backend/app/validators/data_quality.py` |
| Conflict | SourceConflictValidator | `backend/app/validators/source_conflict.py` |
| Gate | DbValidationGate | `backend/app/db/validation_gate.py` |
| Write | DuckDBWriteManager | `backend/app/db/write_manager.py` |
| Guard | ResourceGuard | `backend/app/core/resource_guard.py` |
| Migrations | 004 ingestion + 005 validation | `backend/app/db/migrations/` |

**Batch C 门禁：** 312 pytest passed · cov 94% · Audit PASS · `READY_FOR_BATCH_D: yes`

## Batch D 缺口（GitNexus query 无命中）

- **无** `DataSyncOrchestrator` / `backend/app/sync/*` 实现
- **无** migration 应用 `data_sync_job` / `job_event_log`（仅在 `specs/schema/schema.sql` 定义）
- **无** ingestion 编排 E2E（仅有 `test_batch_c_validation_flow` 手工串联 validator 链）

## 目标运行时链路（`03_runtime_flows.md`）

```text
CLI/Scheduler → ResourceGuard → DataSyncOrchestrator → Adapter
  → staging → DataQualityValidator → SourceConflictValidator
  → DbValidationGate → WriteManager → clean tables
```

## 关键契约

- `specs/contracts/sync_job_contract.yaml` — job_type + status 枚举
- `docs/modules/data_sync_orchestrator.md` §13 — 状态机、run/job/task id、断点续跑

## Plan 聚焦

1. migration **006** 建 sync 表
2. `backend/app/sync/jobs.py` 状态机 + job 模型
3. `backend/app/sync/orchestrator.py` 编排 fetch→validate→write
4. ResourceGuard 门禁 + registry bootstrap + ingestion smoke

## 明确不做

Layer 1–5 建模、FastAPI 生产路由、Agent sandbox、真实 vendor HTTP、全量 security CI sprint。
