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
| R2-PARTIAL-1 | Backfill skips quality gate + clean write | Round 3 ops | `ROUND2_GAPS_AND_DEVIATIONS.md` §2.1 · `DECISIONS.md` §11 |
| R2-PARTIAL-2 | Reconcile skeleton (no re-fetch) | Round 3 | `ROUND2_GAPS_AND_DEVIATIONS.md` §2.2 |
| R2-PARTIAL-3 | manual_review_queue after failed reconcile | By design | `ROUND2_GAPS_AND_DEVIATIONS.md` §2.3 |
| R2-PARTIAL-4 | COMPLETED vs write non-atomic | Round 3 ops | `BATCH_D_STATUS.md` D-A2-3 |
| R2-GAP-1 | `init_db.py` does not auto `sync_to_db` | Round 3 ops | `sync_registry.py` / `DECISIONS.md` §9 |
| R2-GAP-2 | No source capability list API | Round 4 | `ROUND2_GAPS_AND_DEVIATIONS.md` §2.6 |
| D2-P3-1 | `registry_generation` / `removed_from_yaml_at` audit columns | Round 3+ | `DECISIONS.md` |
| D3-P3-1 | Adapter skeleton explicit classes (5 vendors) | By design | `data_adapter_contract.md` |
| D1-P3-1 | Default pytest without project basetemp on Windows | Environment | use `--basetemp=.audit-sandbox/pytest` |
| D1-P3-2 | GitNexus impact native dependency | Tooling setup | run `node .gitnexus/run.cjs analyze` after commit |
| D5-P1-2 | Manifest protocol uses archived Trellis tasks | By design | contract smoke against frozen Batch D archive |
| D7-P1-1 | Orchestrator handler registry (partial ports only) | Round 3 | `sync/pipeline.py` defers full handler split |
| D7-P2-2 | `sys.path.insert` in scripts | Round 3 packaging | editable install; console_scripts planned |
| D3-P1-2 | `SourceRegistry._validate_domain_roles` / `WriteManager._execute_write` C901 | Round 3 hygiene | optional refactor; default ruff check excludes C901 |
| D4-P3-1 | Starlette/httpx deprecation test warning | **Resolved** @ `master` | dev dep `httpx2>=2.0.0` replaces `httpx` for TestClient |

Verification command baseline (2026-06-19):

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
cd frontend && npm run typecheck && npm run test
```
