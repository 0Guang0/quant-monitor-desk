# Resolved Issues Registry

> Purpose: one file for resolved/closed issues, gates, risks, and repairs.  
> Pair: unresolved items live in `docs/UNRESOLVED_ISSUES_REGISTRY.md`.  
> Last reconciled: 2026-06-21 after Batch 2.5 audit fix branch (path_compat, schema.sql, uv.lock).

## Round 3 Batch 2.5 resolved items (2026-06-21)

| ID               |     Closed | Item                                                                         | Evidence                                                                                                                         |
| ---------------- | ---------: | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| B2.5-O-02        | 2026-06-21 | `specs/schema/schema.sql` synced with migration 011 axis tables              | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02` · `specs/schema/schema.sql`                                               |
| B2.5-O-03        | 2026-06-21 | `axis_observation` timestamp ordering via app-layer (DuckDB ALTER CHECK N/A) | `test_layer1Observation_noFutureDataRejected` · `test_layer1Ingestion_phase0_axisObservation_appValidatorEnforcesTimestampOrder` |
| B2.5-WIN-PATH-01 | 2026-06-21 | Windows MAX_PATH raw evidence under deep pytest basetemp                     | `backend/app/storage/path_compat.py` · `test_save_windowsLongPath_writesSuccessfully` · phase3/4 evidence tests                  |

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

| Command / evidence                                                                                                                                                                                           | Result                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_documentation_index.py tests/test_global_execution_rules.py tests/test_trellis_validate_plan.py -q` | 25 passed in current session.                                                                             |
| `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q`                                                                                                            | 9 passed in current session.                                                                              |
| `pytest tests/test_documentation_index.py tests/test_global_execution_rules.py tests/test_trellis_validate_plan.py -q`                                                                                       | 16 passed in current session.                                                                             |
| Archived Round2.6 Contract Gate audit                                                                                                                                                                        | PASS.                                                                                                     |
| Archived Round2.6 Routing Service Gate audit                                                                                                                                                                 | PASS; records `pytest -q` 443 tests, `check_module_boundaries.py` PASS, production-equivalent smoke PASS. |

## Round 3 Batch 2.5 — Layer 1 observation ingestion bridge

| ID        | Closed     | Evidence                                                                                                                        |
| --------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------- |
| B2.5-O-04 | 2026-06-20 | `commit_clean_observation_and_snapshots` + `Layer1ObservationWriter`; `test_layer1Observation_cleanWrite_usesWriteManager`      |
| B2.5-O-07 | 2026-06-20 | Single `fetch_log` per service fetch; `base_adapter.record_fetch_log`; `test_layer1MicroIngestion_writesFetchLogAndRawEvidence` |

## Round 3 Batch 2.75 — planning/policy gate

| ID               | Closed     | Evidence                                                                                                                                                                                                                                                 | Follow-up                                                                                   |
| ---------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| R3-B2.75-PLAN-01 | 2026-06-21 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`; `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`; `docs/quality/production_live_pilot_policy.md`; `tests/test_production_live_pilot_policy.py`; `.ai-bridge/current-plan.md` | Does not close `R3-B2.75-01`; actual controlled live pilot implementation remains DEFERRED. |

## Operating rule

When a row is moved here from `docs/UNRESOLVED_ISSUES_REGISTRY.md`, include:

1. closure date,
2. concrete code/docs/tests evidence,
3. whether it still has any follow-up item under a new ID.
