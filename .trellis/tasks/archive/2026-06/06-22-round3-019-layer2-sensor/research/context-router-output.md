# Context Router Output

- task: `06-22-round3-019-layer2-sensor`
- modules: layer1_axes, layer2_sensors, ops

## Source authorities

- `design` docs/modules/layer1_global_regime_panel.md — layer1_axes design authority
- `design` docs/architecture/module_boundary_matrix.md — layer1_axes design authority
- `design` docs/architecture/04_data_architecture.md — layer1_axes design authority
- `contract` specs/contracts/layer1_axis_contract.yaml — layer1_axes contract
- `contract` specs/contracts/snapshot_lineage_contract.yaml — layer1_axes contract
- `contract` specs/contracts/resource_limits.yaml — layer1_axes contract
- `policy` docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md — layer1_axes rule
- `policy` docs/implementation_tasks/GLOBAL_TESTING_POLICY.md — layer1_axes rule
- `policy` docs/quality/production_live_pilot_policy.md — layer1_axes rule
- `task-card` docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md — layer1_axes implementation task
- `task-card` docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md — layer1_axes implementation task
- `design` docs/modules/layer2_cross_asset_sensor.md — layer2_sensors design authority
- `contract` specs/contracts/layer2_sensor_contract.yaml — layer2_sensors contract
- `policy` docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md — layer2_sensors rule
- `task-card` docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md — layer2_sensors implementation task
- `design` docs/modules/ops_and_performance.md — ops design authority
- `design` docs/ops/verification_commands.md — ops design authority
- `design` docs/ops/performance_limits.md — ops design authority
- `design` docs/ROUND3_HANDOFF.md — ops design authority
- `contract` specs/contracts/ops_health_check_contract.yaml — ops contract
- `contract` specs/contracts/ops_db_inspect_contract.yaml — ops contract
- `contract` specs/contracts/review_sandbox_contract.yaml — ops contract
- `task-card` docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md — ops implementation task

## Tests

- `tests/test_layer1_axis_loader.py` — Layer1 axis loader registry and snapshot behavior
- `tests/test_layer1_interpretation.py` — Layer 1 feature, interpretation, lineage, and WriteManager integration tests.
- `tests/test_layer1_ingestion_gates.py` — Layer 1 ingestion Phase 0 gate tests (Round 3 Batch 2.5 §8.1).
- `tests/test_layer1_observation_ingestion.py` — Layer 1 observation ingestion pipeline tests (Batch 2.5 §8.2–8.5).
- `tests/test_observation_mapper.py` — Focused tests for observation_mapper boundary paths (audit A05-P1-01 / A04-P2-01).
- `tests/test_batch25_production_data_gate.py` — Batch 2.5 evidence is staged-only, not production-live readiness
- `tests/test_batch275_live_pilot_gate.py` — Batch 2.75 live pilot fail-closed gate and route readiness
- `tests/test_production_live_pilot_policy.py` — Batch 2.75 fail-closed pilot policy documentation
- `tests/test_fred_staged_semantics.py` — FRED / macro_supplementary staged-only semantics (B2.5-O-05)
- `tests/test_layer2_sensor_loader.py` — 验证 Layer2 sensor loader、snapshot、observation、lineage、ResourceGuard 行为
- `tests/test_snapshot_lineage_kernel.py` — 覆盖范围：core/snapshot_lineage 共享内核；测试对象：校验与 DB tuple 映射；目的：三层层 lineage 去重后行为不变。
- `tests/test_batch3_staged_downstream_gate.py` — 确保 Batch 3 只能 staged-only，不得被误读为 production-live readiness
- `tests/test_resource_guard.py` — ResourceGuard HARD_STOP and metrics contract
- `tests/test_staged_pilot.py` — Staged pilot sandbox boundaries; does not open production-live
- `tests/test_ops_db_inspector.py` — Ops DB inspector tests (Round 3 Batch 1).
- `tests/test_ops_interface_probe.py` — Ops interface_probe + mutation_proof wiring tests (OP-06).
- `tests/test_interface_probe_018c.py` — 018C low-cost data-interface probe tests.
- `tests/test_production_gate.py` — ADV-A5-002: production_gate.py smoke tests.
- `tests/test_round3_verification_command_matrix.py` — Round 3 verification command matrix — doc index and gate-test discoverability.
- `tests/test_round3_audit_registry_alignment.py` — Round 3 Batch 2.5 / Batch 2.75 audit follow-up 文档对齐测试。
- `tests/test_unresolved_item_task_coverage.py` — 确保未闭合项不会在 Plan 阶段因只读原始任务卡而遗漏。
