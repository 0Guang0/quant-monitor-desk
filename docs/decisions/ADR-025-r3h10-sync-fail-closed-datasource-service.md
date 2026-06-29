# ADR-025: Sync Production Fail-Closed Without `datasource_service`

## Status

Accepted (2026-06-29) — Plan R3H-10 / S10-01

## Context

R3H-10 closes **C2** by making `DataSourceService` the sole production fetch facade for Sync, CLI route preview, and rehearsal boundaries (`STAGED-PILOT-SSOT`).

Existing guards already **fail-closed** when production passes `adapter=` without `DataSourceService` (`guard_production_adapter_bypass` in `backend/app/sync/runners.py`). Runners also reject runs with neither `adapter` nor `fetch_callable` (`IncrementalJobRunner.run` / `BackfillShardRunner.run`).

The remaining ambiguity was orchestrator-level behavior when **both** `adapter=` and `datasource_service=` are omitted: auto-construct a default production service vs explicit error.

Reference analysis (`reference-adoption-r3h10.md`) flags EasyXT `auto_data_updater` as an anti-pattern: a second implicit sync entry (`DataManager` via `sys.path`) bypassing a unified facade.

## Decision

1. **Production semantics:** `DataSyncOrchestrator.run_incremental` / `run_backfill` **must not** auto-construct a default `DataSourceService` when `datasource_service=` is omitted. **`run_reconcile`** remains adapter-shaped in R3H-10 (see §Reconcile defer).
2. **Required caller contract:** operators and scripts must pass `datasource_service=` explicitly on the production gold path (as in `tests/test_vendor_fetch_e2e.py`).
3. **Failure mode:** fail-closed with a clear, testable error distinguishing:
   - missing `datasource_service=` (this ADR), vs
   - `adapter=` bypass without service (existing R3Y guard).
4. **Tests:** extend `tests/test_sync_orchestrator.py` (or equivalent) so production-profile calls without `datasource_service=` and without `adapter=` RED→GREEN per S10-01.
5. **Out of scope:** changing pytest-only `adapter=` hooks guarded by `sync_adapter_bypass_allowed()`.

### Reconcile defer (R3H-10 closure)

- **R3H-10 S10-01 delivered:** `guard_production_datasource_service_required` on `run_incremental` / `run_backfill` only.
- **`run_reconcile(conflict_id, *, adapter=)`** keeps mandatory `adapter=`; production profile **fail-closed** via `guard_production_adapter_bypass` (`test_r3ySync001_reconcile_*`).
- **`datasource_service=` gold path for reconcile** is **deferred** to a post-R3H-10 sync slice (bound: Wave 2 / R3H-08 product live prep or dedicated reconcile-service follow-up). Not a silent bypass: reconcile without service **cannot run** in production today.

## Alternatives Considered

### Auto-construct default `DataSourceService`

- Pros: fewer call-site changes for scripts.
- Cons: hides registry/guard/fixture choices; creates implicit second entry akin to EasyXT `DataManager`; weakens auditability of `datasource_service_contract.yaml`.
- **Rejected.**

### Fail-closed (chosen)

- Pros: symmetric with adapter bypass guard; explicit gold path; aligns with C2 SSOT and PASS gate.
- Cons: call sites must wire service explicitly.

## Consequences

- S10-01 Execute focuses on orchestrator-level enforcement and error messaging, not inventing new runner semantics.
- Documentation and live card reference this ADR.
- R3H-08 product live work inherits an explicit service injection contract.

## References

- Execute entry: `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md` §4
- `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/to-issues-slices.md` §3
- `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/research/reference-adoption-r3h10.md` §3.2
- `backend/app/sync/runners.py` — `guard_production_adapter_bypass`
