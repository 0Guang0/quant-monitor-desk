# R3-DCP-08 EXTERNAL-INDEX — 包外文档索引

> **Execute：** 开工前 Read §A；编码中按 §B/§C 路由  
> **活卡路径（不移动）：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`

---

## §A — 切片开工前必读（外部）

| # | 路径 | 用途 |
|---|------|------|
| A1 | `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` | 活卡 §1–§7 AC |
| A2 | `docs/modules/layer4_market_structure.md` | G4 设计权威 |
| A3 | `docs/quality/待修复清单.md` §4 | ACC-MOOTDX · ACC-EASTMONEY · ACC-LAYER-E2E |
| A4 | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 | Wave 4 挂钩 |
| A5 | `docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md` | US 日历 |
| A6 | `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | Tier A clean 域 |
| A7 | `docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md` | 本票 ADR |
| A8 | `specs/contracts/reference_adoption_guardrails.yaml` | L1/L2/L3 铁律 |
| A9 | `docs/ops/data_sync_quick_reference.md` | eastmoney taxonomy / sync CLI |
| A10 | `.trellis/tasks/archive/2026-06/06-29-round3h-r3h07-us-trading-calendar/research/00-EXECUTION-ENTRY.md` | R3H-07 只读 trace |

---

## §B — 执行情境路由（外部）

| 情境 | 路径 |
|------|------|
| REQ2-EM 硬约束 | `docs/quality/待修复清单.md` §3 `R3-B2.75-REQ2-EM` |
| Tier A 11 源路由 | `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/to-issues-slices.md` |
| Layer1 clean e2e 模式 | `tests/layer1_clean_e2e_support.py` |
| B3F-REG merge policy | `docs/quality/coordination/WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` |
| 022 Layer4 原始 AC | `.trellis/tasks/archive/2026-06/06-24-round3-022-layer4-market/` |

---

## §C — 源码/测试字典

| 符号 | 路径 |
|------|------|
| MarketStructureBuilder | `backend/app/layer4_markets/market_structure.py` |
| US calendar | `backend/app/ops/data_health_profiles/us_trading_calendar.py` |
| alpha_vantage incremental | `backend/app/ops/alpha_vantage_incremental_run.py` |
| mootdx sync | `backend/app/cli/data_commands.py` (`sync_mootdx_incremental`) |
| source_registry | `specs/datasource_registry/source_registry.yaml` |
| source_capabilities | `specs/datasource_registry/source_capabilities.yaml` |
| 022 tests | `tests/test_layer4_market_structure.py` |
| mootdx router tests | `tests/test_qmd_data_sync_tier_a_router.py` |
| staged fixture | `tests/fixtures/layer4_staged_market/` |

---

## §D — 并行轨边界

| 轨 | 禁止本轨修改 |
|----|--------------|
| DCP-07 Layer2 | `backend/app/layer2_sensors/**` |
| DCP-09 CI | `scripts/wave3_*` CI 主改 |
| DCP-10 L5 | `backend/app/layer5_evidence/**` |
