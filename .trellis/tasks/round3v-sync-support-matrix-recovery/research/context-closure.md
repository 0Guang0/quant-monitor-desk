# Context closure — B3V-SYNC sync support matrix

## Upstream wiring

- `specs/contracts/sync_job_contract.yaml` — implemented/reserved SSOT
- `backend/app/sync/orchestrator.py` · `runners.py` — runtime deferred + crash hook
- `write_contract.yaml` / `WriteManager` — **read-only** (B3V-OPS)
- ADR-001 — COMPLETED after write commit; recovery not same-transaction

## VR closure (branch)

- **VR-SYNC-002:** support matrix + `DeferredJobTypeError` — closed on branch
- **VR-SYNC-001:** path A — crash-window pytest + `recover_stuck_writing_job` GREEN

## Deferred (unchanged)

- Full runner impl for `full_load` / `data_quality` / `revision_audit`
- registry 三件套 direct commit — `research/registry_proposed_delta.yaml` only
