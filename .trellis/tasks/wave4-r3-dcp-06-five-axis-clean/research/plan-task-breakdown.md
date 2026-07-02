# Plan Task Breakdown — R3-DCP-06

## Overview

Deliver G12 five-axis PASS: each axis reads Tier A clean data, computes features/interpretation, and passes dedicated pytest. No new migrations.

## Architecture Decisions

| ID   | 决策                                             | 理由                                     |
| ---- | ------------------------------------------------ | ---------------------------------------- |
| AD-1 | 新 clean reader 模块，不替换 staged ingestion 桥 | 018A 桥保留；LOW impact                  |
| AD-2 | 每轴 1 P0 锚点（ADR-029）                        | ponytail 可交付；全 YAML 指标属 Batch 6+ |
| AD-3 | 流动性用 alpha_vantage bar Amihud                | tiingo 非 Tier A；ponytail 有升级路径    |
| AD-4 | replay 种子 DB（tmp_path）                       | 与 DCP-05 e2e 一致；live 非本票必须项    |
| AD-5 | ACC-LAYER-E2E-LIVE-001 L1 关、L3–L5 阶段外置     | 路线图 §3.5.2                            |

## Task List

| Task   | Description                | AC                | Verify                                   | Deps  | Files                                     |
| ------ | -------------------------- | ----------------- | ---------------------------------------- | ----- | ----------------------------------------- |
| T1 S00 | Clean reader + no-fallback | unit 绿           | `test_layer1CleanReader_*`               | —     | `layer1_axes/clean_observation_reader.py` |
| T2 S01 | Environment axis           | e2e 绿            | `test_layer1_environment_clean_e2e.py`   | T1    | tests + seed helper                       |
| T3 S02 | Credit stress              | e2e 绿            | `test_layer1_credit_stress_clean_e2e.py` | T1    | tests                                     |
| T4 S03 | Risk appetite              | e2e 绿            | `test_layer1_risk_appetite_clean_e2e.py` | T1    | tests                                     |
| T5 S04 | Liquidity ponytail         | e2e 绿 + ADR note | `test_layer1_liquidity_clean_e2e.py`     | T1    | tests + bar helper                        |
| T6 S05 | Sentiment COT              | e2e 绿            | `test_layer1_sentiment_clean_e2e.py`     | T1    | tests                                     |
| T7 S06 | Integration + ledger       | §3.5.1 [x]        | full pytest                              | T2–T6 | K1 yaml, MCR, 待修复清单                  |

## Checkpoints

1. S00 merge → 五轴并行开工
2. 五轴 e2e 绿 → S06
3. Audit A1–A8 → Repair → `validate-plan-freeze` 已先于 Execute

## Risks

| 风险                            | 缓解                                           |
| ------------------------------- | ---------------------------------------------- |
| indicator_id 与 YAML 不完全一致 | ADR-029 锁定 P0 id；loader 测对齐              |
| COT 行形状与 macro 不同         | observation_mapper 扩或 COT 专用 mapper（S05） |
| 流动性 spec 与实现张力          | ponytail 注释 + 阶段外置 tiingo 全路径         |

## Open Questions

无 — Plan 阶段无需 grill-gate（P0 锚点与 ADR-029 已绑定路线图）。
