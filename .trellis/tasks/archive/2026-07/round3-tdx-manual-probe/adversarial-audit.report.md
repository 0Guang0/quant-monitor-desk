# Adversarial Audit Report — round3-tdx-manual-probe (B01-TDX)

> **Auditor:** B01-TDX 对抗性闭合 Agent · `composer-2.5`  
> **工作区：** `quant-monitor-desk-wt-b01-tdx`  
> **分支：** `debt/round3-tdx-manual-probe`  
> **日期：** 2026-06-25  
> **输入：** `DEBT.plan.md`、`BATCH_01_HARDENING_RULES.md`、`agents/audit-adversarial-authority.md`、Execute 证据

---

## 总判定

| 项                               | 值                                            |
| -------------------------------- | --------------------------------------------- |
| **对抗性审计判定**               | **PASS**                                      |
| **OPEN（BLOCKING）**             | **0**                                         |
| **OPEN（NON-BLOCKING）**         | **0**                                         |
| **PROBE_REDEFERRED（书面闭合）** | BLK-TDX-04/05 live host/port + pytdx optional |
| **COORDINATOR-QUEUED**           | BLK-TDX-06 registry proposed delta            |

---

## TDX-AUD-P01..P08 处置

| ID              | Sev      | 发现                                                              | 处置                                                                                            | 状态       |
| --------------- | -------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------- |
| **TDX-AUD-P01** | BLOCKING | 交付物未 commit（untracked task dir / tests / ops）               | `git add` + commit 全量 allowed 文件                                                            | **CLOSED** |
| **TDX-AUD-P02** | BLOCKING | 缺 RED 证据 `tdx-*-red.txt`                                       | 补齐 `execute-evidence/tdx-01..06-*-red.txt`                                                    | **CLOSED** |
| **TDX-AUD-P03** | BLOCKING | 无 `MAX_TOTAL_ROWS` / `max_network_calls` 单测                    | `test_tdx_caps_maxTotalRows_*` + `test_tdx_caps_maxNetworkCalls_*`                              | **CLOSED** |
| **TDX-AUD-P04** | BLOCKING | equity/index 窗口/行数 cap 无 gate 测试                           | `test_tdx04_equityIndexTargets_respectWindowAndRowCaps`                                         | **CLOSED** |
| **TDX-AUD-P05** | BLOCKING | raw record 缺 `as_of`                                             | `_run_single_probe` 写入 `as_of`；`test_tdx02_mockedEquity_rawRecordHasAsOf`                    | **CLOSED** |
| **TDX-AUD-P06** | BLOCKING | `comparison.missing[]` 与 verdict 分类不一致                      | `startswith("missing_")` / `comparable_`；index/list 缺失分支；`test_tdx05_comparisonMissing_*` | **CLOSED** |
| **TDX-AUD-P07** | BLOCKING | `DEBT.plan` gate 引用不存在的 `test_layer2_cross_asset_sensor.py` | 改为 `test_layer2_sensor_loader.py::test_stagedSource_rejectsTdxPytdx_viaBuilder`               | **CLOSED** |
| **TDX-AUD-P08** | BLOCKING | 缺 production primary 负向或 018C 引用                            | `test_tdx08_routeMatrix_neverSelectsTdxAsPrimary`（`interface_probe.build_route_matrix`）       | **CLOSED** |

---

## 阻塞项书面闭合

| ID             | 处置                                                                                                       | 状态                   |
| -------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------- |
| **BLK-TDX-04** | 授权 MD 占位 host；`test_tdx_blk04_livePath_documentedProbeDeferred` → `TDX_PROBE_REDEFERRED`              | **PROBE_REDEFERRED**   |
| **BLK-TDX-05** | pytdx 未安装时 live → `TDX_PROBE_FAIL_DEPENDENCY`；CI 默认 mocked 绿                                       | **PROBE_REDEFERRED**   |
| **BLK-TDX-06** | `registry_proposed_delta.yaml` + `coordinator_status: COORDINATOR-QUEUED`；本分支不 commit registry 三件套 | **COORDINATOR-QUEUED** |

**不冒充：** live bounded fetch 未 PASS；`tdx_pytdx_live_probe: PROBE_REDEFERRED`。

---

## DH2-BASE 依赖

| 项                                                | 处置                                                                                                    |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `test_dataHealthIntegration_v2Evidence_bundle` 红 | cherry-pick DH2-BASE：`tests/fixtures/data_health/v2_integration_bundle/` + `_V2_EVIDENCE` 指向 fixture |

---

## pytest 复跑（闭合前）

| 命令                                              | 预期                            |
| ------------------------------------------------- | ------------------------------- |
| `uv run pytest tests/test_tdx_manual_probe.py -q` | 20 passed                       |
| `uv run python scripts/loop_maintain.py`          | exit 0                          |
| `uv run pytest -q`                                | 全绿（commit catalog/index 后） |

---

## 残余风险（非 OPEN）

1. **Live TDX HQ** — 用户填写 host/port 后须主会话或授权会话重跑 live 切片；本分支仅 mocked + REDEFERRED 闭合。
2. **Registry** — `tdx_pytdx` proposed delta 待主会话 Track A §7.4 批处理。
3. **EM / AkShare** — `R3-B2.75-REQ2-EM`、`R3-PROMPT14-AKSHARE-VAL-01` 保持 OPEN（负向测试已覆盖）。

---

_审计日期：2026-06-25 · B01-TDX 零 OPEN 闭合_
