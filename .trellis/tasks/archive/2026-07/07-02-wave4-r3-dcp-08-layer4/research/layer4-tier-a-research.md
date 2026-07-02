# Layer4 Tier A Clean Read — Trellis Research

> **Query:** How US_EQ market structure can read from Tier A clean instead of staged fixture  
> **Scope:** `security_bar_1d` · `us_trading_calendar` · `MarketStructureBuilder`  
> **Date:** 2026-07-02

## Findings

1. **DCP-05** 已交付 `us_equity_daily_bar` → `security_bar_1d` clean write（alpha_vantage replay e2e 绿）。
2. **022** `MarketStructureBuilder` 硬闸 `source_mode=staged_fixture_only`；manifest 非 staged 即拒。
3. **R3H-07** `US_EQ` build 已调用 `is_trading_day`（`market_structure.py:191-197`），与 fixture `is_trading_day` 双重守卫一致。
4. **breadth.json** fixture 字段：`advancers`, `decliners`, `total_amount`, `breadth_label` — 可从 bar 表聚合：
   - `advancers` = count(close > pre_close)
   - `decliners` = count(close < pre_close)
   - `total_amount` = sum(amount) 或 volume×close ponytail 近似
5. **calendar row** 可由 `us_trading_calendar.get_trading_days` + 单 trade_date 行合成（`source=us_trading_calendar_ssot`）。

## Caveats

- 第一版 **不** 拉 sector/index 快照（活卡非目标）；仅 breadth + calendar 最小竖切。
- 默认 **replay** sandbox DB；live 须 `QMD_ALLOW_LIVE_FETCH=1` + 隔离库（对称 DCP-05/06）。
- CN_A 留作 Wave 4+ 第二竖切；本票 registry 片仍处理 cn 域 mootdx/eastmoney。

## 推荐 Execute 触点

| 新/改模块                                                       | 职责                                                      |
| --------------------------------------------------------------- | --------------------------------------------------------- |
| `layer4_markets/clean_read.py`                                  | 从 DuckDB `security_bar_1d` 读 US bar + 聚合 breadth      |
| `USEquityCleanMarketAdapter`                                    | `load_calendar` / `load_breadth` 走 clean + calendar SSOT |
| `MarketStructureBuilder.build(..., source_mode="tier_a_clean")` | 新入口；staged 路径不变                                   |
| `tests/layer4_clean_e2e_support.py`                             | bootstrap sandbox DB + seed replay bars                   |
| `tests/test_layer4_us_equity_clean_e2e.py`                      | 主 AC 证据                                                |
