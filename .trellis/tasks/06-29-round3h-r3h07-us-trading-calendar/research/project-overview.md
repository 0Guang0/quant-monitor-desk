# Project Overview — R3H-07（GitNexus 1a）

**Query:** US trading calendar · CAL-US · window_kind · layer4 market_structure · DataSourceService

**Scope:** `ops/data_health_profiles/` · `datasources/fetch_ports/` · `datasources/fetch_window.py` · `layer4_markets/market_structure.py` · `datasources/service.py`

**Date:** 2026-06-29

## Findings

| 区域                    | 现状                                                                                                                | R3H-07 目标                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **CN 日历 G2/G17**      | `cn_trading_calendar.py` + `calendar_gap_rules` `calendar_authority=True` @ R3H-03                                  | **回归不破坏**                                 |
| **US 日历**             | 无 `us_trading_calendar`；US ports 用自然日 `timedelta` + `window_kind: calendar_days`                              | L2 SSOT + `trading_sessions`                   |
| **fetch_window**        | `recent_window_start(calendar_days=14)` only                                                                        | 增 trading-session 窗口 helper                 |
| **US fetch ports**      | `yahoo_finance_port` · `stooq_port` · `alpha_vantage_port` — `MAX_WINDOW_DAYS` 按日历 span                          | 按 trading days 计 span + 过滤 bar             |
| **Evidence normalizer** | `build_daily_bar_evidence_bundle` default `window_kind=calendar_days`                                               | US 路径显式 `trading_sessions`                 |
| **Layer4 G4**           | `MarketStructureBuilder` + `StagedCNAMarketAdapter`；`US_EQ` registry seed 存在但 calendar 来自 staged fixture only | US 非交易日拒绝共用 `us_trading_calendar`      |
| **Layer4 plan YAML**    | `L4-US-DEFERRED` readiness=deferred                                                                                 | 本卡闭合 calendar 语义；非 full US market live |
| **C2 service**          | R3H-10 CLOSED — fetch 经 `DataSourceService`                                                                        | 窗口语义在 evidence bundle + 契约字段可验证    |
| **测试锚点**            | `test_market_data_adapters.py` 断言 `calendar_days`（R3H02-R-22）                                                   | S07-02 翻转 + 假日负向 S07-04                  |

## GitNexus query 摘要

- `fetch_payload → recent_window_start` 流程仍经 `calendar_days`（proc_284 等）
- `parse_pilot_date_window` 有 `trading` vs `calendar` 标签但仅 rehearsal 估算（`1.5x + 2`），**非** SSOT
- `MarketStructureBuilder` 已有 non-trading-day `Layer4MarketError` 模式（CN fixture）

## Caveats

- 参考项目 `参考项目/**` 本地可能 gitignore；US 采纳以 QMD `cn_trading_calendar` 镜像 + ADR-026 为准
- crypto 源不在 CAL-US 范围
- 改 fetch ports / normalizer 前 GitNexus `impact`
