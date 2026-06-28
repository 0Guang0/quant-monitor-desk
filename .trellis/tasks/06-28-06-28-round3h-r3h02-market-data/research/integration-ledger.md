# Integration Ledger — R3H-02

> Plan 5c · 垂直切片与 manifest 对照

## 垂直切片（to-issues S0–S8）

见 `research/to-issues-slices.md`。

## 内联 vs manifest

| 来源                                                      | 处置                               |
| --------------------------------------------------------- | ---------------------------------- |
| 活卡 §1.1 / §2.8                                          | 并入 frozen §1/§2                  |
| 活卡 §4.1–§4.3                                            | 并入 frozen §4                     |
| 活卡 §7 caps                                              | 并入 frozen §7                     |
| 活卡 §8.1                                                 | 并入 frozen §8                     |
| 活卡 §9 九步                                              | 并入 frozen §9；命令在 INDEX §1    |
| 活卡 §10.1                                                | 并入 frozen §10                    |
| grill-me Q1–Q14                                           | 并入 frozen §1/§8/§9               |
| `market_data_evidence_v1` / `crypto_market_evidence_v1`   | inline frozen §5.1 + 代码 SSOT     |
| `R3G_MASS_REHEARSAL_OPEN_GAPS.md` G2/G13/G16              | INDEX §3 must-read                 |
| `backend/app/datasources/adapters/yahoo_finance.py`       | INDEX §3 must-read（迁移源）       |
| `backend/app/ops/sandbox_clean_write/rehearsal_loader.py` | INDEX §3 must-read（yahoo bundle） |
| `backend/app/datasources/fetch_ports/fred_port.py`        | INDEX §3 must-read（模式参照）     |
| BATCH_3H coordinator/hardening                            | INDEX §3 must-read                 |

## Execute 不读

`research/plan-boot.md`、`grill-me-session.md`、`brainstorm-session.md`、本 ledger（除非 handoff 争议）

**Phase 5c complete**
