# PROMPT_15 — fix/round3-r3x-residual-open-items-closure

Use this prompt in a **fresh implementation session**. Create branch/worktree first, then execute **exhaustive** residual open-item closure.

## 1. Branch / worktree setup

- Branch: `fix/round3-r3x-residual-open-items-closure`
- Base: latest `master` @ `ae542970` (or coordinator-confirmed HEAD)
- Worktree: `../quant-monitor-desk-wt-fix-r3-r3x-residual-closure`
- Target merge: `master`

Confirm before branch creation:

- Working tree clean on base.
- PROMPT_11–13 merged to `master`.
- Task card exists: `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_residual_open_items_closure.md`

## 2. Mission

**Zero intentional deferrals inside the fixable set.** Fix every item in the task card Master Checklist that is fixable at the current staged-only stage—**blocking or not**.

Read PROMPT_11 archived merge gate:

`.trellis/tasks/archive/2026-06/06-22-round3-contract-architecture-adversarial-audit/execute-evidence/merge_gate_report.md`

Cross-check `docs/quality/adversarial_audit_report.md`, PROMPT_12/13 merge_gate deferred sections, and `019_plan_audit_report.md` F-019-R01..R03.

## 3. Required task card

`docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_residual_open_items_closure.md`

## 4. Required reads

- `AGENTS.md`, `CLAUDE.md`, `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `/karpathy-guidelines`, `/testing-guidelines`, `/tdd` before each code slice
- **`/ponytail` (full mode, mandatory)** — shortest working diff; stdlib/native first; no unrequested abstractions; deletion over addition; one runnable check per non-trivial fix group

## 5. Ponytail (mandatory, full intensity)

Apply the ponytail ladder on **every** checklist item before writing code:

1. Does this need to exist at all? (YAGNI — no speculative helpers)
2. Stdlib / existing project utility?
3. Native platform / contract / DB constraint?
4. Already-installed dependency?
5. One line?
6. Only then: minimum code that works.

Rules for this slice:

- No interface-with-one-impl, no factory-for-one-product, no config for never-changing values.
- Fewest files; shortest diff wins. Refactor **down** any over-built code already written in this branch.
- Deliberate simplifications: `// ponytail: …` or `# ponytail: …` with ceiling + upgrade path when relevant.
- One small `test_*.py` assertion per non-trivial fix group — no fixture forests, no per-function suites unless required by `/testing-guidelines`.
- Never ponytail away: validation at trust boundaries, data-loss prevention, security, accessibility, or anything explicitly in the Master Checklist.

## 6. Execution rules

1. **TDD only** — RED evidence file per checklist group, then GREEN.
2. **`merge_gate_report.md`** — every Master Checklist row: `FIXED` | `ALREADY_CLOSED` | `OUT_OF_SCOPE` + reason.
3. **GitNexus `impact()`** before editing symbols; **`detect_changes()`** before handoff.
4. **Registry:** coordinator-owned — update `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED` only for items in §4.7; mark RESOLVED with evidence paths.
5. Add `tests/test_r3x_residual_open_items_closure.py` as regression umbrella for ADV-R3X IDs.

## 7. Hard exclusions (document OUT_OF_SCOPE, do not fake-fix)

- Do **not** close `R3-B2.75-REQ2-EM`
- No live network fetch; no production DB writes
- No default enable for `tdx_pytdx`, QMT, xqshare, Yahoo
- No production-live readiness claims
- No full Layer3/4 snapshot lineage (`ADV-R3X-LINEAGE-001`) — defer to Batch 4/5 in registry only
- PROMPT_14 pilot is a separate branch after this merge

## 8. Deliverables

- Implementation + tests closing all fixable checklist rows
- `.trellis/tasks/fix-round3-r3x-residual-open-items-closure/execute-evidence/merge_gate_report.md`
- RED/GREEN evidence per major group under `execute-evidence/`
- Full `pytest -q` green

## 9. Coordinator merge gate

Incoming branch must provide: changed files, checklist table, targeted pytest, no-mutation proof, staged-only claim, registry summary.
