# PROMPT_07 — feature/round3-019-layer2-sensor

Use this prompt in a fresh session. The session must create the branch/worktree first, then run the full Plan -> Execute flow for `019`.

## 1. Branch / worktree setup

- Branch to create: `feature/round3-019-layer2-sensor`
- Base branch: `master` after `integration/round3` has merged, or `integration/round3` if explicitly instructed before merge-back
- Suggested worktree path: `../quant-monitor-desk-wt-round3-019-layer2-sensor`
- Target merge branch: `integration/round3` for active integration, then master through coordinator

Before creating the branch, confirm:

- `R3-B3-STAGED-DOWNSTREAM-GATE` is closed and merged into the chosen base.
- Prompt files and task cards are visible in the base.
- Working tree is clean.

## 2. Mission

Implement Round 3 Batch 3 `019` Layer2 cross-asset sensor under staged-only downstream semantics.

Implement:

- `cross_asset_registry`
- `cross_asset_observation`
- `cross_asset_daily_snapshot`
- `double_count_guard`
- Layer2 snapshot lineage and no-future-data tests

## 3. Required Plan-stage input index

Read and summarize these before writing MASTER.plan.md:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `docs/modules/layer2_cross_asset_sensor.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/local_file_system.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

Also read the merged PROMPT 01 evidence if present:

- `.trellis/tasks/06-22-round3-batch3-staged-gate/execute-evidence/merge_gate_report.md`

## 4. Allowed files

Only after MASTER/AUDIT plan names them:

- `backend/app/layer2_sensors/`
- `tests/test_layer2_sensor_loader.py` or narrow Layer2 tests
- `specs/contracts/layer2_sensor_contract.yaml` if contract gaps are discovered
- `specs/contracts/snapshot_lineage_contract.yaml` only if this branch owns it and 023A is read-only for that file
- task-local Trellis planning/evidence files

## 5. Forbidden files / behavior

- No production-live readiness claim.
- No production DB writes.
- No external vendor writes.
- No live FRED.
- No use of `tdx_pytdx` as production source.
- No treating `tdx_pytdx` disabled candidate as Primary.
- No default source enablement.
- No fallback from Eastmoney hist to TDX/Sina/QMT/xqshare.
- No Layer3/4/5 implementation.
- No full Layer1 standardized field copy into Layer2.
- No trading/order semantics.
- No front-end final layout.

## 6. Required implementation safeguards

- Start with RED tests for staged-only behavior, double counting, lineage, and no future data.
- `double_count_guard` must prove Layer1 slow variables are display/reference only and not re-counted.
- Main-contract switch must be an explicit event, not a silent switch.
- ResourceGuard must protect any batch-like operation.
- WriteManager must gate any clean-table write.
- Every snapshot must carry `snapshot_id`, `snapshot_type`, `layer_id`, `as_of_timestamp`, `source_fetch_ids`, `source_content_hashes`, `rule_version`, `code_version`, `parameter_hash`, and upstream snapshot fields where applicable.

## 7. Verification commands

Run at minimum:

- `pytest tests/test_layer2_sensor_loader.py -q` if created or updated
- `pytest tests/test_batch3_staged_downstream_gate.py -q`
- `pytest tests/test_batch25_production_data_gate.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `python -m compileall backend/app/layer2_sensors tests`
- `ruff check backend/app/layer2_sensors tests/test_layer2_sensor_loader.py` if code changed

Run broader `pytest -q` before final merge if feasible. If a command is blocked or unavailable, record exact reason.

## 8. Done criteria

- MASTER/AUDIT plan explicitly states staged-only limitations.
- Layer2 tests prove no double-counting and no future-data leakage.
- No production data/source readiness is claimed.
- No core file group conflict with 023A.
- Merge report includes changed files, tests, ResourceGuard status, DB mutation status, and remaining deferred items.
