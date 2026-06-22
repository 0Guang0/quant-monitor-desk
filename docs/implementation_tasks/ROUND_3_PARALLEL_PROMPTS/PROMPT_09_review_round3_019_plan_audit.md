# PROMPT_09 — review/round3-019-plan-audit

Use this prompt in a fresh review session. The session must create the review branch/worktree first, then review the 019 plan/audit artifacts. This is not an implementation branch.

## 1. Branch / worktree setup

- Branch to create: `review/round3-019-plan-audit`
- Base branch: same base as `feature/round3-019-layer2-sensor`; preferably `master` after `integration/round3` has merged
- Suggested worktree path: `../quant-monitor-desk-wt-review-round3-019-plan-audit`
- Target merge branch: normally none until review report is accepted; if archived, merge through `integration/round3`

Before creating the branch, confirm:

- `R3-B3-STAGED-DOWNSTREAM-GATE` is closed in the chosen base.
- `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md` exists.
- `feature/round3-019-layer2-sensor` plan artifacts are available, or this review will be a pre-implementation checklist review.

## 2. Mission

Review `feature/round3-019-layer2-sensor` planning and audit artifacts for missing constraints, staged-only violations, source misuse, lineage gaps, and test weakness.

## 3. Required read index

Read and summarize:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `docs/modules/layer2_cross_asset_sensor.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

If available, also read the implementation branch's:

- `MASTER.plan.md`
- `AUDIT.plan.md`
- source context index
- changed-file list
- test plan

## 4. Review checklist

Block if any of these are true:

- 019 claims production-live readiness.
- 019 uses `tdx_pytdx` as production source or Primary.
- 019 uses live FRED or external vendor writes by default.
- 019 silently falls back from Eastmoney hist to TDX/Sina/QMT/xqshare.
- 019 lacks `double_count_guard` semantics.
- 019 lacks no-future-data tests.
- 019 bypasses WriteManager or ResourceGuard.
- 019 modifies Layer3/4/5 runtime beyond an agreed interface boundary.
- 019 and 023A both write `snapshot_lineage_contract.yaml` without ownership resolution.

## 5. Allowed files

- review report under task-local review path
- `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md` only if improving this task card
- no implementation code

## 6. Forbidden files / behavior

- No backend code changes.
- No contract changes except this review task card.
- No DB writes.
- No source/network fetch.
- No registry edits.
- No direct merge of 019 branch.

## 7. Verification commands

Use only targeted read-supporting tests if available:

- `pytest tests/test_batch3_staged_downstream_gate.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_trellis_audit_trace_authority.py -q`

## 8. Done criteria

- Review report returns PASS / BLOCK / WARN.
- Findings are actionable and reference exact files/sections.
- Report states whether 019 may proceed, must fix blockers, or needs user decision.
- Report explicitly covers staged-only semantics, data-source boundaries, double-counting, lineage, tests, and core-file ownership.
