# Nightly CI — network acceptance (R3-DCP-09 / ADR-030)

PR CI (`.github/workflows/ci.yml`) **does not** pass `--run-network`. Nightly owns live-network regression.

## Workflow

- File: `.github/workflows/nightly.yml`
- Triggers: daily cron `06:00 UTC` + `workflow_dispatch` (manual)

## Steps

```bash
# 1) Batch 2.75 live pilot subset (ACC-LIVE-NETWORK-CI-001 / LIVE-NETWORK-GATE-001)
uv run pytest -q --run-network -m network \
  tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive

# 2) Live production acceptance with findings gate (ACC-LIVE-ACCEPT-NIGHTLY-001)
uv run python scripts/wave3_live_production_acceptance.py \
  --fail-on-severity HIGH,CRITICAL
```

## Isolated quick profile (PR / local)

```bash
uv run python scripts/wave3_isolated_production_acceptance.py --quick
```

`--quick` skips `pytest_full` (~200s); closes `WAVE3-ACC-OPT-01`.

## Environment

| Variable               | Nightly value               |
| ---------------------- | --------------------------- |
| `QMD_DATA_ROOT`        | `.audit-sandbox/nightly-*`  |
| `QMD_ALLOW_LIVE_FETCH` | `1`                         |
| `FRED_API_KEY`         | GitHub secret (if required) |

### Akshare / eastmoney（`ACC-LIVE-NETWORK-CI-001`）

Batch 2.75 Phase 3 第 2 路 `akshare` `fetch_daily_bar_validation` 须能直连 eastmoney/sina。

| 要求     | 说明                                                                                                                                                             |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 系统代理 | Windows Clash/V2Ray 须将 `eastmoney.com` / `push2.eastmoney.com` 设为 **DIRECT**；否则 `NETWORK_ERROR`                                                           |
| 代码侧   | `cn_rehearsal_live_ports._bypass_system_proxy` 已清 env proxy + `urllib.request.getproxies`                                                                      |
| 关账命令 | `QMD_ALLOW_LIVE_FETCH=1 uv run pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` exit 0 |

本地审计若 akshare 仍 `NETWORK_ERROR`，以 **nightly workflow** 绿为运维关账证据（见 `待修复清单.md` §4 `ACC-LIVE-NETWORK-AKSHARE-ENV`）。

Evidence artifacts land under `.audit-sandbox/wave3-*-acceptance-*/`.
