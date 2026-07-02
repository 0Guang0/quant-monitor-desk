# PROMPT_03 — debt/r3b275-perf-hyg-registry

Use this prompt in a fresh session for Batch 2.75 perf/hyg registry debt.

## Mission

Close or precisely re-defer `R3-B25-PERF-BUDGET-01` and `R3-B25-HYG-03`. Keep the branch limited to documentation, evidence, and registry-alignment tests.

## Branch / worktree

- Branch: `debt/r3b275-perf-hyg-registry`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-r3b275-perf-hyg`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
4. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
5. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
6. `docs/AUDIT_DEFERRED_REGISTRY.md`
7. `docs/UNRESOLVED_ISSUES_REGISTRY.md`
8. `docs/RESOLVED_ISSUES_REGISTRY.md`
9. `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`
10. `docs/quality/production_live_pilot_policy.md`
11. `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`

## Source IDs

- `R3-B25-PERF-BUDGET-01`
- `R3-B25-HYG-03`

## Allowed files

- registry docs
- pending-fix registry docs
- task-local evidence files
- registry alignment tests
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md` only if an index is stale

## Hard boundaries

- Do not edit backend runtime files.
- Do not change source defaults.
- Do not write the project database.
- Do not claim new production readiness.

## Workflow

1. Create a Phase 8D lightweight plan.
2. Decide for each source ID: close with evidence, re-defer with owner/phase/closure command, or leave untouched with reason.
3. Keep registry edits line-specific.
4. Run registry and policy tests.
5. Produce a merge report with exact rows changed.

## Verification commands

- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_trellis_audit_trace_authority.py -q`
- `pytest tests/test_batch25_production_data_gate.py -q`
- `python scripts/check_doc_links.py`

## Done criteria

- Every changed registry row has owner, phase, closure command, and evidence pointer.
- No runtime or source behavior changed.
- Merge report lists changed files, source IDs, tests, and remaining deferred items.
