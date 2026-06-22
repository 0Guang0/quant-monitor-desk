# PROMPT_19 — feature/round3-real-data-staged-pilot-v2

Use this prompt in a fresh implementation session. Create the branch/worktree first, then execute the staged real-data pilot v2 expansion task.

## 1. Branch / worktree setup

- Branch to create: `feature/round3-real-data-staged-pilot-v2`
- Base branch: latest user-confirmed `master` after mainline closeout
- Suggested worktree path: `../quant-monitor-desk-wt-feature-r3-real-data-staged-pilot-v2`
- Target merge branch: `integration/round3` or next user-confirmed integration branch

Before starting, confirm:

- Mainline closeout is visible.
- Existing dirty files are not overwritten.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md` exists.
- If `review/round3-post-r3x-strict-adversarial-audit` has already completed, read its PASS/WARN/BLOCK before executing.

## 2. Mission

Expand the completed PROMPT_14 staged pilot into a bounded v2 pilot using real sources under staged/raw/sandbox-only constraints. The goal is to expose real data quality, route, schema, validation, conflict, and no-mutation behavior — not to enable production clean writes.

## 3. Required task card

Read and follow exactly:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`

## 4. Mandatory /to-issues slicing

During plan stage, use `/to-issues` and create vertical issue slices matching the task card:

- R3Y-SP2-01 pilot v2 plan/caps
- R3Y-SP2-02 baostock expanded sample
- R3Y-SP2-03 cninfo metadata expanded sample
- R3Y-SP2-04 akshare validation retry/re-defer
- R3Y-SP2-05 route preview matrix v2
- R3Y-SP2-06 validation report v2
- R3Y-SP2-07 conflict summary v2
- R3Y-SP2-08 production no-mutation proof v2
- R3Y-SP2-09 close/re-defer matrix

Each issue must have RED/GREEN evidence or explicit non-testable rationale. Do not submit only a script that “runs”; submit issue-level evidence.

## 5. Required read index

At minimum read and summarize all required files from the task card, especially:

- `AGENTS.md`, `CLAUDE.md`, `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`
- `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/mutation_proof.py`
- `backend/app/datasources/`, `backend/app/storage/`, `backend/app/db/`
- `tests/test_staged_pilot.py`, `tests/test_datasource_service.py`, `tests/test_source_route_planner.py`, `tests/test_raw_store.py`, `tests/test_db_validation_gate.py`

Do not stop at this index. Follow route planner, adapter, validation, storage, and evidence references before implementing.

## 6. Allowed source scope

Allowed:

- `baostock` small expanded sample
- `cninfo` metadata small expanded sample
- `akshare` validation-only retry/re-defer

Deferred / forbidden in this branch:

- TDX live fetch
- QMT / xqshare enablement
- Yahoo default enablement
- live FRED
- production clean write
- full market scan
- full history backfill

## 7. Allowed files

Only after plan names them:

- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/mutation_proof.py`
- narrow pilot-required datasource/storage fixes
- `tests/test_staged_pilot.py`
- `tests/test_vendor_fetch_e2e.py`
- `tests/test_production_live_pilot_policy.py`
- task-local Trellis evidence

## 8. Verification

Run at minimum:

```bash
python -m pytest tests/test_staged_pilot.py -q
python -m pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q
python -m pytest tests/test_raw_store.py tests/test_db_validation_gate.py tests/test_ops_db_inspector.py tests/test_production_live_pilot_policy.py -q
```

If vendor fixture/e2e is added:

```bash
python -m pytest tests/test_vendor_fetch_e2e.py -q
```

## 9. Done criteria

- All `/to-issues` slices have evidence.
- route preview v2, fetch summary v2, raw/staging manifest v2, validation report v2, conflict summary v2, no-mutation proof v2, closeout v2 are produced.
- At least one allowed source/domain succeeds or all failures are explicitly classified.
- Production clean tables remain unmodified.
- No production-live readiness claim.
