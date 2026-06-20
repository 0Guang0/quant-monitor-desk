# Phase 0 Source Context Crosswalk — 018A §5 → Execute matrix

> F-A3-03 · annex authority: `research/original-plan-trace.md` §5.1–5.5  
> Summary matrix: `execute-evidence/phase0_source_context_matrix.md`

## Purpose

The execute matrix is a **filtering summary**. This crosswalk maps every `original-plan-trace.md` annex row to Phase 0 closure status so auditors can trace AC-P0-1 without re-reading 97+ paths.

## §5.1 Root & protocol

| Path                                 | Matrix row      | Phase 0 status                      |
| ------------------------------------ | --------------- | ----------------------------------- |
| `README.md`                          | implicit (root) | Boot #7                             |
| `MIGRATION_MAP.md`                   | matrix          | Plan only                           |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | matrix          | Plan only                           |
| `GLOBAL_EXECUTION_RULES.md`          | `GLOBAL_*.md`   | Boot #11; summarized MASTER         |
| `GLOBAL_TESTING_POLICY.md`           | `GLOBAL_*.md`   | Boot #12                            |
| `GLOBAL_RESOURCE_LIMITS.md`          | `GLOBAL_*.md`   | Boot #13 → resource_limits contract |
| `staged_acceptance_policy.md`        | implicit        | Boot #9                             |
| `PENDING_USER_DECISIONS.md`          | matrix          | Boot #8; no reopen                  |

## §5.2 Architecture & modules

| Path                              | Matrix row | Phase 0 status                          |
| --------------------------------- | ---------- | --------------------------------------- |
| `03_runtime_flows.md`             | matrix     | Boot #14; runtime_flow_contract pointer |
| `04_data_architecture.md`         | matrix     | Boot #15                                |
| `module_boundary_matrix.md`       | matrix     | **AC-P0-4** gate test                   |
| `layer1_global_regime_panel.md`   | implicit   | Boot #17                                |
| `datasource_service.md`           | matrix     | Boot #18; AC-P0-3                       |
| `write_manager.md`                | matrix     | Boot #22; Phase 4 prereq                |
| `data_validation_and_conflict.md` | matrix     | Boot #21                                |
| `db_inspect_cli.md`               | implicit   | Boot #24; Phase 1 prep                  |
| `ADR-001-*.md`                    | implicit   | Boot #26                                |
| `ADR-002-*.md`                    | implicit   | Boot #48; B2.5-O-03 deferred            |

## §5.3 Contracts / schema / registry

| Path                                 | Matrix / gate     | Phase 0 status                |
| ------------------------------------ | ----------------- | ----------------------------- |
| `schema.sql`                         | matrix + gate §1  | Lags 011 — B2.5-O-02          |
| `011_layer1_tables.sql`              | matrix + gate §1  | Authoritative DDL             |
| migrations 004–010                   | gate §1b          | Chain tests green             |
| `source_route_contract.yaml`         | matrix + gate §2  | AC-P0 silent-fallback tests   |
| `datasource_service_contract.yaml`   | matrix + gate §2  | Factory boundary tests        |
| `write_contract.yaml`                | matrix + gate §2  | Observation target mapping    |
| `snapshot_lineage_contract.yaml`     | matrix + gate §2  | Lineage JSON tests            |
| `data_quality_rules.yaml`            | gate §2           | layer1_rules section test     |
| `ops_db_inspect_contract.yaml`       | gate §2           | KEY_TABLES parity             |
| `runtime_flow_contract.yaml`         | gate §2 (F-A3-06) | Boot #51; pointer             |
| `resource_limits.yaml`               | gate §2 (F-A3-06) | Boot #36; resource_guard test |
| `platform_source_matrix.yaml`        | gate §2 (F-A3-06) | Boot #40; staged route        |
| `reference_adoption_guardrails.yaml` | gate §2 (F-A3-06) | Filtered — no external refs   |
| `source_registry.yaml`               | matrix            | AC-P0-3 registry gate         |
| `source_capabilities.yaml`           | implicit          | Boot #38                      |

## §5.4 Registry / decisions

| Path                            | Status                    |
| ------------------------------- | ------------------------- |
| `AUDIT_DEFERRED_REGISTRY.md`    | Boot #71; B2.5-O-02..O-06 |
| `UNRESOLVED_ISSUES_REGISTRY.md` | Boot #72                  |
| `RESOLVED_ISSUES_REGISTRY.md`   | Boot #73                  |

## §5.5 Wiring (code)

| Path                       | Matrix / boot    | Phase 0 status                                                             |
| -------------------------- | ---------------- | -------------------------------------------------------------------------- |
| `db/connection.py`         | Boot #52         | prereq                                                                     |
| `db/write_manager.py`      | Boot #55         | prereq                                                                     |
| `db/validation_gate.py`    | Boot #56; E11b   | `test_layer1Ingestion_phase0_validationGateModule_exposesDbValidationGate` |
| `core/resource_guard.py`   | Boot #57; E11b   | `test_layer1Ingestion_phase0_resourceGuard_exposesCheckBeforeFetch`        |
| `datasources/service.py`   | matrix           | `create_adapter` boundary                                                  |
| `sync/pipeline.py`         | E11a             | Contrast doc gate §3                                                       |
| `ops/db_inspector.py`      | implicit         | Phase 1 inventory dependency                                               |
| `layer1_axes/*.py`         | matrix           | Batch 2 engines green                                                      |
| `configs/layer1_axes.yml`  | matrix (F-A3-16) | **Phase 2 must-read**; ENV-E1-DGS10 gate                                   |
| `layer1_axes/ingestion.py` | EXPECTED gap     | B2.5-O-04 → §8.3+                                                          |

## Filtered (not Execute must-read)

Per `phase0_source_context_matrix.md` §0.6.1 and `original-plan-trace.md` §已过滤.

`phase0_source_context_crosswalk complete — F-A3-03`
