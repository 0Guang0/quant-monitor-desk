# PROMPT_00 — integration/round3 Merge Coordinator

Use this prompt in one coordinator session only. This is not an implementation branch prompt.

## Mission

Create or maintain the Round 3 integration branch and act as merge coordinator for staged-only mainline and Phase 8D parallel branches. Do not implement feature logic in this session.

## Branch / worktree

- Target branch: `integration/round3`
- Base: `master` at or after commit `700135ca` (`chore: add round3 repair debt worktree protocol`)
- Suggested worktree path: `../quant-monitor-desk-wt-integration-round3`
- Do not create implementation branches from a dirty working tree.

## Required reads before action

Read these in order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.trellis/workflow.md`
4. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
5. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
6. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
7. `docs/ROUND3_HANDOFF.md`
8. `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
9. `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/*.md`

## Allowed scope

- Create or switch to `integration/round3`.
- Maintain an integration checklist in task/evidence docs if a Trellis task is created.
- Review branch self-reports and merge-gate evidence.
- Reconcile registry rows only when a merged branch explicitly owns a registry slice or a merge gate requires coordinator reconciliation.

## Forbidden scope

- No backend runtime implementation.
- No production DB mutation.
- No live-source fetch.
- No source default enablement.
- No registry row edits from multiple active branches at once.
- No merging a branch without its merge-gate evidence.

## Workflow

1. Confirm `master` contains commit `700135ca` or a descendant.
2. Confirm the current working tree is clean except known pre-existing evidence side effects if documented by the user.
3. Create or checkout `integration/round3`.
4. For each incoming branch, require:
   - changed files and intended scope
   - out-of-scope untouched files
   - targeted tests
   - broad verification or tool limitation note
   - production DB no-mutation proof if any data path touched
   - staged-only / production-live claim check
   - registry reconciliation summary
5. Merge in this order unless a later MASTER plan overrides it:
   - tests/CI-only branches
   - docs/evidence-only branches
   - registry-only branches
   - `feature/round3-batch3-staged-gate`
   - mainline runtime branches: `019 -> 020 -> 023A -> 021 -> 022 -> 023B`
   - source/data/probe branches after isolated review

## Expected output to user

Report:

- current integration branch state
- active branch matrix
- branches safe to start now
- branches blocked on staged gate
- merge-gate checklist status
- any dirty files that must not be mixed into branch work
