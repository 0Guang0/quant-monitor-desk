# Adversarial Audit Remediation — PROMPT_10 slice

Audit agent: [code-reviewer](7b1b61a3-e942-42d6-8cb4-6965226d0f0b) · 22 findings · remediated 2026-06-22

| ID | Sev | Verdict | Remediation |
| -- | --- | ------- | ----------- |
| F-01 | CRITICAL | **Fixed** | `TdxPytdxProbeFetchPort` fail-closed without `authorization_verified`; plan forbids `run_interface_probe` for live |
| F-02 | CRITICAL | **Fixed** | `tdx_live_manual_probe_gate.py`; plan forbids `live_pilot.validate_authorization` reuse |
| F-03 | HIGH | **Fixed** | `live_manual_probe_plan.md` §8.3 ephemeral enable contract |
| F-04 | HIGH | **Fixed** | Execute prerequisite + partial-scope path in §4 / §11.4 |
| F-05 | HIGH | **Fixed** | `parse_index_instrument()` + plan symbol resolution for `000001.SH` |
| F-06 | HIGH | **Fixed** | §8.2 Phase 2 vs Phase 3对照表 |
| F-07 | HIGH | **Fixed** | `tests/test_tdx_live_manual_probe_authorization.py` |
| F-08 | HIGH | **Fixed** | `execute-evidence/verification_2026-06-22.txt` |
| F-09 | HIGH | **Fixed** | `DEBT.plan.md` owner / coordinator / evidence_path |
| F-10 | MEDIUM | **Fixed** | Authorization phrase cites plan + checklist |
| F-11 | MEDIUM | **Fixed** | Host/port table columns unified (7 columns) |
| F-12 | MEDIUM | **Fixed** | Unified `probe-tdx-*` probe_id namespace |
| F-13 | MEDIUM | **Fixed** | §6 evidence chain (ResourceGuard, file_registry, fetch_log) |
| F-14 | MEDIUM | **Fixed** | §11.1 `tdx_pytdx_live_probe` state machine |
| F-15 | MEDIUM | **Fixed** | `authorized_session_id` in auth file + gate |
| F-16 | MEDIUM | **Fixed** | Forbidden entrypoints in plan §3 + `interface_probe.py` docstring |
| F-17 | MEDIUM | **Fixed** | `upstream: tdx_hq_host:host:port` in port + plan §6 |
| F-18 | MEDIUM | **Fixed** | 018C evidence appendix in `DEBT.plan.md` |
| F-19 | LOW | **Fixed** | R3D §8 rollback pointer |
| F-20 | LOW | **Fixed** | §7 DB must exist / `db_absent` |
| F-21 | LOW | **Fixed** | §8.1 BLOCK condition simplified |
| F-22 | LOW | **Fixed** | Committed on `debt/r3b275-018c-live-manual-probe-plan` |

## Residual execute risk (documented, not planning blockers)

- `run_tdx_live_manual_probe()` not implemented yet
- `with_ephemeral_capability_enable()` not implemented yet
- `get_security_list` / `get_index_bars` fetch ports not implemented yet
