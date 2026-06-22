# PROMPT_01 — feature/round3-batch3-staged-gate

Use this prompt in a fresh session dedicated to closing `R3-B3-STAGED-DOWNSTREAM-GATE` before any `019` implementation.

## Mission

Freeze Batch 3 staged-only semantics so Round 3 can proceed to `019` without claiming production-live readiness. This branch is docs/tests/gate only unless a validated plan explicitly proves a narrow test-only change is needed.

## Branch / worktree

- Branch: `feature/round3-batch3-staged-gate`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-r3-batch3-staged-gate`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.trellis/workflow.md`
4. `.trellis/spec/guides/complex-task-planning-protocol.md`
5. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
6. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
7. `docs/ROUND3_HANDOFF.md`
8. `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
9. `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`
10. `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
11. `docs/AUDIT_DEFERRED_REGISTRY.md`
12. `docs/UNRESOLVED_ISSUES_REGISTRY.md`
13. `docs/quality/production_live_pilot_policy.md`
14. `docs/quality/staged_acceptance_policy.md`
15. `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`

## Required decision record

The plan must explicitly state:

- Batch 2.75 closeout is `PILOT_FAIL_SOURCE`.
- Request 2 Eastmoney hist remains deferred as `R3-B2.75-REQ2-EM`.
- Batch 3 / `019` may proceed only as staged-only downstream work.
- No evidence in this branch creates production-live readiness.
- 018C may run in parallel but does not unblock production-live claims.

## Allowed files

Prefer docs and tests only:

- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md` only if stale wording is discovered
- targeted tests that assert staged-only semantics, if existing test coverage is insufficient

## Forbidden files / behavior

- No backend runtime implementation.
- No production DB mutation.
- No live FRED fetch.
- No source registry default enablement.
- No `019` Layer2 implementation.
- No 018C source probe implementation.
- No Batch 2.75 closeout rewrite.

## Workflow

1. Create a Trellis task or Phase 8D lightweight plan for the gate.
2. Produce a Source Context Index in MASTER / plan notes.
3. Check whether the task card and gate document already close the gate.
4. If incomplete, make minimal docs/tests edits only.
5. Run targeted tests and doc link checks if available.
6. Produce merge-gate evidence.

## Verification commands

Run what is available in this worktree:

- `pytest tests/test_batch25_production_data_gate.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `python scripts/check_doc_links.py`

If a command is blocked by tooling, record `COMMAND_BLOCKED_BY_TOOLING` with the exact command.

## Done criteria

- `R3-B3-STAGED-DOWNSTREAM-GATE` is explicitly closed or its remaining gap is documented.
- `019` has a clear staged-only start condition.
- All production-live language is fail-closed.
- Merge report lists changed files, tests, no-production/no-runtime assertions, and remaining deferred items.
