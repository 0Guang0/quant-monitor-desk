# PROMPT_05 — chore/round3-ci-gate-hardening

Use this prompt in a fresh session for Round 3 verification-command and gate hygiene. This branch is allowed to run in parallel if it does not edit runtime behavior.

## Mission

Make Round 3 verification commands, doc-link checks, and staged/live-readiness guard tests easier to run and harder to misinterpret. Do not change business logic.

## Branch / worktree

- Branch: `chore/round3-ci-gate-hardening`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-round3-ci-gate`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
4. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
5. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
6. `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
7. `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
8. `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
9. `docs/quality/production_live_pilot_policy.md`
10. `docs/quality/staged_acceptance_policy.md`
11. `docs/ops/verification_commands.md` if present
12. `pyproject.toml` and existing pytest config only if needed

## Allowed files

- tests that assert protocol/gate semantics
- docs/ops verification command docs
- doc link check configuration if already present
- pytest markers/config only if required by a narrow plan
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md` only if the command index is stale

## Hard boundaries

- Do not edit backend runtime behavior.
- Do not alter data-source routing defaults.
- Do not write project DB files.
- Do not introduce network-dependent tests as default CI.
- Do not make broad formatting-only changes across unrelated files.

## Workflow

1. Create a Phase 8D lightweight plan.
2. Inventory current Round 3 verification commands from docs and tests.
3. Identify missing or stale commands.
4. Add minimal docs/tests/config updates only.
5. Run targeted tests and doc link check.
6. Produce a merge report with command matrix.

## Verification commands

- `pytest tests/test_trellis_audit_trace_authority.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_batch25_production_data_gate.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `python scripts/check_doc_links.py`

## Done criteria

- Round 3 command matrix is current.
- Staged-only and production-live policy tests are easy to find.
- No runtime behavior changed.
- Merge report lists changed files, tests, and any commands intentionally not run.
