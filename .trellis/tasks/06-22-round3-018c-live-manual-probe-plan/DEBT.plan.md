# Repair/Debt Lite Plan — r3b275-018c-live-manual-probe-plan

## Source of truth

| Field | Value |
| ----- | ----- |
| Owner | Round 3 debt stream / PROMPT_10 session agent |
| Merge coordinator | `integration/round3` (per `PROMPT_00`) |
| Evidence path | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/execute-evidence/` |
| Audit / registry IDs | `R3-B2.75-REQ2-EM`, `R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE`, `R3-018C-LIVE-MANUAL-PROBE-PLAN` |
| Prior 018C closeout | `PROBE_ACCEPT_DISABLED_CANDIDATE` (`tdx_pytdx`); `tdx_pytdx_live_probe`: `PROBE_REDEFERRED` |
| Base branch | `master` @ `76ea3471` (`integration/round3` not present locally) |
| Working branch | `debt/r3b275-018c-live-manual-probe-plan` |
| Worktree | `../quant-monitor-desk-wt-r3b275-018c-live-manual-probe-plan` |
| Target merge branch | `integration/round3` |
| Phase | 8D Repair/Debt Lite — planning + fail-closed gate scaffold |

## Appendix — 018C evidence snapshot (base @ 76ea3471)

```
interface_probe_decision.md:
  overall: PROBE_ACCEPT_DISABLED_CANDIDATE
  tdx_pytdx: PROBE_ACCEPT_DISABLED_CANDIDATE
  akshare_sina_sidecar: PROBE_REDEFERRED
  tdx_pytdx_live_probe: PROBE_REDEFERRED
  unblocks production-live: False
```

Registry: `tdx_pytdx` `enabled_by_default: false`, `validation_only: true`, `default_role: Validation`.

## Base verification (pre-branch)

- [x] 018C disabled candidate visible (appendix above)
- [x] `tdx_pytdx` disabled-by-default and validation-only
- [x] No user live TDX authorization in planning session

## Decision

Planning artifacts + `tdx_live_manual_probe_gate.py` + authorization tests. **Zero** live HQ connect in this slice.

## Allowed files

- Task-local `DEBT.plan.md`, `live_manual_probe_plan.md`, `authorization_checklist.md`, `execute-evidence/`
- `backend/app/ops/tdx_live_manual_probe_gate.py` (fail-closed gate)
- `backend/app/ops/interface_probe_fetch_ports.py` (block unauthenticated TDX connect)
- `tests/test_tdx_live_manual_probe_authorization.py`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md`

## Forbidden

Live TDX network fetch, production DB mutation, clean write, default enablement, Primary promotion, Request 2 closeout claim, `live_pilot.validate_authorization` reuse for TDX

## Verification

See `execute-evidence/verification_2026-06-22.txt`

## Merge report statement

Production-live readiness **remains blocked** until separately authorized live probe succeeds with no-mutation proof.
