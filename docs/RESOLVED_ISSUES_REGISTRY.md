# Resolved Issues Registry

> Purpose: one file for resolved/closed issues, gates, risks, and repairs.  
> Pair: unresolved items live in `docs/UNRESOLVED_ISSUES_REGISTRY.md`.  
> Last reconciled: 2026-06-24 post-wave-B merge + Trellis archive (`master` @ `68b10982`).

## Post-Wave B resolved (2026-06-24)

| ID                  | Closed     | Item                                             | Evidence                                                                                                                                                                              |
| ------------------- | ---------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-TASK-021         | 2026-06-24 | Layer3 industry-chain daily snapshot (`021`)     | `.trellis/tasks/archive/2026-06/06-24-round3-021-layer3-snapshot/` · `backend/app/layer3_chains/snapshot_builder.py` · Audit PASS · 8 snapshot tests                                  |
| R3-PROMPT19-V2      | 2026-06-24 | PROMPT_19 staged real-data pilot v2              | merge `e4abb372` · `.trellis/tasks/archive/2026-06/06-24-round3-real-data-staged-pilot-v2/` · `tests/test_staged_pilot.py` · Audit PASS                                               |
| R3Y-MUT-PROOF-001   | 2026-06-24 | `mutation_proof` VERIFIED hash+count semantics   | `backend/app/ops/mutation_proof.py` · `tests/test_staged_pilot.py` AC-MUT-001 / `test_mutationProof_*` · AUD-04 closed in PROMPT_19                                                   |
| R3Y-REGISTRY-ALPHA2 | 2026-06-24 | fix α-2 registry / COVERAGE / Map §2.4 reconcile | merge `984c7b28` · `.trellis/tasks/archive/2026-06/fix-r3y-registry-lineage-defer/` · `tests/test_round3_audit_registry_alignment.py` · `tests/test_unresolved_item_task_coverage.py` |
| R3Y-SYNC-001        | 2026-06-24 | Sync production `adapter=` bypass fail-closed    | merge `616feeb8` · `.trellis/tasks/archive/2026-06/fix-r3y-sync-adapter-guard/` · `tests/test_sync_orchestrator.py::test_r3ySync001_*`                                                |

## Post-PROMPT_18 wave-A resolved (2026-06-23)

| ID                           | Closed     | Item                                                    | Evidence                                                                                                                                               |
| ---------------------------- | ---------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R3-B3-STAGED-DOWNSTREAM-GATE | 2026-06-22 | Batch 3 staged-only downstream gate closed (docs/tests) | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` · `.trellis/tasks/archive/2026-06/06-22-round3-batch3-staged-gate/`                                    |
| R3-TASK-019                  | 2026-06-23 | Layer2 cross-asset sensor (`019`) staged pipeline       | `.trellis/tasks/archive/2026-06/06-22-round3-019-layer2-sensor/` · Audit PASS                                                                          |
| R3-TASK-020                  | 2026-06-23 | Layer3 industry chain loader (`020`)                    | `.trellis/tasks/archive/2026-06/06-23-round3-020-layer3-loader/` · `backend/app/layer3_chains/` · Audit PASS · 14 tests                                |
| R3-TASK-023A                 | 2026-06-23 | Layer5 evidence foundation (`023A`) minimal slice       | `.trellis/tasks/archive/2026-06/06-22-round3-023a-evidence-foundation/`                                                                                |
| R3Y-AUDIT-GATE-18            | 2026-06-23 | PROMPT_18 post-R3X strict adversarial audit complete    | `.trellis/tasks/archive/2026-06/06-23-round3-post-r3x-strict-audit/review-evidence/R3Y-AUD-08-go-no-go.md` · **`WARN_ALLOW_WITH_CONTROLS`** (no BLOCK) |

## Post-14 registry/docs hygiene resolved (2026-06-22)

| ID              | Closed     | Item                                                                                                                                        | Evidence                                                                                                                                                      |
| --------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-AUDIT-DEF-03 | 2026-06-22 | Per-subdir `--limit` scan cap tests for `raw`/`parquet`/`audit`/`report`                                                                    | `tests/test_ops_db_inspector.py` (`test_dbInspect_subdirScan_respectsLimit` et al.) · post-14 Slice 3 B-027 · `tests/test_round3_audit_registry_alignment.py` |
| R2-RISK-3       | 2026-06-22 | Unimplemented `write_mode` (`replace_partition` 等) fail-closed via `WriteManager.UNSUPPORTED_MODES` (B-008); `append`/`upsert` implemented | `tests/test_r3x_ponytail_structural_bucket_b.py` · `debt/round3-ponytail-structural-bucket-b` merge gate · `specs/contracts/write_contract.yaml`              |

## Round 3 PROMPT_14 resolved items (2026-06-22)

| ID                    | Closed     | Item                                                                                                                                                       | Evidence                                                                                                                                                                                                                                              |
| --------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-PROMPT14-STAGED-01 | 2026-06-22 | PROMPT_14 staged real-data pilot executed; closeout `PILOT_PASS_STAGED_RAW` (partial — akshare validation NETWORK_ERROR; see `R3-PROMPT14-AKSHARE-VAL-01`) | `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/pilot_closeout.json` · `merge_gate_report.md` · `docs/quality/prompt14_user_authorization_2026-06-22.md` · `tests/test_staged_pilot.py`; does **not** close `R3-B2.75-REQ2-EM` |

## Round 3 Batch 2.5 resolved items (2026-06-21)

### Batch 2.5 audit follow-ups（2026-06-21）

| ID            | Closed     | Item                                                 | Evidence                                                  |
| ------------- | ---------- | ---------------------------------------------------- | --------------------------------------------------------- |
| R3-B25-DOC-01 | 2026-06-21 | Batch 3 staged-only downstream gate 已记录           | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`           |
| A08-P1-02     | 2026-06-21 | pytest slow marker 与 quick profile tier 已补齐      | `pytest.ini` · `pyproject.toml` · `KNOWN_PYTEST_SKIPS.md` |
| R3-B25-HYG-04 | 2026-06-21 | audit sandbox artifact review 噪音已通过忽略规则缓解 | `.gitignore` `.audit-sandbox*` rule                       |

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

| ID               | Closed     | Evidence                                                                                                                                                                                                                                                     | Follow-up                                                                                                                                                                                          |
| ---------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-B2.75-PLAN-01 | 2026-06-21 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`; `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`; `docs/quality/production_live_pilot_policy.md`; `tests/test_production_live_pilot_policy.py`; `.ai-bridge/current-plan.md`     | Does not close `R3-B2.75-01`; actual controlled live pilot implementation remains DEFERRED.                                                                                                        |
| R3-B2.75-01      | 2026-06-21 | `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/final_pilot_closeout.md`; `phase3_raw_micro_fetch_evidence.json`; `phase4_validation_report.json`; `phase3_request2_evidence_reconciliation.md`; `tests/test_batch275_live_pilot_gate.py` | Closeout `PILOT_FAIL_SOURCE` — partial sandbox live evidence (Request 1/3); Request 2 original endpoint failure; does **not** open production-live access. Follow-up: `R3-B2.75-REQ2-EM` / `018C`. |

## Operating rule

When a row is moved here from `docs/UNRESOLVED_ISSUES_REGISTRY.md`, include:

1. closure date,
2. concrete code/docs/tests evidence,
3. whether it still has any follow-up item under a new ID.
