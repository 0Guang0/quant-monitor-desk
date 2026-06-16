# Documentation Index

Navigation hub for **Quant Monitor Desk**. For a compact project map see [`MIGRATION_MAP.md`](../MIGRATION_MAP.md) at the repository root.

## Architecture

| File | Topic |
|------|-------|
| [00_project_overview.md](architecture/00_project_overview.md) | Goals, v1.6 scope, layer definitions |
| [01_context_and_problem.md](architecture/01_context_and_problem.md) | Problem framing |
| [02_solution_strategy.md](architecture/02_solution_strategy.md) | Solution approach |
| [03_runtime_flows.md](architecture/03_runtime_flows.md) | Runtime orchestration |
| [04_data_architecture.md](architecture/04_data_architecture.md) | Data layers, stores |
| [05_module_map.md](architecture/05_module_map.md) | Five-layer framework + modules |
| [06_phase_plan.md](architecture/06_phase_plan.md) | Phased delivery |
| [07_project_directory_structure.md](architecture/07_project_directory_structure.md) | Directory layout |
| [08_decision_log_index.md](architecture/08_decision_log_index.md) | ADR index |

## Modules

See [`docs/modules/`](modules/) — one file per implementation module (data sync, layers, API, agent, ops, etc.).

## Operations

| File | Topic |
|------|-------|
| [backup_and_recovery.md](ops/backup_and_recovery.md) | Backup policy |
| [performance_limits.md](ops/performance_limits.md) | ResourceGuard authority |
| [ops_and_performance_v1_2.md](ops/ops_and_performance_v1_2.md) | Ops handbook |
| [logs_health_audit.md](ops/logs_health_audit.md) | Logging and audit |
| [layer3_config_health_check.md](ops/layer3_config_health_check.md) | Layer 3 config checks |
| [daily_weekly_monthly_checklist.md](ops/daily_weekly_monthly_checklist.md) | Routine checklists |

## ADRs

| ADR | Decision |
|-----|----------|
| [ADR-0001](adr/ADR-0001-use-duckdb-local-first.md) | DuckDB local-first |
| [ADR-0002](adr/ADR-0002-agent-readonly-boundary.md) | Agent read-only |
| [ADR-0003](adr/ADR-0003-layer1-standardization-only.md) | L1 standardization only |
| [ADR-0004](adr/ADR-0004-layer3-shock-anchor-model.md) | L3 shock-anchor model |
| [ADR-0005](adr/ADR-0005-primary-validation-fallback-source-model.md) | Source roles |

## Quality

| File | Topic |
|------|-------|
| [final_package_rules.md](quality/final_package_rules.md) | Deliverable rules |
| [self_check_and_audit.md](quality/self_check_and_audit.md) | Audit checklist |

## API & agent contracts (narrative)

See [`docs/api/`](api/) for FastAPI routes and agent tool documentation.

## Implementation tasks

Start at [`implementation_tasks/README.md`](implementation_tasks/README.md).

Global rules (read before any task):

- [GLOBAL_EXECUTION_RULES.md](implementation_tasks/GLOBAL_EXECUTION_RULES.md)
- [GLOBAL_TESTING_POLICY.md](implementation_tasks/GLOBAL_TESTING_POLICY.md)
- [GLOBAL_RESOURCE_LIMITS.md](implementation_tasks/GLOBAL_RESOURCE_LIMITS.md)
- [GLOBAL_TASK_TEMPLATE.md](implementation_tasks/GLOBAL_TASK_TEMPLATE.md)

## Specs (machine-readable)

Repository root: [`specs/`](../specs/)

- [`specs/schema/schema.sql`](../specs/schema/schema.sql)
- [`specs/contracts/`](../specs/contracts/)
- [`specs/layer1_axes/`](../specs/layer1_axes/)
- [`specs/layer3_global_industry_chains/`](../specs/layer3_global_industry_chains/)
