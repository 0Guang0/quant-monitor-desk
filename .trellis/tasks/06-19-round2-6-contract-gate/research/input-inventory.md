# Input Inventory — 06-19-round2-6-contract-gate

P0i complete

## 1. Trellis protocol inputs

| Path | Why required |
|---|---|
| `AGENTS.md` | Project Trellis/GitNexus gates. |
| `.cursor/skills/trellis-plan/SKILL.md` | Plan Phase P0 protocol. |
| `.trellis/spec/guides/complex-task-planning-protocol.md` | Complex task file/phase contract. |
| `.trellis/spec/guides/templates/MASTER.plan.md` | MASTER structure. |
| `.trellis/spec/guides/templates/AUDIT.plan.md` | Audit structure. |

## 2. Original implementation-task authority

| Path | Why required |
|---|---|
| `docs/implementation_tasks/README.md` | Global order; Round2.6 before Round3. |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | No-action, no silent fallback, Round2.6 red lines. |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | Test assertions and mock boundary. |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | ResourceGuard and prod-equivalent limits. |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` | Task-card conventions. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/README.md` | Round2.6 scope. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md` | CapabilityRegistry future tests. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md` | RoutePlan/DataSourceService future tests. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016C_define_module_boundary_contract.md` | Module-boundary checker. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` | Data CLI/error guide tests. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016E_define_platform_source_matrix_and_qmt_xqshare.md` | Platform matrix / disabled qmt_xqshare tests. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` | Phase D benchmark handoff, not implemented in this task. |

## 3. Specs/contracts to enforce in this task

| Path | Why required |
|---|---|
| `specs/datasource_registry/source_registry.yaml` | Current source/domain authority. |
| `specs/datasource_registry/source_capabilities.yaml` | New capability matrix. |
| `specs/contracts/source_capability_contract.yaml` | Required tests and current adapter-domain gap. |
| `specs/contracts/source_route_contract.yaml` | RoutePlan object/status/fallback contract. |
| `specs/contracts/datasource_service_contract.yaml` | Direct adapter factory boundary; service fetch sequence. |
| `specs/contracts/module_boundary_contract.yaml` | Import boundary rules. |
| `specs/contracts/platform_source_matrix.yaml` | QMT/xqshare default-disabled rules. |
| `specs/contracts/data_cli_contract.yaml` | Dry-run / route-preview CLI contract. |
| `specs/contracts/dependency_extras_contract.yaml` | Optional extras gate. |
| `specs/contracts/diagnostics_api_contract.yaml` | Read-only diagnostics, used for future route preview boundaries. |
| `specs/contracts/reference_adoption_guardrails.yaml` | Prohibit trading/auto-login/silent fallback. |

## 4. Existing code/test touchpoints for Execute impact analysis

| Path | Intended operation in this task |
|---|---|
| `backend/app/datasources/adapters/*.py` | Read; tests will expose legacy `supported_domains`. No production refactor in Task 1. |
| `backend/app/datasources/source_registry.py` | Read; source/domain authority for tests. |
| `backend/app/datasources/adapters/__init__.py` | Read; factory boundary tests may scan imports. |
| `backend/app/sync/runners.py` | Read; no refactor yet. |
| `backend/app/sync/event_payload.py` | Read; informs Phase C route persistence decision. |
| `tests/test_source_registry.py` | Existing source registry test patterns. |
| `tests/test_adapter_skeletons.py` | Existing adapter-domain tests. |
| `tests/test_vendor_fetch_e2e.py` | Existing fixture E2E baseline. |
| `tests/test_documentation_index.py` | Existing docs index gate. |

## 5. Outputs expected from this task

| Path | Type |
|---|---|
| `tests/test_source_capabilities.py` | New tests. |
| `tests/test_source_route_planner.py` | New contract tests, may be xfail only until Task 2 if scoped in MASTER §8. |
| `tests/test_datasource_service.py` | Boundary tests. |
| `tests/test_module_boundaries.py` | Module-boundary tests. |
| `scripts/check_module_boundaries.py` | New static checker. |
| `tests/test_platform_source_matrix.py` | Platform source tests. |
| `tests/test_data_cli_contract.py` | Contract-only dry-run tests. |
| `tests/test_dependency_extras_contract.py` | Default dependency boundary. |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | Reconcile resolved/still-deferred rows. |

## 6. Deliberately excluded from this task

- `backend/app/datasources/service.py`, `route_planner.py`, `capability_registry.py` implementation — Task 2.
- Sync runner service refactor — Task 2.
- Production-equivalent scale smoke changes — Task 2.
- Frontend/API diagnostics implementation — Round4 tasks 024/026/027.
