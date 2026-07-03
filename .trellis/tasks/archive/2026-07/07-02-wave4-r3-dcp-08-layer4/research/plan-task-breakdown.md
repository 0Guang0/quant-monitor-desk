# R3-DCP-08 Plan Task Breakdown

> Phase 5a · planning-and-task-breakdown

## Overview

Wave 4 G4 最小竖切：P0 **`US_EQ`** 从 Tier A `security_bar_1d` clean + R3H-07 US 日历 → Layer4 breadth snapshot + lineage；并行 registry 片承接 mootdx dry-run 与 eastmoney taxonomy（不关 REQ2-EM）。

## Architecture Decisions

| #    | 决策                            | 理由                                                             |
| ---- | ------------------------------- | ---------------------------------------------------------------- |
| AD-1 | P0 `market_id=US_EQ`            | R3H-07 日历已接线；Tier A US bar clean 已交付；022 US 测已有基础 |
| AD-2 | 新增 `tier_a_clean` source_mode | 保留 staged 022 AC；不破坏 manifest 硬闸                         |
| AD-3 | registry delta 主会话 merge     | B3F-REG 并行 policy                                              |
| AD-4 | 不关 REQ2-EM                    | 活卡 §3 硬约束                                                   |

## Task List

| Task | Description                | AC                          | Verification | Dependencies | Files                               |
| ---- | -------------------------- | --------------------------- | ------------ | ------------ | ----------------------------------- |
| T1   | clean read + aggregator    | breadth 字段可断言          | unit test    | —            | `clean_read.py`                     |
| T2   | USEquityCleanMarketAdapter | calendar+breadth from clean | adapter test | T1           | `market_structure.py`               |
| T3   | Builder tier_a_clean 入口  | 022 + e2e 绿                | pytest       | T2           | `market_structure.py`               |
| T4   | mootdx registry reconcile  | ACC-MOOTDX 关               | router test  | —            | registry delta · `data_commands.py` |
| T5   | eastmoney taxonomy docs    | ACC-EASTMONEY 部分          | rg + ops     | —            | registry · ops md                   |
| T6   | L4 e2e evidence            | ACC-LAYER-E2E L4            | e2e md       | T3           | tests · research                    |

## Checkpoints

- CP1: S08-READ GREEN
- CP2: S08-E2E GREEN + 022 无回归
- CP3: registry 片 + CLOSE 全绿

## Risks

| 风险                                       | 缓解                                                                                |
| ------------------------------------------ | ----------------------------------------------------------------------------------- |
| mootdx 升 primary 与 baostock 产品路径冲突 | domain primary 保持 baostock；explicit `--source-id mootdx` 路由 overlay（ADR-033） |
| breadth 聚合口径与设计文档全字段差距       | ponytail 最小字段；index/sector 后续票                                              |
| registry 并行 merge 冲突                   | proposed delta YAML；主会话单点 apply                                               |

## Open Questions

无 — P0 market_id 已定案 US_EQ（见 doubt review Cycle 1）。
