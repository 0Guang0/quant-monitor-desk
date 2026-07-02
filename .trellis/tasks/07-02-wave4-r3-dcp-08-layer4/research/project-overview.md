# R3-DCP-08 GitNexus Phase 1a — Project Overview

> **Query:** Layer4 market structure · breadth · US calendar · Tier A clean read  
> **Date:** 2026-07-02 · repo: quant-monitor-desk

## 模块地图（G4 Layer4）

| 组件 | 路径 | 现状 |
|------|------|------|
| MarketStructureBuilder | `backend/app/layer4_markets/market_structure.py` | staged fixture only；`source_mode=staged_fixture_only` 硬闸 |
| Registry seeds | `REGISTRY_SEEDS` in market_structure.py | 8 market_id 元数据 |
| US calendar guard | `us_trading_calendar.is_trading_day` | R3H-07 SSOT；US_EQ build 前 lazy import |
| Lineage | `layer4_markets/lineage.py` | snapshot envelope 与 L2/L3 同型 |
| Staged tests | `tests/test_layer4_market_structure.py` | CN_A 主路径 + US_EQ 日历对称测 |

## Tier A 上游（DCP-05 已交付）

| 域 | 主源 | L4 可用性 |
|----|------|-----------|
| `us_equity_daily_bar` | yahoo_finance / stooq / alpha_vantage | alpha_vantage incremental → `security_bar_1d` clean ✅ |
| `cn_equity_daily_bar` | baostock | mootdx explicit sync → clean ✅（registry 路由待 reconcile） |

## 执行流（当前 vs 目标）

```text
[当前] staged manifest → StagedFixtureMarketAdapter → breadth/calendar JSON
[目标] security_bar_1d clean + us_trading_calendar → CleanMarketAdapter(US_EQ) → breadth + lineage
```

## 关键缺口

1. 无 `CleanMarketAdapter` / clean read path（022 仅 staged）
2. breadth 未从 bar 聚合（fixture 直读）
3. `source_dataset_ids` 仍 `staged:layer4_market:*`
4. registry mootdx dry-run `selected_source_id` 与 `--source-id mootdx` 不一致（台账 open）

## 评级

G4 `R3→R4`：本票完成后 US_EQ clean e2e 绿 → 可升 `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` 子集
