# Original Plan Trace — 06-19-round2-6-contract-gate

## Round / Batch

Round 2.6 — Datasource Routing & Ops Alignment. This Trellis task covers Phase B only: executable contracts and boundary tests before Phase C implementation.

## Task cards → MASTER AC mapping

| Task card | Required content | MASTER §2 AC |
|---|---|---|
| `016A_define_source_capability_registry.md` | Capability registry tests; domain reconciliation | AC-B1, AC-B2 |
| `016B_define_source_route_plan_and_datasource_service.md` | RoutePlan/DataSourceService contract tests | AC-B3, AC-B4 |
| `016C_define_module_boundary_contract.md` | Static import boundary checker | AC-B5 |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | Data CLI/error docs contract tests | AC-B6 |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md` | Platform matrix tests; disabled qmt_xqshare | AC-B7 |
| `016F_define_prod_equivalent_scale_benchmark.md` | Benchmark requirements handed off to Task 2 | AC-B9 |
| `ROUND2_6_PHASE_A_SELF_CHECK.md` | Domain mismatch and cleanup decision | AC-B1, AC-B8, AC-B10 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | Reconcile stale deferred rows | AC-B8 |

## Input files already identified

| Path | Category | Manifest |
|---|---|---|
| `docs/implementation_tasks/README.md` | global order | required |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | global execution | required |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | testing | required |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | resources | required |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` | task format | required |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/README.md` | round scope | required |
| `specs/datasource_registry/source_registry.yaml` | current source/domain authority | required |
| `specs/datasource_registry/source_capabilities.yaml` | capability contract | required |
| `specs/contracts/source_capability_contract.yaml` | capability tests | required |
| `specs/contracts/source_route_contract.yaml` | route tests | required |
| `specs/contracts/datasource_service_contract.yaml` | service boundary tests | required |
| `specs/contracts/module_boundary_contract.yaml` | import checker | required |
| `specs/contracts/platform_source_matrix.yaml` | platform tests | required |
| `specs/contracts/data_cli_contract.yaml` | CLI contract tests | required |
| `specs/contracts/dependency_extras_contract.yaml` | dependency contract tests | required |
| `specs/contracts/reference_adoption_guardrails.yaml` | red flags | required |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | deferred state authority | required |

## Path corrections

- Task cards are Phase A design-only, but this Trellis task intentionally implements their `Future implementation tasks` testing/checking slice.
- `DataSourceService` / `SourceRoutePlanner` production implementation is deferred to sibling task `06-19-round2-6-routing-service-gate`.
- Current adapter domain names intentionally remain production code until Task 2; Task 1 must expose them with tests and optionally compatibility-map tests if no production refactor is done here.
