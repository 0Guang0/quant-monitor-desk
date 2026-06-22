# PROMPT_02 — debt/r3b275-018c-low-cost-probe

Use this prompt in a fresh session dedicated to the 018C low-cost source probe. This branch may run in parallel with staged-only Batch 3 gate work, but it must not change production readiness claims.

## Mission

Evaluate low-cost source candidates for the Batch 2.75 Request 2 failure without weakening QMD data-source governance. Treat all external repositories as references only.

## Branch / worktree

- Branch: `debt/r3b275-018c-low-cost-probe`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-r3b275-018c-probe`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.trellis/workflow.md`
4. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
5. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
6. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
7. `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
8. `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`
9. `docs/AUDIT_DEFERRED_REGISTRY.md`
10. `docs/UNRESOLVED_ISSUES_REGISTRY.md`
11. `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`
12. `docs/quality/production_live_pilot_policy.md`
13. `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
14. `specs/datasource_registry/source_registry.yaml`
15. `specs/datasource_registry/source_capabilities.yaml`
16. `specs/contracts/source_route_contract.yaml`
17. `specs/contracts/datasource_service_contract.yaml`
18. `specs/contracts/data_quality_rules.yaml`
19. `specs/contracts/source_conflict_rules.yaml`
20. `specs/contracts/resource_limits.yaml`

## External references to open and cite in the plan

- `https://github.com/henrylin99/tdx_quant`
- `https://github.com/quant-king299/EasyXT`
- `https://github.com/quant-king299/JQ2PTrade`
- `https://github.com/quant-king299/ptqmt-site`
- `https://github.com/bebopze/tdx-quant`
- `https://github.com/afute/TdxQuantNet`
- `https://github.com/hlh2518/tdx-quant`

Only `henrylin99/tdx_quant` is currently primary Python/pytdx implementation reference. `afute/TdxQuantNet` and `hlh2518/tdx-quant` are follow-up only until source/license/tests/API behavior are inspected.

## Allowed files

Only if explicitly planned:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`
- task-local evidence under the Trellis task
- `.audit-sandbox/` or task-local sandbox evidence
- narrow `specs/datasource_registry/source_registry.yaml`
- narrow `specs/datasource_registry/source_capabilities.yaml`
- narrow `backend/app/datasources/adapters/` disabled candidate code
- narrow `backend/app/ops/` bounded sidecar probe runner
- tests for disabled-by-default, route fail-closed, no-primary-promotion, raw-only evidence, and no-mutation proof

## Forbidden files / behavior

- No production DB mutation.
- No clean production write.
- No default enablement of `tdx_pytdx`.
- No Primary role for `tdx_pytdx`.
- No automatic fallback from Eastmoney hist to Sina/TDX/QMT/xqshare.
- No QMT/xqshare live connection unless separately user-authorized in a future task.
- No trading/order API, auto-login, captcha, GUI, broad source-health release, or DB-GPT runtime integration.
- No Batch 2.75 closeout rewrite.
- No `019` implementation.

## Workflow

1. Create a Phase 8D lightweight plan or Trellis task before implementation.
2. Record source-of-truth IDs: `R3-B2.75-REQ2-EM`, `R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE`, `PILOT_FAIL_SOURCE`.
3. Decide whether this session is docs/plan-only, registry draft, adapter/probe implementation, or evidence-only.
4. If implementing, start RED tests for disabled-by-default and fail-closed behavior.
5. Keep probe caps narrow: `security_list`, `cn_equity_daily_bar`, `cn_index_daily_bar`; max small sample window only.
6. Store raw evidence only; prove no production DB mutation.
7. Close with `PROBE_ACCEPT_DISABLED_CANDIDATE`, `PROBE_REJECT_SOURCE`, or `PROBE_REDEFERRED`.

## Verification commands

Run relevant commands only for changed scope:

- `pytest tests/test_datasource_service.py -q`
- `pytest tests/test_source_route_planner.py -q`
- `pytest tests/test_source_capabilities.py -q`
- `pytest tests/test_source_conflict_validator.py tests/test_data_quality_validator.py -q`
- `pytest tests/test_batch25_production_data_gate.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `python scripts/check_doc_links.py`

If a command does not exist or is blocked, record it exactly.

## Done criteria

- External URLs are cited in MASTER Source Context Index.
- Candidate remains disabled-by-default and validation-only.
- All endpoint labels distinguish `stock_zh_a_hist` / Eastmoney hist from `stock_zh_a_daily` / Sina and `tdx_pytdx`.
- Evidence includes source, operation, endpoint/vendor label, params, content hash, timestamp, sandbox path, and failure reason.
- Production DB no-mutation proof is attached.
- Merge report states this branch does not unblock production-live readiness.
