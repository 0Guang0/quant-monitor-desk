# B02_04 — Sync Job Support Matrix and Crash-window Recovery

> Owns: `VR-SYNC-002`, coordinates with `VR-SYNC-001`.  
> Roadmap: Round 3V.1 · Batch package: `BATCH_3V_VERIFIED_AUDIT_CLEANUP` (follow-through to Round 3F.4 if recovery is too broad).  
> Suggested branch: `fix/round3v-sync-support-matrix-recovery`.  
> Parallel: do not combine with `qmd data` CLI release work; CLI must consume the support matrix after this task.

---

## 1. Goal

Make sync job runtime capabilities explicit and safe: implemented job types must be callable, reserved job types must return stable deferred errors, and COMPLETED/write crash-window semantics must be closed or precisely re-deferred.

---

## 2. Scope

### `VR-SYNC-002`

- Split sync job contract into `implemented_job_types` and `reserved_job_types`.
- Current implemented set should match actual runtime methods, such as incremental/backfill/reconcile if confirmed.
- `full_load`, `data_quality`, and `revision_audit` must be either implemented with tests or return stable `DEFERRED_JOB_TYPE` style errors.
- Update registry row text if method names drifted from code.

### `VR-SYNC-001`

- Review COMPLETED/write state transitions.
- If scope is small, add injected-crash tests and same-transaction/recovery behavior.
- If scope is broad, produce a precise Round 3F.4 task handoff with owner, entrypoints, and closure tests.

---

## 3. Required inputs

- `specs/contracts/sync_job_contract.yaml`.
- `backend/app/sync/orchestrator.py`.
- `backend/app/sync/runners.py`.
- `backend/app/db/write_manager.py`.
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` rows `D2-P1-1`, `R3-PARTIAL-5`.
- Existing sync/orchestrator tests.

---

## 4. Forbidden scope

- Do not expose reserved job types through CLI/API as available.
- Do not perform production clean write.
- Do not implement full_load/data_quality/revision_audit broadly unless split into `/to-issues` slices and approved by scope.
- Do not hide `NotImplementedError` behind generic exceptions; use stable deferred status.

---

## 5. Implementation slices

1. `B02-SYNC-01` — Contract support matrix: implemented vs reserved job types.
2. `B02-SYNC-02` — Runtime parity test for implemented job types.
3. `B02-SYNC-03` — Reserved job type returns stable deferred error, not bare `NotImplementedError`.
4. `B02-SYNC-04` — Registry text reconcile for D2-P1-1.
5. `B02-SYNC-05` — Crash-window injection review for R3-PARTIAL-5.
6. `B02-SYNC-06` — Close `VR-SYNC-001` if tests are sufficient; otherwise create Round 3F.4 handoff.

---

## 6. Testing requirements

- Contract implemented job types equal runtime callable job types.
- Reserved job types return deferred status with code, owner/phase, and docs anchor.
- No bare `NotImplementedError` reaches CLI/API boundary.
- Crash-window test or handoff evidence must cover write-success/status-failure and audit-failure windows.
- **`VR-SYNC-001`:** closing requires crash-window pytest **or** written Round 3F.4 handoff (path in branch `research/sync-001-handoff.md`); support-matrix-only is insufficient.
- Tests document coverage scope, test object, and purpose.

---

## 7. Acceptance commands

```bash
uv sync --locked
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py -q
uv run pytest tests/test_write_manager.py tests/test_db_validation_gate.py -q
uv run ruff check backend/app/sync backend/app/db tests
```

Use nearest existing test files if names differ; document substitutions.

---

## 8. Done criteria

- `VR-SYNC-002` is closed or precisely re-deferred.
- `VR-SYNC-001` is closed or handed to Round 3F.4 with exact recovery tests.
- CLI/API consumers cannot call reserved job types as if implemented.
- No production DB mutation occurred.
