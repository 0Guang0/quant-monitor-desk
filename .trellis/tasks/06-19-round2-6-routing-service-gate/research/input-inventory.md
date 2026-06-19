# Input Inventory — 06-19-round2-6-routing-service-gate

P0i complete

## 1. Prerequisite task inputs

| Path | Why required |
|---|---|
| `.trellis/tasks/06-19-round2-6-contract-gate/MASTER.plan.md` | Parent contract gate scope and AC. |
| Parent Contract Gate audit result | Runtime prerequisite checked in MASTER §8.0; do not hard-index future `audit.report.md` before it exists. |
| Parent migrated Phase A findings | Runtime prerequisite checked in MASTER §8.0/§8.12; do not hard-index future `research/phase-a-self-check.md` before Task 1 creates it. |
| Parent execute evidence | Runtime evidence source after Task 1 executes; not a plan-time required path. |

## 2. Original implementation-task authority

| Path | Why required |
|---|---|
| `docs/implementation_tasks/README.md` | Round3 gate. |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | no trading, no silent fallback, no auto-login. |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | tests and mock boundaries. |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | ResourceGuard and production-equivalent limits. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md` | CapabilityRegistry implementation. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md` | Route/service implementation. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016C_define_module_boundary_contract.md` | Boundary checker must remain green after refactor. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` | CLI/error output constraints. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016E_define_platform_source_matrix_and_qmt_xqshare.md` | QMT/xqshare disabled constraints. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` | Production-equivalent benchmark scope. |

## 3. Specs/contracts

| Path | Why required |
|---|---|
| `specs/datasource_registry/source_registry.yaml` | current source/domain authority. |
| `specs/datasource_registry/source_capabilities.yaml` | capability matrix. |
| `specs/contracts/source_capability_contract.yaml` | capability tests. |
| `specs/contracts/source_route_contract.yaml` | route model/status/persistence. |
| `specs/contracts/datasource_service_contract.yaml` | service facade contract. |
| `specs/contracts/module_boundary_contract.yaml` | import constraints. |
| `specs/contracts/platform_source_matrix.yaml` | qmt/xqshare platform rules. |
| `specs/contracts/data_cli_contract.yaml` | smoke/dry-run CLI expectations. |
| `specs/contracts/reference_adoption_guardrails.yaml` | forbidden adoptions. |

## 4. Code touchpoints

| Path | Intended operation |
|---|---|
| `backend/app/datasources/capability_registry.py` | Create. |
| `backend/app/datasources/route_models.py` | Create. |
| `backend/app/datasources/route_planner.py` | Create. |
| `backend/app/datasources/service.py` | Create. |
| `backend/app/datasources/adapters/*.py` | Update supported_domains or add tested compatibility map. |
| `backend/app/datasources/adapters/__init__.py` | Keep factory; mark service-internal in production path. |
| `backend/app/sync/runners.py` | Refactor fetch entry to service/fetch callable without breaking tests. |
| `backend/app/sync/orchestrator.py` | Wire service/fetch callable if needed. |
| `backend/app/sync/event_payload.py` | Extend route payload fields if using job_event_log. |
| `scripts/production_equivalent_smoke.py` | Extend service-path smoke. |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | Final reconciliation before Round3. |
| `docs/implementation_tasks/README.md` | Remove temp self-check gate reference if migrated. |
| `ROUND2_6_PHASE_A_SELF_CHECK.md` | Clean up after migration. |

## 5. Tests expected

- Parent Task 1 tests must exist and remain green.
- Add/extend service-path E2E tests.
- Add production-equivalent smoke assertions.
- Add RoutePlan payload/log tests.

## 6. Exclusions

- No FastAPI diagnostics implementation.
- No frontend UI implementation.
- No BacktestReviewEngine or Review Sandbox implementation.
- No qmt_xqshare adapter implementation or source enablement without user authorization.
- No new schema migration unless payload_json route persistence is proven insufficient and user approves ADR.
