# Resolved Issues Registry

> Purpose: one file for resolved/closed issues, gates, risks, and repairs.  
> Pair: unresolved items live in `docs/UNRESOLVED_ISSUES_REGISTRY.md`.  
> Last reconciled: 2026-06-20 after Round 3 Batch 1 early ops closure.

## Round 3 Batch 1 resolved items (2026-06-20)

| ID                        |     Closed | Item                                           | Evidence                                                                                                                                                                                       |
| ------------------------- | ---------: | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-EARLY-DB-INSPECT-CLI   | 2026-06-20 | Read-only DB inspect CLI Phase A               | `backend/app/ops/db_inspector.py`; `scripts/qmd_ops.py db-inspect`; `tests/test_ops_db_inspector.py`; `specs/contracts/ops_db_inspect_contract.yaml`.                                          |
| DB-R3-001                 | 2026-06-20 | Project `data/` root inventory via inspect     | `.trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.3-inspect.json` (`raw_files_count`, `parquet_files_count`); documented absence/limited local files acceptable per Batch 1 AC. |
| DB-R3-002                 | 2026-06-20 | Read-only DuckDB open + key table row counts   | `.trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.3-inspect.json` (`read_only_open=true`, `key_tables`); `tests/test_ops_db_inspector.py::test_dbInspect_dbFile_unchanged`.     |
| DOC-R3-001                | 2026-06-20 | Round 2.6 archived PASS surfaced in handoff    | `docs/ROUND3_HANDOFF.md` §Round 2.6 gate.                                                                                                                                                      |
| DOC-R3-002                | 2026-06-20 | Registry authority note on early close plan    | `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md` authority block.                                                                                                                        |
| R3-PARTIAL-2              | 2026-06-20 | Vendor FetchPort E2E + full_load skeleton      | `tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath`; `tests/test_sync_jobs.py::test_syncJob_fullLoad_createdToPlanned_recordsEvent`.                     |
| R3-EARLY-PROD-SCALE-BENCH | 2026-06-20 | Production-equivalent smoke evidence (Batch 1) | `.trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.5-smoke-output.json`; `scripts/production_equivalent_smoke.py --use-service-path` (cross-ref `R2.6-IMPL-7`).                  |

## Round2.6 resolved items

| ID          |     Closed | Item                                              | Evidence                                                                                                                                                                                                                                                                 |
| ----------- | ---------: | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R2.6-IMPL-1 | 2026-06-19 | `SourceCapabilityRegistry` production enforcement | `backend/app/datasources/capability_registry.py`; `tests/test_source_capabilities.py`; archived routing-service audit PASS.                                                                                                                                              |
| R2.6-IMPL-2 | 2026-06-19 | Adapter domain alignment                          | adapter `supported_domains`; batch_b fixture; `tests/test_source_capabilities.py`; archived routing-service audit PASS.                                                                                                                                                  |
| R2.6-IMPL-3 | 2026-06-19 | `SourceRoutePlanner` + route persistence          | `backend/app/datasources/route_planner.py`; `backend/app/datasources/route_models.py`; `job_event_log` ROUTE_PLAN payload; `tests/test_source_route_planner.py`.                                                                                                         |
| R2.6-IMPL-4 | 2026-06-19 | `DataSourceService` fetch facade                  | `backend/app/datasources/service.py`; `tests/test_datasource_service.py`.                                                                                                                                                                                                |
| R2.6-IMPL-5 | 2026-06-19 | Sync runner service-based fetch path              | `backend/app/sync/runners.py` fetch_callable; orchestrator `datasource_service`; `tests/test_sync_orchestrator.py`; `tests/test_sync_jobs.py`.                                                                                                                           |
| R2.6-IMPL-7 | 2026-06-19 | Production-equivalent scale benchmark             | `scripts/production_equivalent_smoke.py --use-service-path`; archived routing-service audit metrics.                                                                                                                                                                     |
| R2.6-B1     | 2026-06-19 | Round2.6 Phase B contract gate tests              | `tests/test_source_capabilities.py`; `tests/test_source_route_planner.py`; `tests/test_datasource_service.py`; `tests/test_module_boundaries.py`; `tests/test_data_cli_contract.py`; `tests/test_dependency_extras_contract.py`; `tests/test_platform_source_matrix.py`. |
| R2.6-B2     | 2026-06-19 | Module boundary static checker                    | `scripts/check_module_boundaries.py`; `tests/test_module_boundaries.py`.                                                                                                                                                                                                 |
| R2.6-B3     | 2026-06-19 | Phase A self-check migrated to Trellis            | `.trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate/research/phase-a-self-check-migrated.md`.                                                                                                                                                            |

## Round2.5 / Round2 resolved reference items

| ID          |     Closed | Item                                                               | Evidence                                                                                                                                         |
| ----------- | ---------: | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| R2.5-1..5   | 2026-06-19 | Repair-package Round2 contract drift                               | `docs/quality/ROUND2_REPAIR_ALIGNMENT_TRACKER.md`.                                                                                               |
| R2.5-6      | 2026-06-19 | Domain schedulable before domain_allowed; DISABLED_SOURCE priority | `backend/app/datasources/base_adapter.py`; `tests/test_fetch_disabledDomain_returnsDisabledSourceBeforeDomainAllowed` evidence in tracker/audit. |
| PROC-R2.5-1 | 2026-06-19 | Round2.5 merge + Trellis handoff                                   | PR #15 → commit `7ce283a` on `master` per registry.                                                                                              |
| D3-P3-1     | 2026-06-19 | Five vendor skeleton adapter classes                               | `tests/test_adapter_skeletons.py`.                                                                                                               |
| D5-P1-2     | 2026-06-19 | Manifest protocol uses archived Trellis                            | frozen Batch D archive.                                                                                                                          |
| D1-P3-2     | 2026-06-19 | GitNexus tooling set up                                            | `node .gitnexus/run.cjs analyze` evidence in historical tracker.                                                                                 |

## Round4/security resolved reference items

| ID           |   Closed | Item                                                       | Evidence                                      |
| ------------ | -------: | ---------------------------------------------------------- | --------------------------------------------- |
| R4-API-SEC-1 | Round2.5 | `test_apiSecurityContract_isSingleAuthorityForQueryBudget` | `tests/test_api_security_contract.py`.        |
| R4-API-SEC-2 | Round2.5 | `test_resourceLimitsApiLimits_matchApiSecurityContract`    | `tests/test_api_security_contract.py`.        |
| D4-P3-1      |   PR #11 | Starlette/httpx deprecation warning                        | `httpx2` dev dependency evidence in registry. |
| R2-HYG-2     |   Round2 | Windows pytest temp handling                               | `pyproject.toml` basetemp per registry.       |

## Current verification snapshot

| Command / evidence                                                                                                                                                                     | Result                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `pytest -q`                                                                                                                                                                            | PASS in current session.                                                                                  |
| `pytest tests/test_module_boundaries.py tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_platform_source_matrix.py -q` | 37 passed in current session.                                                                             |
| `pytest tests/test_vendor_fetch_e2e.py -q`                                                                                                                                             | 2 passed in current session.                                                                              |
| `pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py -q`                                                                                                                    | 24 passed in current session.                                                                             |
| Archived Round2.6 Contract Gate audit                                                                                                                                                  | PASS.                                                                                                     |
| Archived Round2.6 Routing Service Gate audit                                                                                                                                           | PASS; records `pytest -q` 443 tests, `check_module_boundaries.py` PASS, production-equivalent smoke PASS. |

## Operating rule

When a row is moved here from `docs/UNRESOLVED_ISSUES_REGISTRY.md`, include:

1. closure date,
2. concrete code/docs/tests evidence,
3. whether it still has any follow-up item under a new ID.
