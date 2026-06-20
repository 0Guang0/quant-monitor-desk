# Phase 0 DB / Contract Gate — Batch 2.5 (post adversarial audit remediation)

> AC-P0-2 · schema/migration/契约偏差分类 · remediated 2026-06-20

## 1. schema.sql vs migration 011

| Table                          | migration 011 | schema.sql | Verdict                |
| ------------------------------ | ------------- | ---------- | ---------------------- |
| `axis_registry`                | YES           | NO         | **DEFERRED B2.5-O-02** |
| `axis_indicator_registry`      | YES           | NO         | B2.5-O-02              |
| `axis_indicator_profile`       | YES           | NO         | B2.5-O-02              |
| `axis_observation`             | YES           | NO         | B2.5-O-02              |
| `axis_feature_snapshot`        | YES           | NO         | B2.5-O-02              |
| `axis_interpretation_snapshot` | YES           | NO         | B2.5-O-02              |
| `axis_snapshot_lineage`        | YES           | NO         | B2.5-O-02              |

**Authority:** `apply_migrations()` through `011_layer1_tables` (runtime). `schema.sql` sync tracked in `AUDIT_DEFERRED_REGISTRY.md` B2.5-O-02.

**Closure tests:** `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`, `test_layer1Migration_axisObservation_columnsMatchModuleSpec`, `tests/test_layer1_axis_loader.py::test_layer1Migration_createsRegistryTables`.

## 1b. Ingestion migrations 004–011

| Migration | Ingestion objects                                                                 | Gate test                                                       |
| --------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 004       | `source_registry`, `fetch_log`                                                    | `test_layer1Ingestion_phase0_ingestionChainTablesAfterApply`    |
| 005       | `validation_report`, `data_quality_log`, `source_conflict`, `manual_review_queue` | same                                                            |
| 006       | `data_sync_job`, `job_event_log`                                                  | same                                                            |
| 007       | sync rebuild + `write_audit_log` columns                                          | `test_schema_migration.py`                                      |
| 008       | lineage JSON columns on `validation_report`                                       | Batch 2.6 tests                                                 |
| 009       | `fetch_log` / registry CHECK                                                      | `test_audit_remediation.py` (Phase 0 block)                     |
| 010       | `validation_report` NOT NULL hardening                                            | migration apply                                                 |
| 011       | 7× `axis_*` tables                                                                | `test_layer1Ingestion_phase0_applyMigrations_createsAxisTables` |

## 2. Contract vs code

| Contract                               | Verification                                                                                                     | Status                                                             |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `write_contract.yaml`                  | `test_layer1Ingestion_phase0_writeContractMapsToObservationTarget` + reject_if mapping test                      | PASS (target `axis_observation` write **RESOLVED** B2.5-O-04 §8.5) |
| `snapshot_lineage_contract.yaml`       | `test_layer1Lineage_phase0_ddlStoresSerializedFetchIds` + Batch 2 lineage tests                                  | PASS (JSON in VARCHAR documented)                                  |
| `source_route_contract.yaml`           | `test_layer1Ingestion_phase0_sourceRouteContract_forbidsSilentFallback` + `test_noSilentFallbackCopied`          | PASS                                                               |
| `datasource_service_contract.yaml`     | `test_datasource_service.py::test_apiAndAgentCannotImportAdapterFactory`                                         | PASS                                                               |
| `data_cli_contract.yaml`               | `test_layer1Ingestion_phase0_dataCliContract_loadable` + `test_data_cli_contract.py`                             | PASS                                                               |
| `data_quality_rules.yaml` layer1_rules | `test_layer1Ingestion_phase0_dataQualityRules_layer1SectionExists`                                               | PASS                                                               |
| `layer1_axis_contract.yaml`            | `test_layer1Ingestion_phase0_layer1AxisContractRequiredFields`                                                   | PASS                                                               |
| `ops_db_inspect_contract.yaml`         | `test_dbInspect_layer1AxisTables_presentAfterMigration` + KEY_TABLES parity test                                 | PASS (remediated)                                                  |
| `runtime_flow_contract.yaml`           | Boot read #51; `03_runtime_flows.md` cross-ref; Phase 3–4 write chain                                            | PASS (pointer; enforcement via write_contract + pipeline contrast) |
| `resource_limits.yaml`                 | Boot read #36; `GLOBAL_RESOURCE_LIMITS.md` + `test_layer1Ingestion_phase0_resourceGuard_exposesCheckBeforeFetch` | PASS (Phase 3 micro-fetch will enforce)                            |
| `platform_source_matrix.yaml`          | Boot read #40; registry `source_registry.yaml` primary/validation roles                                          | PASS (staged route AC-P2-0; B2.5-O-05 live FRED deferred)          |
| `reference_adoption_guardrails.yaml`   | Filtered per original-plan-trace §5.3 (no external reference adoption this batch)                                | N/A — documented exclusion                                         |

## 3. §3.4 wiring vs `sync/pipeline.py`

`Layer1ObservationIngestionService.commit_*` calls validators + `DbValidationGate` + `WriteManager` **directly** (not `SyncValidationPipeline`).

| `write_contract.validation_gate.reject_if` | Planned hook                                   |
| ------------------------------------------ | ---------------------------------------------- |
| `validation_status == FAILED`              | `DbValidationGate` + `DataQualityValidator`    |
| `source_conflict_severity == severe`       | `DbValidationGate` + `SourceConflictValidator` |
| `manual_review_required == true …`         | `DbValidationGate`                             |

**Boot reads (E11a):** `pipeline.py`, `orchestrator.py`, `runners.py` — recorded in `8.0-boot-reads.txt`.

## 4. axis_observation DDL / write path

| Item                          | Status                                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------- |
| DDL columns (17)              | `observation_contract.py` + `test_layer1Migration_axisObservation_columnsMatchModuleSpec`                      |
| DB CHECK on timestamps        | **DEFERRED B2.5-O-03** — ADR-002 app-layer; `test_layer1Ingestion_phase0_axisObservation_noDbCheck_classified` |
| WriteManager clean write      | **RESOLVED B2.5-O-04** — `test_layer1Observation_cleanWrite_usesWriteManager` (§8.5 PH-A4)                     |
| fetch_log → observation trace | Via `validation_report.source_fetch_ids_json` + `content_hash` (`FETCH_TO_OBSERVATION_TRACE_VIA`)              |

## 5. Staged route (AC-P2-0)

| Field                   | Value                                                                       |
| ----------------------- | --------------------------------------------------------------------------- |
| Indicator               | `ENV-E1-DGS10`                                                              |
| Declared primary        | `FRED:DGS10` (**DEFERRED B2.5-O-05** live)                                  |
| Staged domain/operation | `macro_supplementary` / `fetch_macro_series`                                |
| Registry                | `domain_roles.macro_supplementary.primary=akshare` (remediated)             |
| Gate test               | `test_layer1Ingestion_phase0_frozenIndicator_stagedRouteCapabilityDeclared` |

## 6. DB inventory (Phase 1 prep)

| Table                                    | `DbInspector.KEY_TABLES`        | Notes                         |
| ---------------------------------------- | ------------------------------- | ----------------------------- |
| `axis_observation`                       | YES (remediated)                | Phase 1 baseline row counts   |
| `fetch_log`, `file_registry`, …          | YES                             | ingestion evidence            |
| `instrument_registry`, `security_bar_1d` | YES (`FUTURE_PHASE_KEY_TABLES`) | `exists: false` until Layer 5 |

## 7. BLOCKERs

None for Phase 0 → Phase 1 transition.

`phase0_db_contract_gate complete — adversarial remediation applied`
