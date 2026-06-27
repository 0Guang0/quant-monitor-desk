# Integration Ledger — R3H-01

> Plan 5c · 垂直切片与 manifest 对照

## 垂直切片（to-issues S0–S8）

见 `research/to-issues-slices.md`。

## 内联 vs manifest

| 来源                                                          | 处置                            |
| ------------------------------------------------------------- | ------------------------------- |
| 活卡 §2.8 Plan/Execute 门                                     | 并入 frozen §2                  |
| 活卡 §4.1 数据流/impact                                       | 并入 frozen §4                  |
| 活卡 §7 caps                                                  | 并入 frozen §7                  |
| 活卡 §8.1 停止条件                                            | 并入 frozen §8                  |
| 活卡 §9 九步                                                  | 并入 frozen §9；命令在 INDEX §1 |
| 活卡 §10.1 对抗矩阵                                           | 并入 frozen §10                 |
| grill-me Q1–Q14                                               | 并入 frozen §2/§8/§9            |
| `official_macro_evidence_v1` 形状                             | inline frozen §4.1 + 代码 SSOT  |
| `R3G_MASS_REHEARSAL_OPEN_GAPS.md`                             | INDEX §3 must-read              |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py`     | INDEX §3 must-read              |
| `backend/app/ops/sandbox_clean_write/live_evidence_bridge.py` | INDEX §3 must-read              |
| `backend/app/ops/fred_fetch_ports.py`                         | INDEX §3 must-read（迁移源）    |
| `backend/app/ops/fred_sandbox_pilot.py`                       | INDEX §3 must-read              |
| `backend/app/ops/live_pilot_phase3.py`                        | INDEX §3 must-read              |
| BATCH_3H coordinator/hardening                                | INDEX §3 must-read              |

## implement.jsonl 锚点

| category | paths                                                                       |
| -------- | --------------------------------------------------------------------------- |
| Boot     | frozen, INDEX, context_pack, trellis-execute                                |
| GLOBAL   | 四文件                                                                      |
| Specs    | registry, capabilities, route, layer5, guardrails, DQ                       |
| Code     | fetch_ports targets, normalizers, route_planner, resource_guard             |
| Tests    | test_official_macro_adapters, test_sec_edgar, route/capabilities/guardrails |
| 3G index | R3G_MASS_REHEARSAL_OPEN_GAPS, r3g03 report                                  |

## Execute 不读

`research/plan-boot.md`、`grill-me-session.md`、`brainstorm-session.md`、本 ledger（除非 handoff 争议）
