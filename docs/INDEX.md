# Documentation Index

Navigation hub for **Quant Monitor Desk**. For a compact project map see [`MIGRATION_MAP.md`](../MIGRATION_MAP.md) at the repository root.

## Start here

| File                                       | Topic                            |
| ------------------------------------------ | -------------------------------- |
| [START_HERE.md](START_HERE.md)             | First-use role router            |
| [OPERATOR_GUIDE.md](OPERATOR_GUIDE.md)     | Local ops and safe data sync     |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)   | Development and Round task entry |
| [RESEARCHER_GUIDE.md](RESEARCHER_GUIDE.md) | Layer/review research entry      |

> **权威边界**：`MANIFEST.json` 登记的 docs/specs 为 2026-06-19 修复包权威口径。本索引及 `implementation_tasks/**/plans/`、`DECISIONS.md`、Batch 状态文件为**项目实施补充**，不得覆盖 MANIFEST 权威文件。口径差见 [`quality/REPAIR_IMPORT_CODE_GAP_LEDGER.md`](quality/REPAIR_IMPORT_CODE_GAP_LEDGER.md)。

## Architecture

| File                                                                                | Topic                                  |
| ----------------------------------------------------------------------------------- | -------------------------------------- |
| [00_project_overview.md](architecture/00_project_overview.md)                       | Goals, v1.6 scope, layer definitions   |
| [01_context_and_scope.md](architecture/01_context_and_scope.md)                     | Problem framing                        |
| [02_solution_strategy.md](architecture/02_solution_strategy.md)                     | Solution approach                      |
| [03_runtime_flows.md](architecture/03_runtime_flows.md)                             | Runtime orchestration                  |
| [04_data_architecture.md](architecture/04_data_architecture.md)                     | Data layers, stores                    |
| [05_module_map.md](architecture/05_module_map.md)                                   | Five-layer framework + modules         |
| [module_boundary_matrix.md](architecture/module_boundary_matrix.md)                 | Round2.6 import/module boundary matrix |
| [09_phase_plan.md](architecture/09_phase_plan.md)                                   | Phased delivery                        |
| [07_project_directory_structure.md](architecture/07_project_directory_structure.md) | Directory layout                       |
| [08_decision_log_index.md](architecture/08_decision_log_index.md)                   | ADR index                              |

## Modules

See [`docs/modules/`](modules/) — one file per implementation module (data sync, layers, API, agent, ops, etc.).

**Canonical pointers:** Some topics were split from merged docs; see [`modules/README.md`](modules/README.md) for authoritative vs compatibility-only files (FastAPI/frontend, validation/write concurrency).

## Operations

| File                                                                       | Topic                                                         |
| -------------------------------------------------------------------------- | ------------------------------------------------------------- |
| [backup_and_recovery.md](ops/backup_and_recovery.md)                       | Backup policy                                                 |
| [db_inspect_cli.md](ops/db_inspect_cli.md)                                 | QMD read-only DB inspect CLI design                           |
| [performance_limits.md](ops/performance_limits.md)                         | ResourceGuard authority                                       |
| [ops_and_performance_v1_2.md](ops/ops_and_performance_v1_2.md)             | Ops handbook _(legacy filename; content is current)_          |
| [logs_health_audit.md](ops/logs_health_audit.md)                           | Logging and audit                                             |
| [layer3_config_health_check.md](ops/layer3_config_health_check.md)         | Layer 3 config checks                                         |
| [daily_weekly_monthly_checklist.md](ops/daily_weekly_monthly_checklist.md) | Routine checklists                                            |
| [agent_workflow_boundaries.md](ops/agent_workflow_boundaries.md)           | `.cursor`/`.trellis` trust boundaries                         |
| [verification_commands.md](ops/verification_commands.md)                   | Canonical audit/CI commands (Windows)                         |
| [user_intervention_policy.md](ops/user_intervention_policy.md)             | Agent vs user intervention boundaries                         |
| [generated/project_map.generated.md](generated/project_map.generated.md)   | Machine-generated project map (run `generate_project_map.py`) |
| [data_sync_quick_reference.md](ops/data_sync_quick_reference.md)           | Round2.6 safe data sync quick reference                       |
| [data_sync_command_matrix.md](ops/data_sync_command_matrix.md)             | Round2.6 CLI command matrix                                   |
| [TROUBLESHOOTING.md](ops/TROUBLESHOOTING.md)                               | Troubleshooting entry                                         |
| [ERROR_CODE_GUIDE.md](ops/ERROR_CODE_GUIDE.md)                             | Error code guide                                              |
| [incident_playbook.md](ops/incident_playbook.md)                           | Incident playbook                                             |
| [privacy_data_flow.md](ops/privacy_data_flow.md)                           | Local-only/privacy data flow                                  |
| [qmt_xqshare_setup.md](ops/qmt_xqshare_setup.md)                           | Optional qmt_xqshare setup boundary                           |
| [agent_security_policy.md](ops/agent_security_policy.md)                   | Agent 安全与 D-12 固定来源                                    |
| [config_secret_policy.md](ops/config_secret_policy.md)                     | Secret 与 `.env.local`（D-03）                                |
| [migration_recovery_policy.md](ops/migration_recovery_policy.md)           | Migration 备份恢复（D-06）                                    |
| [privacy_retention_policy.md](ops/privacy_retention_policy.md)             | 留存与归档（D-05）                                            |
| [schema/MIGRATION_COVERAGE.md](schema/MIGRATION_COVERAGE.md)               | Design schema vs applied migrations matrix                    |
| [schema/MIGRATION_008_PLAN.md](schema/MIGRATION_008_PLAN.md)               | Planned migration 008 DB CHECK constraints                    |

## ADRs

| ADR                                                                  | Decision                |
| -------------------------------------------------------------------- | ----------------------- |
| [ADR-0001](adr/ADR-0001-use-duckdb-local-first.md)                   | DuckDB local-first      |
| [ADR-0002](adr/ADR-0002-agent-readonly-boundary.md)                  | Agent read-only         |
| [ADR-0003](adr/ADR-0003-layer1-standardization-only.md)              | L1 standardization only |
| [ADR-0004](adr/ADR-0004-layer3-shock-anchor-model.md)                | L3 shock-anchor model   |
| [ADR-0005](adr/ADR-0005-primary-validation-fallback-source-model.md) | Source roles            |

## Issue registries

| File                                                           | Topic                                                                  |
| -------------------------------------------------------------- | ---------------------------------------------------------------------- |
| [UNRESOLVED_ISSUES_REGISTRY.md](UNRESOLVED_ISSUES_REGISTRY.md) | Current unresolved/deferred/open issues, gaps, risks, and improvements |
| [RESOLVED_ISSUES_REGISTRY.md](RESOLVED_ISSUES_REGISTRY.md)     | Resolved/closed issues and closure evidence                            |
| [AUDIT_DEFERRED_REGISTRY.md](AUDIT_DEFERRED_REGISTRY.md)       | Original audit deferred registry and policy                            |

## Quality

| File                                                                                               | Topic                                 |
| -------------------------------------------------------------------------------------------------- | ------------------------------------- |
| [final_package_rules.md](quality/final_package_rules.md)                                           | Deliverable rules                     |
| [self_check_and_audit.md](quality/self_check_and_audit.md)                                         | Audit checklist                       |
| [production_live_pilot_policy.md](quality/production_live_pilot_policy.md)                         | Batch 2.75 production/live pilot gate |
| [staged_acceptance_policy.md](quality/staged_acceptance_policy.md)                                 | 分阶段验收                            |
| [REPAIR_IMPORT_CODE_GAP_LEDGER.md](quality/REPAIR_IMPORT_CODE_GAP_LEDGER.md)                       | 导入后代码口径差（Phase 3）           |
| [REPAIR_IMPORT_PHASE2_NON_MANIFEST_REVIEW.md](quality/REPAIR_IMPORT_PHASE2_NON_MANIFEST_REVIEW.md) | 非 MANIFEST 文件删留审查              |

## API & agent contracts (narrative)

See [`docs/api/`](api/) for FastAPI routes and agent tool documentation.

## Implementation tasks

Start at [`implementation_tasks/README.md`](implementation_tasks/README.md).

Round 3 Batch 2.5 bridge entry: [`018A_layer1_observation_ingestion_bridge.md`](implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md).

Round 3 Batch 2.75 pilot entry: [`018B_production_live_pilot_gate.md`](implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md).

Forward planning (Round 3D/3E): [`PROJECT_IMPLEMENTATION_ROADMAP.md`](../PROJECT_IMPLEMENTATION_ROADMAP.md) · Batch 01 entry: [`ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/README.md`](implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/README.md).

Plan-stage inputs for turning original tasks into Trellis frozen plans:

- [TASK_INPUT_CONTEXT_INDEX.md](implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md)
- [GLOBAL_EXECUTION_RULES.md](implementation_tasks/GLOBAL_EXECUTION_RULES.md)
- [GLOBAL_TESTING_POLICY.md](implementation_tasks/GLOBAL_TESTING_POLICY.md)
- [GLOBAL_RESOURCE_LIMITS.md](implementation_tasks/GLOBAL_RESOURCE_LIMITS.md)
- [GLOBAL_TASK_TEMPLATE.md](implementation_tasks/GLOBAL_TASK_TEMPLATE.md)

## Specs (machine-readable)

Repository root: [`specs/`](../specs/)

- [`specs/schema/schema.sql`](../specs/schema/schema.sql)
- [`specs/contracts/api_security_contract.yaml`](../specs/contracts/api_security_contract.yaml) — API 分页权威
- [`specs/contracts/runtime_versions.md`](../specs/contracts/runtime_versions.md) — `uv.lock` / 验收命令（D-01）
- [`specs/contracts/ops_db_inspect_contract.yaml`](../specs/contracts/ops_db_inspect_contract.yaml) — read-only DB inspect CLI contract
- [`specs/contracts/`](../specs/contracts/)
- [`specs/datasource_registry/source_capabilities.yaml`](../specs/datasource_registry/source_capabilities.yaml) — Round2.6 source capability matrix
- [`specs/contracts/source_capability_contract.yaml`](../specs/contracts/source_capability_contract.yaml)
- [`specs/contracts/source_route_contract.yaml`](../specs/contracts/source_route_contract.yaml)
- [`specs/contracts/datasource_service_contract.yaml`](../specs/contracts/datasource_service_contract.yaml)
- [`specs/contracts/module_boundary_contract.yaml`](../specs/contracts/module_boundary_contract.yaml)
- [`specs/contracts/backtest_metric_contract.yaml`](../specs/contracts/backtest_metric_contract.yaml)
- [`specs/contracts/user_input_privacy_contract.yaml`](../specs/contracts/user_input_privacy_contract.yaml)
- [`specs/contracts/reference_adoption_guardrails.yaml`](../specs/contracts/reference_adoption_guardrails.yaml)
- [`specs/layer1_axes/`](../specs/layer1_axes/)
- [`specs/layer3_global_industry_chains/`](../specs/layer3_global_industry_chains/)
