# ROUND 2.6 — Datasource Routing & Ops Alignment

> Phase A scope: only design documents, specs/contracts, and execution plans. Do not modify code.

## Purpose

Round2 re-audit closeout has resolved the prior runner/lineage/DB CHECK/backfill/reconcile/vendor-fixture gaps. Round2.6 adds the missing design layer before Round3 modeling expands the system:

1. Source capability matrix.
2. SourceRoutePlan and DataSourceService facade.
3. Module boundary matrix.
4. Data sync quick reference and error guides.
5. Platform/source matrix and optional qmt_xqshare design.
6. Production-equivalent scale benchmark plan.

## Tasks

| Task | Topic |
|---|---|
| `016A_define_source_capability_registry.md` | SourceCapabilityRegistry |
| `016B_define_source_route_plan_and_datasource_service.md` | SourceRoutePlan + DataSourceService |
| `016C_define_module_boundary_contract.md` | ModuleBoundaryMatrix |
| `016D_define_data_sync_quick_reference_and_error_guides.md` | Ops quick reference and error guides |
| `016E_define_platform_source_matrix_and_qmt_xqshare.md` | Platform source matrix and optional qmt_xqshare |
| `016F_define_prod_equivalent_scale_benchmark.md` | Production-equivalent scale benchmark |

## Non-goals

- No code changes in Phase A.
- No dependency changes.
- No QMT/xqshare enablement.
- No trading, auto-login, silent fallback, or arbitrary strategy execution.
