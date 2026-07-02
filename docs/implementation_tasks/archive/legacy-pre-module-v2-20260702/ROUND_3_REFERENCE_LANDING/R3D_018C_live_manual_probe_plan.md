# R3D_018C_live_manual_probe_plan — Future TDX Live Manual Probe Planning

## 1. Round / batch / branch

| Field                | Value                                                                                                    |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| Round                | Round 3                                                                                                  |
| Batch                | Batch 2.75 follow-up / Phase 8D planning-only debt slice                                                 |
| Branch               | `debt/r3b275-018c-live-manual-probe-plan`                                                                |
| Can run in parallel? | Yes, as planning-only work after 018C disabled candidate acceptance.                                     |
| Must not do          | No live network fetch, no production DB write, no source default enablement, no runtime production path. |

## 2. Mission

Prepare a future user-authorized manual live probe plan for `tdx_pytdx` without executing live network access in this branch.

This task exists because 018C accepted `tdx_pytdx` only as a disabled validation candidate. It did not prove live production readiness and did not close Eastmoney hist Request 2.

## 3. Source of truth

Required prior evidence:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`
- `.trellis/tasks/06-22-round3-018c-low-cost-probe/execute-evidence/interface_probe_decision.md` if merged from `integration/round3`
- `.trellis/tasks/06-22-round3-018c-low-cost-probe/execute-evidence/interface_probe_no_mutation_proof.md` if merged from `integration/round3`

Expected prior decision:

- `tdx_pytdx`: `PROBE_ACCEPT_DISABLED_CANDIDATE`
- `akshare_sina_sidecar`: `PROBE_REDEFERRED`
- `tdx_pytdx_live_probe`: `PROBE_REDEFERRED`
- `Unblocks production-live readiness`: False

## 4. Required Plan-stage input index

Plan must read and summarize:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
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
- `backend/app/datasources/adapters/tdx_pytdx.py` if available after integration merge
- `backend/app/ops/interface_probe.py` if available after integration merge
- `tests/test_interface_probe_018c.py` if available after integration merge

## 5. External references

The plan may cite but must not vendor code from:

- `https://github.com/henrylin99/tdx_quant`
- `https://github.com/afute/TdxQuantNet`
- `https://github.com/hlh2518/tdx-quant`

`henrylin99/tdx_quant` remains the primary Python/pytdx reference. `afute/TdxQuantNet` and `hlh2518/tdx-quant` remain follow-up only until source/license/tests/API behavior are inspected.

## 6. Allowed files

Planning-only by default:

- task-local `DEBT.plan.md`
- task-local `live_manual_probe_plan.md`
- task-local authorization checklist
- docs update to this task card if gaps are found
- optional tests that assert live probe requires explicit authorization, if already in scope

## 7. Forbidden files / behavior

- No live network fetch.
- No TDX host connection.
- No production DB mutation.
- No clean table write.
- No default enablement of `tdx_pytdx`.
- No Primary role for `tdx_pytdx`.
- No automatic fallback from Eastmoney hist to Sina/TDX/QMT/xqshare.
- No QMT/xqshare login, auto-login, trading, order, captcha, or GUI behavior.
- No claim that Request 2 is closed.

## 8. Required plan contents

The plan must define:

- exact user authorization required before any live probe
- allowed TDX host/port source and who provides it
- allowed symbols, market codes, and max rows
- allowed operations only: `fetch_security_list`, `fetch_daily_bar`, `fetch_index_daily_bar`
- sandbox output path
- no-mutation proof method
- route preview expected states
- ResourceGuard caps
- failure taxonomy
- close/re-defer criteria
- rollback/cleanup instructions (see `live_manual_probe_plan.md` §12)

## 9. Done criteria

- A future live manual probe can be executed by a later session without guessing authorization, scope, or safety boundary.
- The branch does not run any live fetch itself.
- The branch preserves disabled-by-default / validation-only status.
- Merge report states that production-live readiness remains blocked until a separately authorized live probe succeeds and passes no-mutation proof.

## 10. Task-local planning artifacts (debt/r3b275-018c-live-manual-probe-plan)

| Artifact | Path |
| -------- | ---- |
| Repair/Debt Lite plan | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/DEBT.plan.md` |
| Live manual probe plan | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md` |
| Authorization checklist | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/authorization_checklist.md` |
| Fail-closed gate | `backend/app/ops/tdx_live_manual_probe_gate.py` |
| Auth tests (no network) | `tests/test_tdx_live_manual_probe_authorization.py` |
| Verification log | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/execute-evidence/verification_2026-06-22.txt` |

Future execute authorization evidence file (not created by planning branch): `docs/quality/tdx_pytdx_live_manual_probe_authorization_<YYYY-MM-DD>.md`
