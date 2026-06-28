# Context closure — B3V-SYNC sync support matrix

> Execute Phase 0 动态闭包（E11：`backend/app/sync/**` · `tests/test_sync_*` 不得列入 implement.jsonl）

## Upstream wiring

- `specs/contracts/sync_job_contract.yaml` — implemented/reserved SSOT
- `backend/app/sync/orchestrator.py` — `recover_stuck_writing_job`（**§9.6 SYNC-06A**）
- `backend/app/sync/runners.py` — `post_write_pre_complete_hook`（**§9.5 · §9.6**）
- `tests/test_sync_orchestrator.py` — parity/deferred/crash/recovery pytest（**§9.1–9.3 · §9.7 SYNC-06B**）
- `write_contract.yaml` / `WriteManager` — **read-only** (B3V-OPS)
- ADR-001 — COMPLETED after write commit; recovery not same-transaction

## VR closure (branch)

- **VR-SYNC-002:** support matrix + `DeferredJobTypeError` — closed on branch
- **VR-SYNC-001:** path A — §9.6–9.8（06A recovery · 06B pytest · 06C proposed delta）

## Deferred (unchanged)

- Full runner impl for `full_load` / `data_quality` / `revision_audit`
- registry 三件套 direct commit — `research/registry_proposed_delta.yaml` only（**§9.8 SYNC-06C**）
