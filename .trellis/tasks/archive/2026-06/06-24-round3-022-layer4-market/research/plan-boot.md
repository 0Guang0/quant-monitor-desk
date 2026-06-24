# Plan Boot — 06-24-round3-022-layer4-market

## 用户目标摘要

交付 Round 3 Batch 5 **`022`** Layer 4 **market structure** 骨架：`market_registry`、calendar、breadth、market snapshots；行为对齐 `layer4_market_contract.yaml`；快照含 **contract-scoped lineage** 与 **`as_of` / no-future-data** 边界；**staged-only**，不得声称 production-live。

## 原计划已读（ROUND + NNN 任务卡 + GLOBAL）

| 顺序 | 路径                                                              | 要点                                    |
| ---- | ----------------------------------------------------------------- | --------------------------------------- |
| 1    | `docs/implementation_tasks/README.md`                             | Round 顺序；GLOBAL 索引                 |
| 2–5  | `GLOBAL_*.md`（4）                                                | 执行/测试/资源/模板                     |
| 6    | `ROUND_3_MODELING_LAYERS/README.md`                               | 019→021→022 顺序                        |
| 7    | `022_implement_layer4_market_structure.md`                        | registry/calendar/breadth/snapshot      |
| 8    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2–§2.6                    | Wave C 022 allowed/forbidden + 验证命令 |
| 9    | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1+§3.3+§8.2      | 权威索引 + PASS 子 AC                   |
| 10   | `docs/modules/layer4_market_structure.md`                         | MarketAdapter、表结构、验收测试         |
| 11   | `specs/contracts/layer4_market_contract.yaml`                     | models + quality_rules + boundaries     |
| 12   | `specs/contracts/snapshot_lineage_contract.yaml`                  | required_fields + no_future_data        |
| 13   | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                   | staged-only 强制                        |
| 14   | `archive/2026-06/06-24-round3-021-layer3-snapshot/MASTER.plan.md` | 021 lineage defer 边界延续              |

## 前置依赖 / Batch 关系

| 前置                           | 状态     | 证据                                                    |
| ------------------------------ | -------- | ------------------------------------------------------- |
| `021` Layer3 snapshot          | merged   | `backend/app/layer3_chains/snapshot_builder.py` + tests |
| `R3-B3-STAGED-DOWNSTREAM-GATE` | CLOSED   | `BATCH3_STAGED_DOWNSTREAM_GATE.md`                      |
| `R3-B2.75-REQ2-EM`             | DEFERRED | 硬约束；不得作 live 前提                                |

## 预期 AC 草稿（→ MASTER §2）

| AC       | 草稿                                                             |
| -------- | ---------------------------------------------------------------- |
| AC-022-1 | `market_registry` 初始化；`market_id` 唯一                       |
| AC-022-2 | `market_calendar` PK `(market_id, trade_date)`；非交易日快照规则 |
| AC-022-3 | `market_breadth_snapshot` 符合 contract required_fields          |
| AC-022-4 | lineage envelope 含 `LINEAGE_REQUIRED_FIELDS`；`layer_id=layer4` |
| AC-022-5 | `no_future_data`：as_of 之后观测拒绝                             |
| AC-022-6 | staged fixture adapter；无 live fetch / 全市场扫描               |
| AC-022-7 | 不写入 Layer5 全量历史；不复制 Layer1 标准化字段（D-09）         |
| AC-022-8 | Tier A 验收 + batch3 staged gate 绿                              |

## Plan Phase 顺序

P0 Boot → 1a 概览 → 2a prd → 2b spec AC → 3 grill-me → 3.5 vertical-slices → 1b GitNexus → 4 接口草图 → 5a/5b §8 → 5c ledger → 5d integration-audit → 冻结

## Phase P0 complete
