# PROMPT_20 — feature/round3-readonly-data-health-v1

Use this prompt in a fresh implementation session. Create the branch/worktree first, then execute the read-only data health v1 task.

## 1. Branch / worktree setup

- Branch to create: `feature/round3-readonly-data-health-v1`
- Base branch: latest user-confirmed `master` after mainline closeout
- Suggested worktree path: `../quant-monitor-desk-wt-feature-r3-readonly-data-health-v1`
- Target merge branch: `integration/round3` or next user-confirmed integration branch

Before starting, confirm:

- Mainline closeout is visible.
- Existing dirty files are not overwritten.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md` exists.
- If staged pilot v2 already completed, read its evidence; otherwise use PROMPT_14 evidence as required input.

## 2. Mission

Implement a minimal read-only data health capability over staged pilot evidence and bounded manifests. This must detect real data quality and lineage issues without writing production DB, running migrations, executing source fetch, or enabling production-live readiness.

This branch must not be a CLI shell only. It must implement actual checks as vertically sliced issues.

## 3. Required task card

Read and follow exactly:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`

## 4. Mandatory /to-issues slicing

During plan stage, use `/to-issues` and create vertical issue slices matching the task card:

- R3Y-DH-01 DataHealth rule model
- R3Y-DH-02 Manifest loader
- R3Y-DH-03 Daily bar health
- R3Y-DH-04 Metadata health
- R3Y-DH-05 Source lineage health
- R3Y-DH-06 Staleness/window health
- R3Y-DH-07 Report builder
- R3Y-DH-08 CLI/service entrypoint
- R3Y-DH-09 Integration with staged pilot evidence

Each issue must be independently testable. Do not implement only a command wrapper.

## 5. Required read index

At minimum read and summarize all required files from the task card, especially:

- `AGENTS.md`, `CLAUDE.md`, `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/ops/data_health_cli.md`
- `docs/ops/db_inspect_cli.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/write_manager.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/production_live_pilot_policy.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/`
- `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md`
- if present: `.trellis/tasks/feature-round3-real-data-staged-pilot-v2/execute-evidence/`
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/mutation_proof.py`
- `backend/app/db/validation_gate.py`
- `backend/app/storage/`, `backend/app/datasources/`, `backend/app/validators/` if present
- `tests/test_ops_db_inspector.py`, `tests/test_staged_pilot.py`, `tests/test_data_quality_validator.py`, `tests/test_source_conflict_validator.py`, `tests/test_db_validation_gate.py`, `tests/test_raw_store.py`

Do not stop at this index. Follow data quality rules, staged pilot manifests, existing validator code, ops patterns, tests, and scripts before implementing.

## 6. Functional scope

Must implement:

- data health result/report model
- read-only manifest/evidence loader
- daily bar checks
- cninfo metadata checks
- source lineage checks
- staleness/window checks
- JSON + text/markdown report builder
- read-only CLI/service entrypoint
- integration check against staged pilot evidence

Must not implement:

- production DB write
- source_health_snapshot clean table write
- source fetch
- migration
- full market scan
- free SQL
- frontend
- auto repair

## 7. Allowed files

Only after plan names them:

- `backend/app/ops/data_health.py` new
- `backend/app/ops/data_health_cli.py` or existing ops wrapper, if needed
- `scripts/qmd_ops.py` or thin wrapper, if existing command style requires
- `tests/test_ops_data_health.py` new
- narrow additions to existing data-quality/source-conflict tests
- task-local Trellis evidence

## 8. Verification

Run at minimum:

```bash
python -m pytest tests/test_ops_data_health.py -q
python -m pytest tests/test_ops_db_inspector.py tests/test_staged_pilot.py -q
python -m pytest tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q
python -m pytest tests/test_db_validation_gate.py tests/test_raw_store.py -q
```

If any referenced test file does not exist, create the minimal missing test file or record why it is not applicable.

## 9. Done criteria

- All `/to-issues` slices have evidence.
- Read-only health report runs on PROMPT_14 or v2 staged pilot evidence.
- Bad fixtures prove checks can fail meaningfully.
- JSON and human-readable summaries are produced.
- No production DB mutation, no source fetch, no migration.
- Report states whether it is sufficient as a sandbox clean-write rehearsal gate.
