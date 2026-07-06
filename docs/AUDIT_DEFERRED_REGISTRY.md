# Audit Deferred Items Registry

**Single source of truth** for open issues, intentional deferrals, and resolved audit items.

> Last reconciled: 2026-07-02 Wave 4 四轨 merge 完成（R3-DCP-07/08/09/10 合入 master）；prior R3-DCP-05 @ `c2258363`；prior 2026-07-01 @ `93b2c82`。

**待修复清单（全项目 SSOT）:** [`docs/quality/待修复清单.md`](quality/待修复清单.md)  
**ingestion 拆分回滚方案（后置）:** [`docs/architecture/layer1_ingestion_refactor_rollback_plan.md`](architecture/layer1_ingestion_refactor_rollback_plan.md)

## Resolution policy (mandatory)

Every issue MUST be in exactly one state:

| State        | Meaning                                                          |
| ------------ | ---------------------------------------------------------------- |
| **RESOLVED** | Implemented + tested + evidence linked                           |
| **OPEN**     | Not done; blocks the listed gate until closed                    |
| **DEFERRED** | Not done yet; **must** name a concrete resolution phase and task |

**Rules:**

1. **Non-blocking ≠ abandoned.** If an item does not block task 017, it still needs `Resolution phase`, `Task hook`, and `Closure test`.
2. **No silent drift.** Undocumented gaps are violations; add a row here (or in `docs/quality/待修复清单.md`) before merge.
3. **Phase names must be actionable:** prefer task IDs (`017`…`035`) or current task-card slug over vague “later”.
4. **Registry wins on conflict** with narrative docs; update narratives to link here.

**Companion docs:** `docs/UNRESOLVED_ISSUES_REGISTRY.md` (current unresolved/deferred split) · `docs/RESOLVED_ISSUES_REGISTRY.md` (closed items split) · `docs/quality/待修复清单.md` (open fix ledger SSOT) · `ROUND2_GAPS_AND_DEVIATIONS.md` (narrative) · `ROUND3_HANDOFF.md` (gate).

---

## OPEN — blocks Round 3 entry (017)

_(none — last gate `PROC-R2.5-1` closed 2026-06-19 via PR #15)_

---

## DEFERRED — Round 2.6 (contract gate + routing service)

| ID          | Item                              | Resolution phase            | Task hook                                     | Blocks 017? | Closure test / evidence                                       |
| ----------- | --------------------------------- | --------------------------- | --------------------------------------------- | ----------- | ------------------------------------------------------------- |
| R2.6-IMPL-6 | `qmd data` production CLI         | **Round 3 ops**             | `035` prep · Task 2 docs                      | No          | CLI smoke when implemented                                    |
| R2.6-IMPL-8 | Live QMT/Yahoo/xqshare validation | **User-authorized staging** | `docs/ops/qmt_xqshare_setup.md` · ops runbook | No          | authorized E2E only; inspect CLI has no `--enable-qmt` (D-11) |

## RESOLVED — Round 2.6 routing service gate (2026-06-19)

| ID          | Item                                              | Evidence                                                                               |
| ----------- | ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| R2.6-IMPL-1 | `SourceCapabilityRegistry` production enforcement | `backend/app/datasources/capability_registry.py` + `tests/test_source_capabilities.py` |
| R2.6-IMPL-2 | Adapter domain alignment                          | adapter `supported_domains` + batch_b fixture + capability tests                       |
| R2.6-IMPL-3 | `SourceRoutePlanner` + persistence                | `route_planner.py` + `job_event_log` ROUTE_PLAN payload                                |
| R2.6-IMPL-4 | `DataSourceService` fetch facade                  | `service.py` + `tests/test_datasource_service.py`                                      |
| R2.6-IMPL-5 | Sync runner service-based fetch path              | `runners.py` fetch_callable + orchestrator `datasource_service`                        |
| R2.6-IMPL-7 | Prod-equivalent scale benchmark                   | `scripts/production_equivalent_smoke.py --use-service-path`                            |

---

## DEFERRED — Round 3 (modeling + ops repay)

Does **not** block 017 per `ROUND2_GAPS` §6; **must** be closed or re-deferred with new ID before Round 4.

| ID                      | Item                                                                                                            | Resolution phase                          | Task hook                                                                               | Blocks 017? | Closure test / evidence                                                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| R3-PARTIAL-1            | Backfill gold-path parity ADR (validate+write+severe conflict **implemented** per ADV-R3X-SYNC-002)             | **Round 3 early** (Batch6 pipeline repay) | `DECISIONS.md` §11 · `orchestrator.run_backfill` · `ROUND2_REPAIR_ALIGNMENT_TRACKER.md` | No          | Batch6 ADR documenting any remaining incremental vs backfill orchestration edge cases **or** close as wont-fix with pytest parity note |
| R3-PARTIAL-3            | `run_reconcile` no re-fetch/compare                                                                             | **Round 3 mid** (after 017–019)           | D2-P2-2 · task **014** extension                                                        | No          | Reconcile job re-fetch pytest                                                                                                          |
| R3-PARTIAL-4            | `manual_review_queue` after failed reconcile vs instant severe queue                                            | **Round 3 mid** (conflict UX)             | **016** / **023** evidence chain                                                        | No          | Documented UX ADR + pytest for chosen path                                                                                             |
| D2-P1-1                 | `run_revision_audit` / `run_data_quality` runners — **matrix + deferred errors partial (B3V-C04)**              | **Round 3F** (post Batch 3V)              | Orchestrator job matrix · `sync/contract.py`                                            | No          | Full runner pytest each; reserved types already return `DeferredJobTypeError`                                                          |
| D2-P1-3                 | `python -m quant_monitor.sync` production CLI                                                                   | **Round 3 ops** (packaging)               | **035** prep · `scripts/sync_registry.py` successor                                     | No          | CLI smoke + doc in `verification_commands.md`                                                                                          |
| D2-P2-1                 | `source_health_snapshot` table                                                                                  | **Round 3 mid**                           | New migration + ops                                                                     | No          | Table + snapshot pytest                                                                                                                |
| D2-P2-2                 | Full reconcile re-fetch (alias)                                                                                 | _(see R3-PARTIAL-3)_                      | —                                                                                       | No          | —                                                                                                                                      |
| D2-P3-1                 | `registry_generation` / `removed_from_yaml_at` columns                                                          | **Round 3 late**                          | migration 009+                                                                          | No          | Migration + sync pytest                                                                                                                |
| D7-P1-1                 | Orchestrator full handler registry                                                                              | **Round 3 hygiene** (post 019)            | `sync/pipeline.py` split                                                                | No          | Handler registry pytest                                                                                                                |
| D7-P2-2                 | `sys.path.insert` in scripts                                                                                    | **Round 3 packaging**                     | **035**                                                                                 | No          | `pip install -e .` + console_scripts                                                                                                   |
| A9-P3-01                | Migration rebuild — **009 partial; fetch_log/manual_review_queue `SELECT *` deferred**                          | **Round 3F**                              | explicit column list in future migration                                                | No          | explicit column list + review sign-off for remaining rebuild paths                                                                     |
| R2-RISK-1               | Orchestrator aggregation coupling                                                                               | **Round 3 hygiene**                       | D7-P1-1                                                                                 | No          | Handler extraction merged                                                                                                              |
| R2-RISK-2               | Adapters depend on storage concrete classes                                                                     | **Round 3 mid**                           | `evidence_ports.py`                                                                     | No          | Port injection on one adapter                                                                                                          |
| R3-MODEL-L3L4-MIGRATION | L3/L4/L5 modeling table DuckDB migrations (industry*chain*\_, market\_\_, instrument_registry, security_bar_1d) | **Round 3F / Batch 6**                    | `docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/`                             | Yes         | `tests/test_migration_coverage.py` + migration 012+ applies deferred tables; `KEY_TABLES` exists for `instrument_registry`             |
| R2-HYG-4                | Test inter-call smell (`test_duckdb_connection`)                                                                | **Round 3 hygiene**                       | optional                                                                                | No          | Refactor or close as wont-fix ADR                                                                                                      |
| R2-HYG-5                | Adapter metadata fields not exposed                                                                             | **Round 3 late**                          | B-P2-1                                                                                  | No          | Skeleton metadata pytest                                                                                                               |

---

## DEFERRED — Round 3 Batch 2.5 (Layer 1 observation ingestion bridge)

> Task-scoped index: historical Batch 2.5 deferred-items evidence.

| ID        | Item                                                                           | Resolution phase                                           | Task hook                                        | Blocks Phase 1? | Closure test / evidence                                                                                                                                                                                                                                                                            |
| --------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------- | ------------------------------------------------ | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B2.5-O-03 | `axis_observation` no DB CHECK on timestamp ordering (DuckDB ALTER limitation) | **Closed via app-layer** (ADR-002)                         | `ingestion.py` commit path + `feature_engine.py` | No (Phase 4)    | `test_layer1Observation_noFutureDataRejected` + `test_layer1Ingestion_phase0_axisObservation_appValidatorEnforcesTimestampOrder`                                                                                                                                                                   |
| B2.5-O-05 | Live FRED `primary_source` for `ENV-E1-DGS10` vs staged `macro_supplementary`  | **RE-DEFERRED — Batch 6** FRED-only **live** primary pilot | `018B_production_live_pilot_gate.md`             | No              | **Not closed by Batch 2.75 Request 3.** Batch 01 FRED **sandbox** evidence recorded (`fred_pilot_closeout.json`, merge `9ae91648`); live FRED primary still requires user-authorized `FRED:DGS10` pilot (`pytest tests/test_fred_staged_semantics.py`, `test_b250o05_reDeferred_closureRowClosed`) |

---

## DEFERRED — Round 3 Batch 2.75 (controlled production live pilot gate)

| ID               | Item                                                                                        | Resolution phase           | Task hook                                                                   | Blocks 019? | Closure test / evidence                                                                                                                                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-B2.75-REQ2-EM | Eastmoney `stock_zh_a_hist` / push2his validation endpoint unreachable in pilot environment | **018C / post Batch 2.75** | `018C_tdx_pytdx_low_cost_probe.md` · `eastmoney_stock_zh_a_hist_verdict.md` | No          | Endpoint reachable with evidence **or** approved alternate validation path documented in 018C; Sina sidecar does not close; **same family** as `R3-PROMPT14-AKSHARE-VAL-01` (`fetch_daily_bar_validation` / `stock_zh_a_hist`) — do **not** close on PROMPT_14 staged pilot alone |

## DEFERRED — Round 3 PROMPT_14 staged real-data pilot (2026-06-22)

| ID                         | Item                                                                                            | Resolution phase                   | Task hook                                                                                                                                                      | Blocks 019? | Closure test / evidence                                                                                                                                                               |
| -------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3-PROMPT14-AKSHARE-VAL-01 | akshare `fetch_daily_bar_validation` / `stock_zh_a_hist` re-defer after PROMPT_14 NETWORK_ERROR | **User-authorized staging / 018C** | `docs/quality/prompt14_user_authorization_2026-06-22.md` · Batch 01 SP3 v3 `registry_proposed_delta_v3.yaml` (merge `1a099e8d`) · cross-ref `R3-B2.75-REQ2-EM` | No          | Successful staged/raw evidence for validation daily bar **or** documented alternate; Sina sidecar does not close original Eastmoney hist; must not promote validation-only to Primary |

| R3-PROMPT14-STAGED-01 | PROMPT_14 staged real-data pilot executed; closeout `PILOT_PASS_STAGED_RAW` (akshare validation NETWORK_ERROR; re-defer `R3-PROMPT14-AKSHARE-VAL-01`) | `prompt14_user_authorization_2026-06-22.md` · `tests/test_staged_pilot.py`; does **not** close `R3-B2.75-REQ2-EM` |

## RESOLVED — Round 3 Batch 3V verified audit cleanup (2026-06-25)

| ID / theme   | Item                                                                   | Evidence                                                                                  |
| ------------ | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| VR-OPS-001   | db-inspect contract YAML SSOT + drift test                             | `master` @ `2aeb6f0` · `tests/test_contract_drift_ops_write.py`                           |
| VR-WRITE-001 | write_contract implemented/reserved modes parity                       | same branch · `specs/contracts/write_contract.yaml`                                       |
| VR-DATA-001  | schema_hash fail-closed runtime slice (partial; registry remainder 3F) | `validation_gate.py` · `tests/test_db_validation_gate.py`                                 |
| VR-STOR-001  | RawStore atomic write                                                  | `path_compat.write_bytes_atomic` · `tests/test_raw_store.py`                              |
| VR-SYNC-002  | sync job support matrix + `DeferredJobTypeError`                       | `backend/app/sync/contract.py` · `tests/test_sync_orchestrator.py`                        |
| VR-SYNC-001  | crash-window recovery path A                                           | `recover_stuck_writing_job` · B3V SYNC-05/06 tests                                        |
| VR-REG-001   | migration 009 CHECK coverage reconcile                                 | `MIGRATION_COVERAGE.md` · `009_status_check_constraints.sql` · schema contract test       |
| VR-DOC-001   | FINAL_AUDIT_REPORT manifest restore                                    | `FINAL_AUDIT_REPORT.md` · `check_manifest_files.py`                                       |
| VR-L5-001    | Layer5 evidence chain stale reconcile                                  | `tests/test_layer5_evidence_chain.py` · l5-reconcile matrix                               |
| VR-MODEL-001 | designed vs implemented table matrix                                   | `tests/test_migration_coverage.py` · `R3-MODEL-L3L4-MIGRATION` defer for gaps             |
| A9-P1-01     | `fetch_log` / `source_registry` CHECK via migration 009                | `009_status_check_constraints.sql` · `test_schemaContract_includesStatusCheckConstraints` |
| A9-P2-02     | `source_conflict` CHECK via 009                                        | same                                                                                      |
| B2.5-O-06    | Broad ingestion CHECK closeout                                         | same as A9-P1-01                                                                          |
| R3-PARTIAL-5 | COMPLETED vs write crash window — recovery path A                      | B3V sync orchestrator crash/recovery tests                                                |

## RESOLVED — Round 3 Batch 2.75 live pilot execute closeout

| ID          | Item                                                                                                           | Evidence                                                                                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| R3-B2.75-01 | Controlled production/live pilot executed; closeout `PILOT_FAIL_SOURCE` (Request 2 Eastmoney hist unreachable) | historical pilot closeout · phase3/4 evidence · production DB zero mutation; does not open formal production-live access |

## RESOLVED — Round 3 Batch 2.75 planning/policy gate

| ID               | Item                                            | Evidence                                                                                                                       |
| ---------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| R3-B2.75-PLAN-01 | Batch 2.75 inserted into Round3 plan and policy | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` · `018B_production_live_pilot_gate.md` · `production_live_pilot_policy.md` · policy tests |

## RESOLVED — Round 3 Batch 2.5 (Layer 1 observation ingestion bridge)

| ID               | Item                                                                                                          | Evidence                                                                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| B2.5-O-04        | `commit_clean_observation_and_snapshots` + `Layer1ObservationWriter` + single-transaction ADR-001 commit path | `test_layer1Observation_cleanWrite_usesWriteManager` · `test_layer1Observation_mappingUsesRawFetchPayload` · `adversarial-audit-phase4-remediation.md` |
| B2.5-O-02        | `specs/schema/schema.sql` synced with migration 011 axis tables                                               | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02` · `specs/schema/schema.sql`                                                                     |
| B2.5-O-07        | Single `fetch_log` row per `DataSourceService.fetch` (service-authoritative write)                            | `base_adapter.py` `record_fetch_log` param · `service.py` · layer1 micro-fetch tests assert `fetch_log_delta=1`                                        |
| B2.5-WIN-PATH-01 | Windows MAX_PATH raw evidence I/O under deep pytest basetemp                                                  | `backend/app/storage/path_compat.py` · `test_save_windowsLongPath_writesSuccessfully` · phase3/phase4 evidence tests with deep basetemp                |

## RESOLVED — PROMPT_15 R3X residual open-items closure (2026-06-22)

| ID / theme                                | Item                                            | Evidence                                                                                                                       |
| ----------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| ADV-R3X-\* / ADV-A1–A6 / F-019 / Registry | Master Checklist 37 former OPEN rows            | `tests/test_r3x_residual_open_items_closure.py` · `merge_gate_report.md` · branch `fix/round3-r3x-residual-open-items-closure` |
| R3-PARTIAL-1 dedup                        | Severe-conflict scope overlaps ADV-R3X-SYNC-002 | `validation_gate.py` job_id-scoped severe conflict check · `ROUND2_REPAIR_ALIGNMENT_TRACKER.md` note                           |
| ADV-R3X-SYNC-001 (partial)                | Service-path `datasource_service` injection     | `runners.py` · `orchestrator.run_incremental(..., datasource_service=...)` · PROMPT_15 merge gate                              |

> **Follow-up (closed 2026-06-24):** `R3Y-SYNC-001` adapter bypass → **RESOLVED** via `fix/r3y-sync-adapter-guard` (`test_r3ySync001_*`); reconcile internal fetch remains test-only (`R3-PARTIAL-3`).

## RESOLVED — Round 3 wave A mainline (2026-06-23)

| ID                           | Item                                    | Evidence                                                                        |
| ---------------------------- | --------------------------------------- | ------------------------------------------------------------------------------- |
| R3-B3-STAGED-DOWNSTREAM-GATE | Batch 3 staged gate                     | `BATCH3_STAGED_DOWNSTREAM_GATE.md` · archived `06-22-round3-batch3-staged-gate` |
| R3-TASK-019                  | Layer2 sensor `019`                     | archived `06-22-round3-019-layer2-sensor`                                       |
| R3-TASK-020                  | Layer3 loader `020`                     | archived `06-23-round3-020-layer3-loader` · Audit PASS                          |
| R3-TASK-023A                 | Evidence foundation `023A`              | archived `06-22-round3-023a-evidence-foundation`                                |
| R3Y-AUDIT-GATE-18            | PROMPT_18 strict audit gate synthesized | `R3Y-AUD-08-go-no-go.md` · `WARN_ALLOW_WITH_CONTROLS`                           |

## DEFERRED — Round 3 PROMPT_18 R3Y follow-ups

Does **not** block staged-only mainline; PROMPT_19/β-1 **closed** 2026-06-24; Wave C closed α-3 / β-2 / C-20 / `022` (2026-06-24).

| ID                  | Item                                      | Resolution phase | Task hook                                | Blocks 019? | Closure test / evidence                                                 |
| ------------------- | ----------------------------------------- | ---------------- | ---------------------------------------- | ----------- | ----------------------------------------------------------------------- |
| ADV-R3X-LINEAGE-001 | Full L3/L4 snapshot lineage               | **Batch 6**      | `023_implement_layer5_evidence_chain.md` | No          | snapshot lineage pytest + registry row; 021/022 staged envelopes merged |
| R3Y-LINEAGE-VR-001  | VR / fetch_log binding for Layer2 lineage | **Batch 6**      | same · AUD-05                            | No          | lineage tests must not use synthetic IDs as VR binding                  |

## RESOLVED — Round 3 Wave B mainline (2026-06-24)

| ID                  | Item                                    | Evidence                                                                          |
| ------------------- | --------------------------------------- | --------------------------------------------------------------------------------- |
| R3-TASK-021         | Layer3 snapshot builder `021`           | archived `06-24-round3-021-layer3-snapshot` · `snapshot_builder.py` · Audit PASS  |
| R3-PROMPT19-V2      | PROMPT_19 staged pilot v2               | merge `e4abb372` · archived `06-24-round3-real-data-staged-pilot-v2` · Audit PASS |
| R3Y-MUT-PROOF-001   | `mutation_proof` VERIFIED semantics     | `mutation_proof.py` · `tests/test_staged_pilot.py` AC-MUT-001                     |
| R3Y-REGISTRY-ALPHA2 | fix α-2 registry / Map reconcile        | merge `984c7b28` · archived `fix-r3y-registry-lineage-defer`                      |
| R3Y-SYNC-001        | Sync `adapter=` prod bypass fail-closed | merge `616feeb8` · archived `fix-r3y-sync-adapter-guard` · `test_r3ySync001_*`    |

## RESOLVED — Round 3 PROMPT_18 R3Y hygiene (2026-06-24)

| ID                    | Item                                     | Evidence                                                                                                                                       |
| --------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| R3Y-STAGED-REG-001    | staged file_registry WriteManager bypass | merge `37142924` · `_register_staged_file_registry_rows` privatized · `tests/test_raw_store.py` · archived `fix-r3y-staged-registry-privatize` |
| R3Y-PROMPT15-EVID-001 | PROMPT_15 execute evidence chain         | merge `871b76e2` · `closed_claim_evidence_index.yaml` · `tests/test_r3x_residual_open_items_closure.py` · archived `fix-r3y-prompt15-evidence` |

## RESOLVED — Round 3 Batch 01 mainline (2026-06-25)

| ID           | Item                                    | Evidence                                                                                                           |
| ------------ | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| R3-TASK-023  | Full Layer5 evidence chain `023b`       | merge `376e30e6` · `evidence_chain.py` · `tests/test_layer5_evidence_chain.py` · ADR-023                           |
| R3D-B01-WL   | Model input whitelist                   | merge `b09a3ca6` · `specs/model_inputs/**` · `tests/test_model_input_whitelist.py`                                 |
| R3D-B01-LIN  | Lineage / Layer3 hygiene                | merge `06bcfde1`                                                                                                   |
| R3E-B01-FRED | FRED sandbox pilot + registry reconcile | merge `9ae91648` · `source_registry.yaml` / `source_capabilities.yaml` / `platform_source_matrix.yaml` `fred` rows |
| R3E-B01-TDX  | TDX manual probe                        | merge `01ad6a07` · `PROBE_PASS_RAW_ONLY` mocked · `registry_proposed_delta.yaml` reconciled                        |
| R3E-B01-SP3  | Staged pilot v3                         | merge `1a099e8d` · `registry_proposed_delta_v3.yaml` reconciled                                                    |
| R3E-B01-DH2  | Data health v2 read-only profiles       | merge `dd5fda5f` · `tests/test_data_health_v2.py`                                                                  |

## RESOLVED — Round 3 Wave C mainline (2026-06-24)

| ID             | Item                     | Evidence                                                                                                                               |
| -------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| R3-PROMPT20-DH | PROMPT_20 data health v1 | merge `5b19e9b1` · `backend/app/ops/data_health.py` · `tests/test_ops_data_health.py` · archived `round3-readonly-data-health-v1`      |
| R3-TASK-022    | Layer4 market structure  | merge `18fd64a3` · `backend/app/layer4_markets/` · `tests/test_layer4_market_structure.py` · archived `06-24-round3-022-layer4-market` |

## RESOLVED — Round 3 PROMPT_18 R3Y hygiene (2026-06-24) — sync bypass only

| ID           | Item                        | Evidence                                                                                                                               |
| ------------ | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| R3Y-SYNC-001 | Sync `adapter=` prod bypass | archived `fix-r3y-sync-adapter-guard` · `guard_production_adapter_bypass` + `guard_runner_direct_adapter_bypass` · `test_r3ySync001_*` |

## OPEN (hygiene) — Round 3 PROMPT_18 R3Y follow-ups

Non-blocking for read-only audit; **Wave C merge closed α-3 / β-2 rows** (2026-06-24). **`R3Y-TEST-DEPTH-001` closed** Wave 4 prep @ 2026-07-01 — see RESOLVED §Wave 4 prep.

_(no OPEN rows)_

---

## DEFERRED — Round 4 (API / frontend / notifications)

Round4 rows are productization work and remain blocked by R3H-05. They do not authorize wrapping vague proposed-disabled source shells. Batch04 may start only after `PASS_ROUND4_REAL_DATA_READY` or `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR`; `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` blocks these rows.

| ID            | Item                                                                                 | Resolution phase | Task hook         | Blocks 017? | Closure test / evidence                          |
| ------------- | ------------------------------------------------------------------------------------ | ---------------- | ----------------- | ----------- | ------------------------------------------------ |
| R2-GAP-2      | No source capability list HTTP API                                                   | **Round 4**      | task **024**      | No          | `GET /api/sources` or documented deferral to 025 |
| R4-API-SEC-3  | `test_pageSizeAboveAbsoluteLimit_returnsQueryTooLarge`                               | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-4  | `test_pageSizeContract_matchesDocs`                                                  | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-5  | `test_frontendPageContracts_doNotUseStale500Limit`                                   | **Round 4**      | **024** + **027** | No          | frontend + API contract test                     |
| R4-API-SEC-6  | `test_unauthenticatedRequest_returnsAuthRequired`                                    | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-7  | `test_prodWithoutToken_failsStartup`                                                 | **Round 4**      | **024**           | No          | startup pytest                                   |
| R4-API-SEC-8  | `test_prodDisabledAuth_failsStartup`                                                 | **Round 4**      | **024**           | No          | startup pytest                                   |
| R4-API-SEC-9  | `test_devDisabledAuthOnlyAllowedOnLoopback`                                          | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-10 | `test_pageSizeAboveLimit_returnsQueryTooLarge`                                       | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-11 | `test_singleLocalToken_mapsToAdmin`                                                  | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-12 | `test_deferredRolesNotEnabledInPhase1` / `test_viewerAgentRoles_areDeferredInPhase1` | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-13 | `test_prodAdminMutationWithoutToken_returnsAuthRequired`                             | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-NOTIF-1    | `test_phase1NotificationThrottle_excludesDesktop`                                    | **Round 4**      | **028**           | No          | `test_notifications.py`                          |
| R4-NOTIF-2    | `test_notificationModule_containsNoActiveDesktopThrottleInPhase1`                    | **Round 4**      | **028**           | No          | module scan test                                 |
| R4-NOTIF-3    | `test_notificationDedupKey_isStable`                                                 | **Round 4**      | **028**           | No          | unit pytest                                      |
| R4-FE-2       | Notification Center `/notifications` page                                            | **Round 4**      | **026** + **028** | No          | frontend route + e2e smoke                       |
| R4-FE-3       | Layer 1–5 dashboard pages                                                            | **Round 4**      | **027**           | No          | page contract snapshots                          |

---

## DEFERRED — Round 5+

Round5 release/security rows must carry Round3H source posture forward (`READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`, `DISABLED_SOURCE`, source limitation, route/evidence status). Round5 must not implement missing source adapters or hide incomplete source admission.

| ID        | Item                        | Resolution phase | Task hook           | Blocks 017? | Closure test / evidence |
| --------- | --------------------------- | ---------------- | ------------------- | ----------- | ----------------------- |
| R2-RISK-5 | gitleaks / full security CI | **Round 5**      | **035** integration | No          | CI job green            |

---

## RESOLVED (reference)

| ID                        | Item                                                                | Closed                    | Evidence                                                                                                                                                                                                                                                                 |
| ------------------------- | ------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R2.5-1..5                 | Repair-package Round 2 contract drift                               | 2026-06-19                | `ROUND2_REPAIR_ALIGNMENT_TRACKER.md`                                                                                                                                                                                                                                     |
| R2.5-6                    | Domain schedulable before domain_allowed (DISABLED_SOURCE priority) | 2026-06-19                | `base_adapter.py` · `test_fetch_disabledDomain_returnsDisabledSourceBeforeDomainAllowed`                                                                                                                                                                                 |
| PROC-R2.5-1               | Round 2.5 merge + historical handoff                                | 2026-06-19                | PR #15 → `7ce283a` on `master`                                                                                                                                                                                                                                           |
| R4-API-SEC-1              | `test_apiSecurityContract_isSingleAuthorityForQueryBudget`          | R2.5                      | `test_api_security_contract.py`                                                                                                                                                                                                                                          |
| R4-API-SEC-2              | `test_resourceLimitsApiLimits_matchApiSecurityContract`             | R2.5                      | same                                                                                                                                                                                                                                                                     |
| D4-P3-1                   | Starlette/httpx deprecation warning                                 | PR #11                    | `httpx2` dev dep                                                                                                                                                                                                                                                         |
| R2-HYG-2                  | Windows pytest temp                                                 | `pyproject.toml` basetemp | D1-P3-1                                                                                                                                                                                                                                                                  |
| D3-P3-1                   | Five vendor skeleton adapter classes                                | Round 2 Batch B           | `test_adapter_skeletons.py`                                                                                                                                                                                                                                              |
| D5-P1-2                   | Manifest protocol uses historical archive                           | by design                 | frozen Batch D archive                                                                                                                                                                                                                                                   |
| D1-P3-2                   | GitNexus tooling                                                    | setup                     | `node .gitnexus/run.cjs analyze`                                                                                                                                                                                                                                         |
| R2.6-B1                   | Round2.6 Phase B contract gate tests (016A–016E contracts)          | 2026-06-19                | `tests/test_source_capabilities.py` · `tests/test_source_route_planner.py` · `tests/test_datasource_service.py` · `tests/test_module_boundaries.py` · `tests/test_qmd_data_cli.py` · `tests/test_dependency_extras_contract.py` · `tests/test_platform_source_matrix.py` |
| R2.6-B2                   | Module boundary static checker                                      | 2026-06-19                | `scripts/check_module_boundaries.py`                                                                                                                                                                                                                                     |
| R2.6-B3                   | Phase A self-check migrated to historical task evidence             | 2026-06-19                | historical routing-service gate evidence                                                                                                                                                                                                                                 |
| R3-EARLY-DB-INSPECT-CLI   | Read-only DB inspect CLI Phase A                                    | 2026-06-20                | `backend/app/ops/db_inspector.py` · `scripts/qmd_ops.py` · `tests/test_ops_db_inspector.py`                                                                                                                                                                              |
| DB-R3-001                 | Project data root inventory documented via inspect                  | 2026-06-20                | db-inspect evidence                                                                                                                                                                                                                                                      |
| DB-R3-002                 | Read-only DB open + key table counts                                | 2026-06-20                | same inspect JSON + no-mutation tests                                                                                                                                                                                                                                    |
| DOC-R3-001                | Round 2.6 PASS in `ROUND3_HANDOFF.md`                               | 2026-06-20                | `docs/ROUND3_HANDOFF.md` §Round 2.6 gate                                                                                                                                                                                                                                 |
| DOC-R3-002                | Registry authority on early close plan                              | 2026-06-20                | `ROUND3_EARLY_CLOSE_PLAN.md` authority block                                                                                                                                                                                                                             |
| R3-PARTIAL-2              | Vendor FetchPort E2E + full_load skeleton closure                   | 2026-06-20                | `tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath`; `tests/test_sync_jobs.py::test_syncJob_fullLoad_createdToPlanned_recordsEvent`                                                                                                |
| R3-EARLY-PROD-SCALE-BENCH | Production-equivalent smoke Batch 1 evidence                        | 2026-06-20                | production-equivalent smoke evidence                                                                                                                                                                                                                                     |

## DEFERRED — Round 3 Batch 1 audit design acceptances (2026-06-20)

Does **not** block finish-work or 017; documented per audit A9 synthesis — must remain visible until closed or superseded.

| ID              | Item                                              | Resolution phase            | Task hook               | Blocks 017? | Closure test / evidence                       |
| --------------- | ------------------------------------------------- | --------------------------- | ----------------------- | ----------- | --------------------------------------------- |
| R3-AUDIT-DEF-02 | AC-E2E-1 live vendor soak beyond fixture/skeleton | **User-authorized staging** | cross-ref `R2.6-IMPL-8` | No          | Authorized staging E2E with real vendor fetch |

---

## RESOLVED — Wave 4 prep hygiene (2026-07-01)

| ID                        | Item                                              | Evidence                                                                                                               |
| ------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| R2-GAP-1                  | `init_db --sync-registry` CI one-liner            | `scripts/init_db.py` · `tests/test_qmd_data_cli.py` · `docs/ops/data_sync_quick_reference.md`                          |
| R3-AUDIT-DEF-01           | db_inspector YAML SSOT + drift tests              | `tests/test_contract_drift_ops_write.py`                                                                               |
| R3-B25-PERF-BUDGET-01     | Authoritative perf-budget CI artifact             | `scripts/ci_perf_budget_artifact.py` · `.github/workflows/ci.yml` · `tests/test_production_equivalent_smoke_budget.py` |
| R3-B25-HYG-03             | production-equivalent benchmark artifact (alias)  | same as `R3-B25-PERF-BUDGET-01`                                                                                        |
| D3-P1-2                   | C901 write-path — ADR wont-fix                    | `docs/decisions/ADR-004-write-path-complexity-ceiling.md` · `tests/test_batch6_wave4_prep_closure.py`                  |
| A9-P2-01                  | `manual_review_queue.priority` app-layer ADR-002  | `docs/decisions/ADR-002-db-check-vs-app-validation.md` · `tests/test_round3f_migration_residuals.py`                   |
| R2-RISK-4                 | App-layer-only `priority` documented + tested     | same as `A9-P2-01`                                                                                                     |
| R3-B6-021-O-01            | Layer3 malformed `bars[]` fail-closed             | `snapshot_builder.py` · `test_layer3Snapshot_malformedBarElement_rejects`                                              |
| R3-B6-021-O-02            | Deterministic rebuild full row tuple              | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash`                                                          |
| R3Y-TEST-DEPTH-001        | Lineage cluster runtime-strong depth (AUD-07 L05) | `tests/test_batch6_wave4_prep_closure.py` · `--collect-only` on four lineage anchor tests                              |
| WAVE-B-HYG-01             | Four SSOT `Last reconciled` normalize equality    | `test_r3yRegistrySlice_alpha2LastReconciled` · 复验 2026-07-01 exit 0                                                  |
| WAVE-B-HYG-02             | Four SSOT `Last reconciled` normalize equality    | `test_r3yRegistrySlice_alpha2LastReconciled`                                                                           |
| WAVE-B-HYG-03             | `QMD_SYNC_ALLOW_ADAPTER` ops escape hatch         | `docs/architecture/06_deployment_and_local_ops.md`                                                                     |
| ACC-SANDBOX-GUARD-001     | Isolated fred/baostock sync sandbox guard         | `assert_sandbox_db_allowed(..., allow_isolated_data_root)` · `test_sandboxDbAllowed_*` · denies `user-live`            |
| ACC-MIGRATION-MATRIX-PATH | migration coverage archive path                   | `docs/schema/MIGRATION_COVERAGE.md` · archive `round3v-layer5-model-schema-reconcile`                                  |
| ACC-REGISTRY-CROSS-001    | Registry cross-check depth                        | `tests/test_batch6_wave4_prep_closure.py` · `collect_pytest_node_id`                                                   |

---

## Verification baseline

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
cd frontend && npm run typecheck && npm run test
```

**Round 3 entry (017):** registry has **no OPEN rows**; all other items DEFERRED with phase or RESOLVED.

---
