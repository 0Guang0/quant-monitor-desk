# GitNexus Summary — R3H-07（1b impact）

**Targets:** `build_daily_bar_evidence_bundle` · `recent_window_start` · US fetch ports · `MarketStructureBuilder.build`

## Blast radius

| Symbol / 区域                                             | 直接调用方                          | 风险                              |
| --------------------------------------------------------- | ----------------------------------- | --------------------------------- |
| `build_daily_bar_evidence_bundle` (`window_kind` default) | yahoo/stooq/AV ports · replay tests | **MEDIUM** — 契约字段翻转         |
| `recent_window_start`                                     | fetch ports · ops shims             | **MEDIUM** — 窗口起点语义         |
| `YahooFinanceMockFetchPort.fetch_payload`                 | adapter · service fetch chain       | **MEDIUM**                        |
| `StooqMockFetchPort` / `AlphaVantageMockFetchPort`        | 同上                                | **MEDIUM**                        |
| `MarketStructureBuilder.build`                            | layer4 tests · sandbox pilots       | **MEDIUM** — US_EQ 路径           |
| `cn_trading_calendar`                                     | `calendar_gap_rules` · CN health    | **LOW** if untouched              |
| `DataSourceService.fetch`                                 | Sync · CLI · tests                  | **LOW** — 不改编排，只变 evidence |

## Affected execution flows

- US market data replay fetch (`fetch_payload → recent_window_start`)
- Layer4 staged market build（calendar row validation）
- `test_market_data_adapters.py` evidence contract（R3H02-R-22 需更新）
- `test_layer4_market_structure.py`（可扩 US 假日用例）

## Change guidance

- **单一 SSOT：** 假日逻辑只写在 `us_trading_calendar.py`；ports/layer4 import 它，禁止 per-source 假日表
- **CN 隔离：** 不修改 `cn_trading_calendar.py`；回归 `tests/test_cn_market_adapters.py` 日历用例
- commit 前 `detect_changes({scope: "compare", base_ref: "master"})`

**Risk level:** MEDIUM（触及 evidence 契约 + 多 US port；不触 Sync fail-closed 核心）
