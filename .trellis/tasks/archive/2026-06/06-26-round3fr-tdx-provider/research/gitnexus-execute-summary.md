# GitNexus Execute Summary — R3FR-03

> Boot 2026-06-26 · branch `refactor/round3fr-tdx-provider`

## query: TDX probe fetch flow

- `TdxPytdxProbeFetchPort` in `interface_probe_fetch_ports.py` (ops layer)
- Callers: `tdx_manual_probe._resolve_live_port`, tests in `test_tdx_live_manual_probe_authorization.py`
- Related: `validate_tdx_live_manual_probe_authorization`, `run_tdx_manual_probe`

## impact: TdxPytdxProbeFetchPort (upstream)

- **Risk:** LOW
- **d=1:** `test_tdx_live_manual_probe_authorization.py`, `interface_probe.py`
- **d=2:** `test_ops_interface_probe.py`, `test_interface_probe_018c.py`
- Plan: slim delegate to new `TdxPytdxFetchPort`; preserve test imports

## impact: run_tdx_manual_probe

- Symbol not indexed; manual trace: tests/test_tdx_manual_probe.py only production caller

## Edit plan

| Symbol                       | Action                                        |
| ---------------------------- | --------------------------------------------- |
| `fetch_port.PortErrorStatus` | Add DISABLED_SOURCE, USER_AUTH_REQUIRED       |
| NEW `TdxPytdxFetchPort`      | QMD-owned port in fetch_ports/                |
| NEW `normalizers/tdx.py`     | Manifest + hash                               |
| `TdxPytdxProbeFetchPort`     | Delegate to port                              |
| `tdx_manual_probe`           | EQUITY_INDEX_CAP=3, use normalizer imports    |
| `tdx_live_manual_probe_gate` | caps=3, FORBIDDEN_LIVE_ENTRYPOINTS + port FQN |
