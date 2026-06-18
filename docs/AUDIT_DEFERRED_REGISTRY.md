# Audit Deferred Items Registry

Items explicitly deferred from Round 2 scope per `DECISIONS.md` and dimension-two audit.
These are **design intent**, not silent drift.

| ID | Item | Target Phase | Evidence |
|---|---|---|---|
| D2-P1-1 | `run_full_load`, `run_revision_audit`, `run_data_quality` | Round 3+ | `BATCH_D_STATUS.md`, `DECISIONS.md` |
| D2-P1-2 | Real vendor FetchPort (non-skeleton) | Batch D+ / Round 3 | adapter skeletons + `DECISIONS.md` |
| D2-P1-3 | `python -m quant_monitor.sync` production CLI | Round 3 ops | `BATCH_D_STATUS.md` |
| D2-P2-1 | `source_health_snapshot` table + health checks | Round 3+ | `DECISIONS.md` |
| D2-P2-2 | Full reconcile re-fetch/compare flow | Round 3 | `orchestrator.run_reconcile` skeleton note |
| D2-P3-1 | `registry_generation` / `removed_from_yaml_at` audit columns | Round 3+ | `DECISIONS.md` |
| D3-P3-1 | Adapter skeleton explicit classes (5 vendors) | By design | `data_adapter_contract.md` |
| D1-P3-1 | Default pytest without project basetemp on Windows | Environment | use `--basetemp=.audit-sandbox/pytest` |
| D1-P3-2 | GitNexus impact native dependency | Tooling setup | run `node .gitnexus/run.cjs analyze` after commit |
| D5-P1-2 | Manifest protocol uses archived Trellis tasks | By design | contract smoke against frozen Batch D archive |
| D7-P1-1 | Orchestrator handler registry (partial ports only) | Round 3 | `sync/pipeline.py` defers full handler split |
| D7-P2-2 | `sys.path.insert` in scripts | Round 3 packaging | editable install; console_scripts planned |
| D3-P1-2 | `SourceRegistry._validate_domain_roles` / `WriteManager._execute_write` C901 | Round 3 hygiene | optional refactor; default ruff check excludes C901 |
| D4-P3-1 | Starlette/httpx deprecation test warning | Dependency upgrade | 0 test failures; install httpx2 when upgrading Starlette |

Verification command baseline (2026-06-19):

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
cd frontend && npm run typecheck && npm run test
```
