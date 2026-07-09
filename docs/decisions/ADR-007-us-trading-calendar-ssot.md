# ADR-007：美股交易日历单一事实来源

## 状态

已接受

## 日期

2026-06-29

## 背景

美股/全球股票类源（`yahoo_finance`、`stooq`、`alpha_vantage`）仍使用自然日窗口（`window_kind: calendar_days`）与 `fetch_window.recent_window_start(calendar_days=…)`。A 股日历已在 R3H-03 闭合（`cn_trading_calendar.py`）。R3H-10 已闭合 C2 SSOT，窗口语义须能通过 `DataSourceService` 拉数/证据路径验证。R3H-06 范围内不新增 clean 层 DDL。

## 决策

1. **权威模块：** 新增 `backend/app/ops/data_health_profiles/us_trading_calendar.py` 作为 QMD 自有 L2 SSOT，形态对齐 `cn_trading_calendar.py`（`is_trading_day`、`get_trading_days`、`get_missing_trading_days`）。
2. **覆盖范围：** NYSE/Nasdaq **合并**美股休市集合，以有界 `frozenset` 表达 `2000-01-01` … `2030-12-31`（周末 + 美国联邦市场假日）。ponytail 上限：2030 年之后须交易所权威 feed 或 ADR 扩展（同 CN `CAL-CN-TAIL` 模式）。
3. **窗口类型：** 美股日线域（`us_equity_daily_bar` 及相关 market_bar fetch plan）在证据包中输出 `window_kind: trading_sessions`；跨度上限按**交易日会话**计数，非自然日。
4. **共享 helper：** 扩展 `backend/app/datasources/fetch_window.py`，提供 trading-session 窗口 helper，供美股 fetch port 使用（非仅 ops 垫片）。
5. **Layer4 G4：** `MarketStructureBuilder` / 美股 adapter 路径对 `US_EQ` 非交易日拒绝使用**同一** `us_trading_calendar`（有界 fixture 行；不做全市场扫描）。
6. **明确排除：** `deribit`、`coingecko`、加密域仍按 `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` §CAL-US 范围保持 `calendar_days` ponytail。

## 曾考虑的替代方案

| 方案                                       | 否决原因                                                 |
| ------------------------------------------ | -------------------------------------------------------- |
| pandas_market_calendars / 运行时交易所 API | 新依赖 + 网络；违背 ponytail 与离线 replay-first         |
| DB 表 + migration                          | 除非 Batch6 ADR，否则超出范围；CN 先例为内存 frozenset   |
| 仅 Mon–Fri 工作日代理                      | 无法满足 CAL-US AC（感恩节等）；INDEX §2 负例测试 S07-04 |
| 每源各建假日表                             | 违背 SSOT；C3 与 G4 须共用同一模块                       |

## 后果

- **正面：** CAL-US 可关账；C3/G4 共用一模块；CN 回归隔离在 `cn_trading_calendar` 测试。
- **负面：** 假日表维护 ponytail 止于 2030；R3H-02 证据契约测须将美股源的 `calendar_days` 翻转为 `trading_sessions`。

## 绑定切片

- **S07-01** — 数据平面（`us_trading_calendar.py`）
- **S07-02** — C3 fetch port + `window_kind`
- **S07-03** — G4 loader
- **S07-04** — 假日负例测试
