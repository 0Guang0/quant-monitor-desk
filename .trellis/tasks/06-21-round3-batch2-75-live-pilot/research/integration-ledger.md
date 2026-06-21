# Integration Ledger — Batch 2.75

> Plan 5c · v3 context packing

## 打包策略

| 策略            | 含义                        |
| --------------- | --------------------------- |
| inline          | MASTER 已总结               |
| summary+pointer | MASTER 摘要 + 原稿          |
| pointer         | implement.jsonl extract/for |

## ledger

| source                                                                                                                | category     | strategy        | master_anchor    | for_ac_step         |
| --------------------------------------------------------------------------------------------------------------------- | ------------ | --------------- | ---------------- | ------------------- |
| `docs/quality/batch275_user_authorization_2026-06-21.md`                                                              | **decision** | pointer         | §0.6             | for:AC-P0           |
| `docs/quality/PENDING_USER_DECISIONS.md`                                                                              | **decision** | summary+pointer | §0.7             | extract:D-11        |
| `018B` §3.1 + ENV-E1-DGS10 shape                                                                                      | **business** | pointer         | §1.1, §2 AC-P3-5 | for:AC-P3-5         |
| `docs/architecture/layer1_ingestion_refactor_rollback_plan.md`                                                        | architecture | pointer         | §3.2             | extract:§6          |
| `docs/quality/production_live_pilot_policy.md`                                                                        | rule         | summary+pointer | §0.7             | for:AC-P0           |
| `specs/datasource_registry/source_registry.yaml`                                                                      | contract     | pointer         | §0.6             | for:AC-P2           |
| `specs/datasource_registry/source_capabilities.yaml`                                                                  | contract     | pointer         | §0.6             | for:AC-P2,P3        |
| `specs/contracts/source_capability_contract.yaml`                                                                     | contract     | pointer         | §0.6             | for:AC-P2           |
| `specs/contracts/platform_source_matrix.yaml`                                                                         | contract     | pointer         | §0.6             | for:AC-P2           |
| `specs/contracts/source_route_contract.yaml`                                                                          | contract     | pointer         | §0.6             | for:AC-P2           |
| `specs/contracts/datasource_service_contract.yaml`                                                                    | contract     | pointer         | §0.6             | for:AC-P3           |
| `specs/contracts/ops_db_inspect_contract.yaml`                                                                        | contract     | pointer         | §0.6             | for:AC-P1,P3        |
| `specs/contracts/data_quality_rules.yaml`                                                                             | contract     | pointer         | §0.6             | for:AC-P4           |
| `specs/contracts/resource_limits.yaml`                                                                                | contract     | pointer         | §10              | for:AC-P45          |
| `docs/modules/datasource_service.md`                                                                                  | design       | pointer         | §3.4             | for:AC-P3           |
| `docs/modules/source_route_plan.md`                                                                                   | design       | pointer         | §3.4             | for:AC-P2           |
| `docs/ops/db_inspect_cli.md`                                                                                          | ops          | pointer         | §8.3             | for:AC-P1           |
| `backend/app/datasources/service.py`                                                                                  | **wiring**   | pointer         | §4               | for:AC-P2,P3        |
| `backend/app/datasources/route_planner.py`                                                                            | **wiring**   | pointer         | §4               | for:AC-P2           |
| `backend/app/ops/db_inspector.py`                                                                                     | **wiring**   | pointer         | §4               | for:AC-P1           |
| `backend/app/core/resource_guard.py`                                                                                  | **wiring**   | pointer         | §3.4             | for:AC-P2,P3        |
| `backend/app/validators/data_quality.py`                                                                              | **wiring**   | pointer         | §3.4             | for:AC-P4           |
| `scripts/production_equivalent_smoke.py`                                                                              | **wiring**   | pointer         | §8.7             | for:AC-P45          |
| `research/batch275-live-pilot-gate-tests.md`                                                                          | rule         | pointer         | §8               | for:§8              |
| `research/vertical-slices.md`                                                                                         | rule         | pointer         | §5               | for:§5              |
| `research/integration-ledger.md`                                                                                      | rule         | pointer         | §0.3             | for:§0.3            |
| `MASTER.plan.md`                                                                                                      | rule         | inline          | §0               | yes                 |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                                                                     | registry     | pointer         | §0.6, §8.1       | for:AC-REG-1        |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                  | registry     | pointer         | §0.6             | for:AC-PM\*         |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                                                                    | registry     | pointer         | §0.6             | for:AC-P5-3         |
| `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`                                                                 | registry     | pointer         | §0.6             | for:AC-PRE          |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                  | map          | pointer         | §0.6             | for:AC-PM\*         |
| `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                                                                       | gate         | pointer         | §11              | for:AC-P5-4         |
| `docs/modules/data_sources.md`                                                                                        | design       | pointer         | §0.6             | for:AC-P2           |
| `docs/modules/source_capability_registry.md`                                                                          | design       | pointer         | §0.6             | for:AC-P1-3         |
| `docs/modules/data_validation_and_conflict.md`                                                                        | design       | pointer         | §0.6             | for:AC-P4-5         |
| `docs/modules/write_manager.md`                                                                                       | design       | pointer         | §0.6             | for:AC-P4           |
| `specs/contracts/write_contract.yaml`                                                                                 | contract     | pointer         | §0.6             | for:AC-P4-2         |
| `docs/quality/staged_acceptance_policy.md`                                                                            | policy       | filtered        | —                | do not reuse staged |
| `backend/app/validators/source_conflict.py`                                                                           | wiring       | pointer         | §4               | for:AC-P4-5         |
| `specs/contracts/source_conflict_rules.yaml`                                                                          | contract     | pointer         | §0.6             | for:AC-P4-5         |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` | business     | pointer         | §8.7             | for:AC-P45          |
| `specs/layer1_axes/.../environment_axis_indicator_spec.yaml`                                                          | spec         | pointer         | §0.6             | for:AC-P3-5         |
| `backend/app/layer1_axes/ingestion.py`                                                                                | wiring       | filtered        | §3.3             | do NOT reuse        |
| `scripts/production_gate.py`                                                                                          | wiring       | pointer         | §10              | for:§10             |
| `scripts/check_doc_links.py`                                                                                          | wiring       | pointer         | §10              | for:§10             |
