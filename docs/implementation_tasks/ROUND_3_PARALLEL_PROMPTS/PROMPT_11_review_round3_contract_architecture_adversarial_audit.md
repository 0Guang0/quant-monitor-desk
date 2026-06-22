# PROMPT_11 — review/round3-contract-architecture-adversarial-audit

Use this prompt in a fresh review session. The session must create the review branch/worktree first, then execute the read-only adversarial audit task.

## 1. Branch / worktree setup

- Branch to create: `review/round3-contract-architecture-adversarial-audit`
- Base branch: latest user-confirmed `master` or `integration/round3`
- Suggested worktree path: `../quant-monitor-desk-wt-review-r3-contract-architecture-audit`
- Target merge branch: normally none until report is accepted; if archived, merge through `integration/round3`

Before creating the branch, confirm:

- Working tree is clean, or existing dirty files are explicitly approved by user/coordinator.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_contract_architecture_adversarial_audit.md` exists.
- Latest Round 3 prompt/task package is visible in the selected base.
- Current completed batch artifacts from PROMPT_07–10 are visible, or their absence is recorded.

## 2. Mission

Perform a read-only adversarial audit of the latest project state against design docs, contracts, architecture, rules, definitions, and business-function specifications.

This is not a normal code review. Trace from docs/specs to implementation and tests. Identify implementation deviation, runtime gaps, vulnerability, architectural drift, data/source/db risks, and completion-quality problems.

## 3. Required task card

Read and follow:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_contract_architecture_adversarial_audit.md`

## 4. Required read index

At minimum read and summarize the files listed in the task card, including:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/INDEX.md`
- `docs/START_HERE.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/architecture/`
- `docs/modules/`
- `docs/quality/`
- `docs/ops/`
- `docs/schema/`
- `specs/contracts/`
- `specs/datasource_registry/`
- `backend/app/`
- `tests/`

Do not stop at this list. Use `ROUND3_BATCH_IMPLEMENTATION_MAP.md`, task-card references, contract `authority` fields, imports, call paths, tests, and failing assertions to discover additional files that must be read before judging a module.

## 5. Current completed batch artifacts to include

User confirmed the current four branches have completed. Read their outputs if present; if not visible, record `MISSING_CURRENT_BATCH_EVIDENCE` and do not assume success.

Must inspect, when available:

- `feature/round3-019-layer2-sensor`: plans, changed files, tests, snapshot lineage evidence, no-future-data evidence, double_count_guard evidence, merge report.
- `feature/round3-023a-evidence-foundation`: plans, changed files, tests, evidence identity, source fetch IDs / content hashes, manual-review evidence, Agent-text-not-fact-source evidence, merge report.
- `review/round3-019-plan-audit`: PASS / WARN / BLOCK report and whether findings were resolved.
- `debt/r3b275-018c-live-manual-probe-plan`: planning-only outputs, authorization checklist, no-live-fetch proof, disabled validation-only status preservation.
- `integration/round3` coordinator artifacts, if present: merge report, conflict notes, post-merge gates, current-batch audit reports.

## 6. Allowed files

- task-local Trellis plan/audit/evidence files
- final review report under an approved review/evidence path
- no implementation code
- no production DB files

## 7. Forbidden behavior

- No implementation code changes.
- No contract/spec edits to make findings disappear.
- No production DB writes.
- No migration execution.
- No external source fetch.
- No enabling QMT, xqshare, TDX live, or production-live source access.
- No full market or full history scan.
- No direct merge of feature branches.
- No treating unverified audit claims as facts.

## 8. Verification commands

Use only targeted read-supporting tests when safe:

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_db_validation_gate.py -q
pytest tests/test_write_manager.py -q
pytest tests/test_sync_orchestrator.py -q
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_module_boundaries.py -q
pytest tests/test_round3_audit_registry_alignment.py -q
pytest tests/test_unresolved_item_task_coverage.py -q
```

If a command is unsafe, unavailable, writes unwanted artifacts, or depends on missing current-batch evidence, record the exact reason.

## 9. Done criteria

- Review report returns PASS / WARN / BLOCK.
- Findings include severity, expected behavior, actual behavior, impact, and exact file references.
- Report explicitly states which issues block real-data staged pilot and which block production-live readiness.
- Current PROMPT_07–10 completion/evidence is included or explicitly marked missing.
- Findings are de-duplicated against unresolved/deferred registries.
