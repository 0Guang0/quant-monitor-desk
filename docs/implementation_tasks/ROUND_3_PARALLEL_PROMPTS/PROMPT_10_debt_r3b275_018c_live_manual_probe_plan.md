# PROMPT_10 — debt/r3b275-018c-live-manual-probe-plan

Use this prompt in a fresh session. The session must create the branch/worktree first, then produce a planning-only live/manual probe plan. Do not run live network calls in this branch.

## 1. Branch / worktree setup

- Branch to create: `debt/r3b275-018c-live-manual-probe-plan`
- Base branch: `master` after `integration/round3` has merged, or `integration/round3` if explicitly instructed before merge-back
- Suggested worktree path: `../quant-monitor-desk-wt-r3b275-018c-live-manual-probe-plan`
- Target merge branch: `integration/round3`

Before creating the branch, confirm:

- 018C disabled candidate result is visible in the base.
- `tdx_pytdx` remains disabled-by-default and validation-only.
- This session has no user authorization to perform live TDX network fetch unless explicitly provided in the same session.

## 2. Mission

Prepare a future user-authorized manual live probe plan for `tdx_pytdx`. This branch does not execute the probe.

The output should make a future live probe safe and unambiguous by defining authorization, host/port source, symbols, row caps, sandbox path, ResourceGuard caps, no-mutation proof, and close/re-defer criteria.

## 3. Required Plan-stage input index

Read and summarize:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `backend/app/datasources/adapters/tdx_pytdx.py` if present
- `backend/app/ops/interface_probe.py` if present
- `tests/test_interface_probe_018c.py` if present

## 4. External references to cite in the plan

- `https://github.com/henrylin99/tdx_quant`
- `https://github.com/afute/TdxQuantNet`
- `https://github.com/hlh2518/tdx-quant`

Do not vendor or copy code. Use these only to frame future probe assumptions and source-inspection follow-up.

## 5. Allowed files

Planning-only:

- task-local `DEBT.plan.md`
- task-local `live_manual_probe_plan.md`
- task-local `authorization_checklist.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md` if correcting gaps
- optional test that asserts live probe requires explicit authorization, only if narrow and no network

## 6. Forbidden files / behavior

- No live network fetch.
- No TDX host connection.
- No production DB mutation.
- No clean table write.
- No default enablement of `tdx_pytdx`.
- No Primary role for `tdx_pytdx`.
- No automatic fallback from Eastmoney hist to Sina/TDX/QMT/xqshare.
- No QMT/xqshare login, trading, captcha, GUI, or auto-login behavior.
- No claim that Eastmoney Request 2 is closed.

## 7. Required plan contents

The plan must define:

- exact user authorization phrase required before live probe
- who provides host/port and how it is recorded
- allowed operations: `fetch_security_list`, `fetch_daily_bar`, `fetch_index_daily_bar`
- allowed symbols/markets and max rows
- sandbox output path
- no-mutation proof method
- route preview expected states
- ResourceGuard caps
- failure taxonomy
- close/re-defer criteria
- rollback/cleanup instructions

## 8. Verification commands

- `pytest tests/test_interface_probe_018c.py -q` if present and no network
- `pytest tests/test_source_capabilities.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `python scripts/check_doc_links.py` if docs changed

## 9. Done criteria

- Future live probe can be executed later without guessing authorization or safety boundary.
- This branch itself ran no live fetch.
- `tdx_pytdx` remains disabled-by-default and validation-only.
- Merge report says production-live readiness remains blocked until separately authorized live probe succeeds and passes no-mutation proof.
