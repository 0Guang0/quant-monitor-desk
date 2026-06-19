# Original Plan Trace — 06-19-round2-6-routing-service-gate

## Round / Batch

Round 2.6 Phase C/D. This task executes the implementation and production-equivalent validation slice after `06-19-round2-6-contract-gate` passes.

## Task cards → MASTER AC mapping

| Task card | Required content | MASTER §2 AC |
|---|---|---|
| `016A_define_source_capability_registry.md` | Implement CapabilityRegistry; close adapter-domain reconciliation | AC-C1, AC-C2 |
| `016B_define_source_route_plan_and_datasource_service.md` | Implement SourceRoutePlan, RoutePlanner, DataSourceService, runner service path | AC-C3, AC-C4, AC-C5 |
| `016C_define_module_boundary_contract.md` | Keep boundary checker green after refactor | AC-C6 |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | Error code/docs anchor preserved in service outcomes | AC-C7 |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md` | Keep qmt/xqshare disabled and not auto-probed | AC-C8 |
| `016F_define_prod_equivalent_scale_benchmark.md` | Extend production-equivalent smoke and ResourceGuard metrics | AC-D1, AC-D2 |
| Contract Gate task | Parent tests and audit must pass | AC-PRE |
| `ROUND2_6_PHASE_A_SELF_CHECK.md` | Clean up root self-check after migration | AC-D4 |

## Path corrections

- Prefer `job_event_log.payload_json` for RoutePlan persistence before Round3. Do not add migration unless ADR + user approval.
- FastAPI diagnostics and frontend UI are Round4, not this task.
- qmt_xqshare adapter/source enablement is optional and requires user authorization; not this task.
