# Merge gate — fix/r3y-sync-adapter-guard (α-1)

**Slice:** α-1 close `R3Y-SYNC-001` (adapter= production fail-closed guard)  
**Branch:** `fix/r3y-sync-adapter-guard`  
**Registry:** `R3Y-SYNC-001` — runtime guard **implemented**; registry CLOSED deferred to **α-2**

## Guard design

Single-point guard in `backend/app/sync/runners.py`:

| Symbol                                 | Role                                                                                                       |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `sync_adapter_bypass_allowed()`        | Returns true when `PYTEST_CURRENT_TEST` is set (pytest) or `QMD_SYNC_ALLOW_ADAPTER=1` (explicit test hook) |
| `guard_production_adapter_bypass(...)` | Raises `ValueError` when `adapter=` is passed without `datasource_service` and bypass is not allowed       |

Orchestrator calls guard at entry of:

- `run_incremental`
- `run_backfill`
- `run_reconcile`

Production profile = neither pytest nor `QMD_SYNC_ALLOW_ADAPTER=1`. Existing `datasource_service=` paths unchanged.

## New tests (`test_r3ySync001_*`)

| Test                                                                  | Purpose                                        |
| --------------------------------------------------------------------- | ---------------------------------------------- |
| `test_r3ySync001_incremental_rejectsAdapterBypassInProductionProfile` | incremental adapter= reject                    |
| `test_r3ySync001_backfill_rejectsAdapterBypassInProductionProfile`    | backfill adapter= reject                       |
| `test_r3ySync001_reconcile_rejectsAdapterBypassInProductionProfile`   | reconcile adapter= reject                      |
| `test_r3ySync001_testHookAllowsAdapterBypassWhenExplicitEnv`          | `QMD_SYNC_ALLOW_ADAPTER=1` preserves test path |

## GitNexus impact (upstream, before edit)

| Symbol            | Risk |
| ----------------- | ---- |
| `run_incremental` | LOW  |
| `run_backfill`    | LOW  |
| `run_reconcile`   | LOW  |

## Commands

```bash
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py -q
# 30 passed

uv run pytest tests/test_datasource_service.py tests/test_source_route_planner.py -q
# 19 passed

uv run pytest -q
# full suite green (see full-pytest-green.txt)

uv run ruff check backend/app/sync tests/test_sync_orchestrator.py tests/test_sync_jobs.py
# All checks passed!
```

## Evidence

| File                                     | Status                  |
| ---------------------------------------- | ----------------------- |
| `execute-evidence/α1-red.txt`            | RED — 3 FAIL (no guard) |
| `execute-evidence/α1-green.txt`          | GREEN — 4 passed        |
| `execute-evidence/full-pytest-green.txt` | full pytest exit 0      |

## Files changed

- `backend/app/sync/runners.py` — guard helpers
- `backend/app/sync/orchestrator.py` — call guard on three entry points
- `tests/test_sync_orchestrator.py` — `test_r3ySync001_*` + `_simulate_production_profile`

## α-2 follow-up

- Registry trio: mark `R3Y-SYNC-001` CLOSED in `AUDIT_DEFERRED_REGISTRY.md` / unresolved registries (α-2 owner only)
