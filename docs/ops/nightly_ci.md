# 夜间 CI — 网络验收（R3-DCP-09 / ADR-011）

PR CI（`.github/workflows/ci.yml`）**不** 传 `--run-network`。夜间流水线负责 live 网络回归。

## 工作流

- 文件：`.github/workflows/nightly.yml`
- 触发：每日 cron `06:00 UTC` + `workflow_dispatch`（手动）

## 步骤

```bash
# 1) Batch 2.75 live pilot 子集（ACC-LIVE-NETWORK-CI-001 / LIVE-NETWORK-GATE-001）
uv run pytest -q --run-network -m network \
  tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive

# 2) 带 findings 门禁的 live 生产验收（ACC-LIVE-ACCEPT-NIGHTLY-001）
uv run python scripts/wave3_live_production_acceptance.py \
  --fail-on-severity HIGH,CRITICAL
```

## 隔离快速配置（PR / 本地）

```bash
uv run python scripts/wave3_isolated_production_acceptance.py --quick
```

`--quick` 跳过 `pytest_full`（约 200s）；闭环 `WAVE3-ACC-OPT-01`。

## 环境变量

| 变量                   | 夜间取值                   |
| ---------------------- | -------------------------- |
| `QMD_DATA_ROOT`        | `.audit-sandbox/nightly-*` |
| `QMD_ALLOW_LIVE_FETCH` | `1`                        |
| `FRED_API_KEY`         | GitHub secret（如需）      |

### Akshare / eastmoney（`ACC-LIVE-NETWORK-CI-001`）

Batch 2.75 Phase 3 第 2 路 `akshare` `fetch_daily_bar_validation` 须能直连 eastmoney/sina。

| 要求     | 说明                                                                                                                                                             |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 系统代理 | Windows Clash/V2Ray 须将 `eastmoney.com` / `push2.eastmoney.com` 设为 **DIRECT**；否则 `NETWORK_ERROR`                                                           |
| 代码侧   | `cn_rehearsal_live_ports._bypass_system_proxy` 已清 env proxy + `urllib.request.getproxies`                                                                      |
| 关账命令 | `QMD_ALLOW_LIVE_FETCH=1 uv run pytest -q --run-network -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive` exit 0 |

本地审计若 akshare 仍 `NETWORK_ERROR`，以 **nightly workflow** 绿为运维关账证据（见 `待修复清单.md` §4 `ACC-LIVE-NETWORK-AKSHARE-ENV`）。

证据产物落在 `.audit-sandbox/wave3-*-acceptance-*/`。
