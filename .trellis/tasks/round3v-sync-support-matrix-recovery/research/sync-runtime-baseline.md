# Research: B3V-SYNC runtime baseline

- **Query**: B3V-SYNC Plan — sync support matrix, deferred errors, crash-window
- **Scope**: internal
- **Date**: 2026-06-25

## Findings

### Files Found

| File Path | Description |
|---|---|
| `specs/contracts/sync_job_contract.yaml` | 扁平 `job_types` 六类，无 implemented/reserved |
| `backend/app/sync/orchestrator.py` | `run_incremental/backfill/reconcile` 已实现；`run_full_load/data_quality` → `NotImplementedError` |
| `backend/app/sync/runners.py` | `_finalize_staged` 同事务写；`IncrementalJobRunner` COMPLETED 在 writer 块外（437-510） |
| `backend/app/sync/jobs.py` | `create_job` 接受六 job_type |
| `backend/app/db/write_manager.py` | `UNSUPPORTED_MODES` → 稳定 `ValueError`（deferred 模式参考，只读） |
| `tests/test_sync_orchestrator.py` | 主测试基线（替代不存在的 `test_sync_runners.py`） |
| `tests/test_r3x_residual_open_items_closure.py` | `test_advA3_016` 仍断言 NIE |

### Code Patterns

- **Implemented runners**: `incremental`, `backfill`, `reconcile`（`orchestrator.py:128-223`）
- **Reserved stubs**: `run_full_load` / `run_data_quality`（`orchestrator.py:225-235`）
- **revision_audit**: 无 `run_revision_audit`；`jobs.py:251-258` 仍可 create_job
- **Crash-window**: `runners.py:437-510` — 写事务提交后 `transition(COMPLETED)`；ADR-001 记录为 intentional
- **Deferred 参考**: `write_manager.py:394-399` ValueError 文案模式

### External References

- `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` — COMPLETED 在写提交后

### Related Specs

- `B02_04_sync_job_support_and_recovery.md` — VR-SYNC-002/001
- `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.5 — write 契约 B3V-OPS 独占

## Caveats / Not Found

- `docs/modules/sync_jobs.md` — 不存在；用契约 YAML + `data_sync_orchestrator` 模块文档
- `tests/test_sync_runners.py` — 不存在；Plan 已 substitution 至 `test_sync_orchestrator.py`
- `implement.jsonl` 不得列 `backend/app/sync/**` 或 `tests/test_sync_*`（E11 负向表）
