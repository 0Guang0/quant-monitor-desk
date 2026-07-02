# R3-DCP-08 GitNexus Phase 1b — Impact Summary

> **Date:** 2026-07-02 · target symbols for Execute

## Impact 目标符号

| Symbol | 文件 | 预期风险 |
|--------|------|----------|
| `MarketStructureBuilder.build` | `market_structure.py` | **MEDIUM** — 022 全量测 + 新 clean e2e |
| `StagedFixtureMarketAdapter` | `market_structure.py` | **LOW** — 保留 staged 路径，不删 |
| `is_trading_day` | `us_trading_calendar.py` | **LOW** — 只读 SSOT，US_EQ 已接线 |
| `sync_mootdx_incremental` | `data_commands.py` | **MEDIUM** — dry-run JSON 对齐（S08-REG-MOOTDX） |
| `enabled_source_registry` | `macro_incremental_common.py` | **LOW** — registry overlay 复用 |

## 直接调用方（blast radius）

- `tests/test_layer4_market_structure.py` — 全部 AC-022 测须保持绿
- 新增 `tests/test_layer4_us_equity_clean_e2e.py` — 本票主证据
- `tests/test_qmd_data_sync_tier_a_router.py` — mootdx dry-run 扩展
- registry 三件套 — **主会话 merge**（Execute 仅 proposed delta）

## 禁止触碰（并行.stringify）

- `layer1_axes/**` · `layer2_sensors/**` · `layer3_chains/**`（DCP-07 轨）
- Eastmoney hist 真网路径（REQ2-EM 硬约束）
- 新 migration（除非 Audit 证明必需 — 本 Plan 无 migration）

## Execute 门禁

改 `MarketStructureBuilder` / `sync_mootdx_incremental` 前必须 `impact()`；commit 前 `detect_changes()`
