# Brainstorm Session — R3H-02（Plan 2a）

> trellis-brainstorm · 2026-06-28

## 问题陈述

五源（alpha_vantage, stooq, yahoo, deribit, coingecko）如何从 proposed-disabled/scaffold 闭合到 Batch 3H 终态，且不与 R3H-01/03/04 registry 冲突？

## 方案对比

| 方案 | 描述                                                  | 裁决                                                 |
| ---- | ----------------------------------------------------- | ---------------------------------------------------- |
| A    | 仅 yahoo 3G fixture 包装为 READY                      | **否决** — hardening 要求五源全闭环                  |
| B    | 单 `market_adapter.py` 五源分支                       | **否决** — 隐藏 auth/caps/evidence 差异              |
| C    | 双 normalizer（market_data + crypto_market）+ 五 port | **采纳** — 对齐 R3H-01 official_macro 模式           |
| D    | yahoo 升格 primary 闭合 G16                           | **否决** — registry validation_only + 路线图         |
| E    | 本卡实现 TradingCalendar 闭合 G2                      | **否决** — 范围过大；ponytail 自然日窗 + R3H-03 协调 |

## 采纳架构

```text
market_data.py (OHLCV/ETF/FX/commodity)
crypto_market.py (deribit/coingecko)
five fetch_ports (mock-first, live opt-in where applicable)
coordinator manifest for registry delta
Layer smoke only
```

## 风险表

| 风险                      | 缓解                                 |
| ------------------------- | ------------------------------------ |
| 期权链/衍生品 cap 突破    | §7 硬 cap + reject_over_cap          |
| aggregator silent primary | route 负例 + R3X validation block 测 |
| 3G yahoo 双路径           | §9.4 统一 replay fixture             |
| registry 并行冲突         | §9.6 coordinator-only                |

**Phase 2a complete**
