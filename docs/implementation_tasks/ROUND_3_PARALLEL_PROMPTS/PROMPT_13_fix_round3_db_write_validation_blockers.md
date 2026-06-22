# PROMPT_13 — fix/round3-db-write-validation-blockers

Use this prompt in a fresh implementation session. The session must create the branch/worktree first, then execute the minimal DB/write/validation blocker repair task.

## 1. Branch / worktree setup

- Branch to create: `fix/round3-db-write-validation-blockers`
- Base branch: latest user-confirmed `master` or `integration/round3`
- Suggested worktree path: `../quant-monitor-desk-wt-fix-r3-db-write-validation-blockers`
- Target merge branch: `integration/round3`

Before creating the branch, confirm:

- Working tree is clean, or existing dirty files are explicitly approved by user/coordinator.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_db_write_validation_blockers.md` exists.
- Current completed batch artifacts from PROMPT_07–10 are visible, or their absence is recorded.

## 2. Mission

Fix the minimal DB, WriteManager, ValidationGate, conflict, and audit blockers that must be safe before a real-data staged pilot can produce meaningful evidence.

This task does not run real source fetch, does not write production clean tables, and does not prove production-live readiness.

## 3. Required task card

Read and follow:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_db_write_validation_blockers.md`

## 4. Required Plan-stage input index

Read and summarize before writing the plan:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/data_sync_orchestrator.md` if present
- `docs/modules/local_file_system.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/runtime_versions.md`
- `docs/schema/`
- schema migration files, if present
- `backend/app/db/`
- `backend/app/storage/`
- `backend/app/sync/`
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/live_pilot.py`
- `tests/test_db_validation_gate.py`
- `tests/test_write_manager.py`
- `tests/test_sync_orchestrator.py`
- `tests/test_sync_jobs.py`
- `tests/test_raw_store.py`
- `tests/test_ops_db_inspector.py`

Do not stop at this list. Trace through project maps, contract authority fields, migrations, import/call paths, tests, and latest audit reports before changing code.

## 5. Current completed batch artifacts to include

User confirmed the current four branches have completed. Include their DB/write/validation implications if present; otherwise record `MISSING_CURRENT_BATCH_EVIDENCE`.

Must inspect, when available:

- `feature/round3-019-layer2-sensor`: snapshot write/staging path, ResourceGuard, WriteManager, no-future-data, lineage fields.
- `feature/round3-023a-evidence-foundation`: evidence identity, source fetch/content hashes, manual-review flags, Agent-text-not-fact-source tests.
- `review/round3-019-plan-audit`: PASS / WARN / BLOCK findings about DB mutation, WriteManager, ResourceGuard, lineage.
- `debt/r3b275-018c-live-manual-probe-plan`: no-mutation proof method, sandbox path, authorization checklist, DB write prohibition.
- integration/coordinator artifacts and current-batch audit reports.

## 6. Allowed files

Only after the plan names them:

- `backend/app/db/validation_gate.py`
- `backend/app/db/write_manager.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/storage/raw_store.py` only if path containment requires it
- `backend/app/sync/`
- `specs/contracts/write_contract.yaml` only if contract ambiguity is proven
- `specs/contracts/data_quality_rules.yaml` only if machine rule metadata is missing
- narrow DB/write/sync/storage tests
- task-local Trellis plan/evidence files

## 7. Forbidden behavior

- No production DB writes.
- No production migration execution.
- No real source fetch.
- No production clean write enablement.
- No deleting or weakening gates to pass tests.
- No bypassing WriteManager.
- No validation-only source clean write.
- No broad unrelated refactor.
- No full data-health CLI implementation in this branch.
- No production-live readiness claim.

## 8. Required safeguards

- Start with RED tests for the exact blocker.
- ValidationGate must cover write contract rejection conditions or explicitly defer with evidence.
- schema/content drift behavior must be safe and auditable.
- staged/file registry writes must validate allowed path containment.
- backfill and incremental paths must obey the same validation/conflict gate class.
- failed audit evidence must remain traceable in rollback/exception scenarios.
- no-mutation proof must remain meaningful.

## 9. Verification commands

Run at minimum:

```bash
pytest tests/test_db_validation_gate.py -q
pytest tests/test_write_manager.py -q
pytest tests/test_sync_orchestrator.py -q
pytest tests/test_sync_jobs.py -q
pytest tests/test_raw_store.py -q
pytest tests/test_ops_db_inspector.py -q
```

If schema/migration contract changed:

```bash
pytest tests/test_schema_contract.py -q
pytest tests/test_schema_migration.py -q
```

If docs/spec links changed:

```bash
python scripts/check_doc_links.py
```

## 10. Done criteria

- DB/write/validation blockers are fixed or explicitly deferred with evidence.
- backfill severe conflict cannot clean write.
- conflict_report_id is traceable from backfill job where applicable.
- staged evidence cannot escape allowed paths.
- failed audit evidence remains traceable.
- Current PROMPT_07–10 completion/evidence is included or explicitly marked missing.
- Merge report lists changed files, tests, DB mutation status, and remaining deferred DB/data-health items.
