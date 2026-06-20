# Phase 0 Source Context Matrix — Batch 2.5

> AC-P0-1 · 018A §5.1–5.5 · MASTER §0.6 + §0.6.1 filter annex

| Source                                             | Category      | Strategy     | Relevance                          | Execute must-read          | Phase 0 status                                                                           |
| -------------------------------------------------- | ------------- | ------------ | ---------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------- |
| `018A_layer1_observation_ingestion_bridge.md`      | original-task | inline §2/§8 | Five-phase bridge definition       | Plan only                  | Summarized in MASTER                                                                     |
| `research/original-plan-trace.md` §5.1–5.5         | index annex   | pointer      | **Full §5 path enumeration (97+)** | AC-P0-1 normative          | Execute matrix is summary; annex authoritative                                           |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2          | index         | inline       | Batch placement                    | Plan only                  | OK                                                                                       |
| `MIGRATION_MAP.md`                                 | map           | inline       | Module boundaries                  | Plan only                  | OK                                                                                       |
| `docs/architecture/03_runtime_flows.md`            | architecture  | pointer      | fetch→validate→write               | Phase 3–4                  | Read via ledger                                                                          |
| `docs/architecture/04_data_architecture.md`        | architecture  | pointer      | raw/clean zones                    | Phase 3–4                  | Read via ledger                                                                          |
| `docs/architecture/module_boundary_matrix.md`      | architecture  | pointer      | Layer1≠adapter                     | **AC-P0-4**                | Gate test enforces                                                                       |
| `docs/modules/datasource_service.md`               | design        | pointer      | Factory facade                     | Phase 3                    | Contract tests green                                                                     |
| `docs/modules/write_manager.md`                    | rule          | pointer      | Clean write                        | Phase 4                    | Prerequisite tests green                                                                 |
| `docs/modules/data_validation_and_conflict.md`     | design        | pointer      | Validators                         | Phase 4                    | Prerequisite tests green                                                                 |
| `specs/schema/schema.sql`                          | schema        | pointer      | Contract DDL                       | **AC-P0-2**                | Lags migration 011                                                                       |
| `backend/app/db/migrations/011_layer1_tables.sql`  | migration     | pointer      | axis_observation DDL               | **AC-P0-2**                | Authoritative for Layer1                                                                 |
| `specs/contracts/source_route_contract.yaml`       | contract      | pointer      | No silent fallback                 | Phase 2                    | Route tests green                                                                        |
| `specs/contracts/datasource_service_contract.yaml` | contract      | pointer      | Factory boundary                   | **AC-P0-3**                | Service tests green                                                                      |
| `specs/contracts/write_contract.yaml`              | contract      | pointer      | WriteRequest                       | Phase 4                    | Write tests green                                                                        |
| `specs/contracts/snapshot_lineage_contract.yaml`   | contract      | pointer      | fetch ids/hashes                   | Phase 4                    | Lineage tests green                                                                      |
| `specs/datasource_registry/source_registry.yaml`   | registry      | pointer      | Primary/Validation                 | **AC-P0-3**                | Gate test enforces                                                                       |
| `backend/app/datasources/service.py`               | wiring        | pointer      | create_adapter @ L190              | Phase 3                    | Static boundary OK                                                                       |
| `backend/app/sync/pipeline.py`                     | wiring        | E11a pointer | Sync job validation                | Phase 0 contrast           | See db_contract_gate                                                                     |
| `backend/app/sync/orchestrator.py`                 | wiring        | E11a pointer | Job runner                         | Phase 0                    | Read-only                                                                                |
| `backend/app/sync/runners.py`                      | wiring        | E11a pointer | Optional narrow                    | Phase 0                    | **No narrow改** default                                                                  |
| `backend/app/layer1_axes/*.py`                     | wiring        | pointer      | Batch 2 engines                    | Phase 4 snapshots          | Loader tests green                                                                       |
| `configs/layer1_axes.yml`                          | config        | pointer      | Allowlist + frozen indicator       | **Phase 2 prep must-read** | Boot read #41; gate test `test_layer1Ingestion_phase0_layer1AxesConfig_resolvesSpecRoot` |
| `GLOBAL_*.md`                                      | rule          | inline §0.7  | Execution policy                   | AC-GATE                    | Summarized                                                                               |
| `docs/quality/PENDING_USER_DECISIONS.md`           | decision      | inline §0.7  | D-01..D-12                         | AC-PRE                     | No reopen                                                                                |

### §0.6.1 filtered (not must-read Execute)

| Path                              | Filter reason                                  |
| --------------------------------- | ---------------------------------------------- |
| migrations 004–010                | Ingestion history; 011 sufficient for axis DDL |
| `fetch_log.py`, `route_models.py` | Covered via service/route_planner              |
| `sync/jobs.py`, `qmd_ops.py`      | Non Layer1 narrow path                         |

### Gap classification

| Gap                              | Classification                                      | Owner hook                   |
| -------------------------------- | --------------------------------------------------- | ---------------------------- |
| `ingestion.py` missing           | EXPECTED B2.5-O-04                                  | §8.2–8.5                     |
| `schema.sql` missing axis tables | **DEFERRED B2.5-O-02**                              | `AUDIT_DEFERRED_REGISTRY.md` |
| FRED primary vs registry         | **DEFERRED B2.5-O-05** staged `macro_supplementary` | AC-P2-0 gate test            |
| `axis_observation` DB CHECK      | **DEFERRED B2.5-O-03**                              | ADR-002 app-layer            |

### DB inventory coverage (018A Phase 1 prep)

| Table                                                                | `DbInspector.KEY_TABLES`        | Phase 0 verified                                        |
| -------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------- |
| `fetch_log`, `file_registry`, `validation_report`, `write_audit_log` | YES                             | prereq tests                                            |
| `axis_observation`, snapshots, lineage, registries                   | YES (remediated)                | `test_dbInspect_layer1AxisTables_presentAfterMigration` |
| `instrument_registry`, `security_bar_1d`                             | YES (`FUTURE_PHASE_KEY_TABLES`) | exists:false until Layer 5                              |

### E11a boot reads (pipeline contrast)

| Path                               | Read | Recorded             |
| ---------------------------------- | ---- | -------------------- |
| `backend/app/sync/pipeline.py`     | YES  | `8.0-boot-reads.txt` |
| `backend/app/sync/orchestrator.py` | YES  | same                 |
| `backend/app/sync/runners.py`      | YES  | same                 |

`phase0_source_context_matrix complete — adversarial remediation applied`
