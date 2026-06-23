# Plan Boot — 06-24-round3-021-layer3-snapshot

## 用户目标摘要

交付 Round 3 Batch 4 **`021`** Layer 3 industry-chain **snapshot builder**：从 `020` `IndustryChainLoader` 输出 + staged Layer5 行情 fixture 生成 `industry_chain_daily_snapshot` 行与 Layer5 映射视图；附带 **contract-scoped** lineage envelope；**staged-only**，不得声称 production-live。

## 原计划已读（ROUND + NNN 任务卡 + GLOBAL）

| 顺序 | 路径                                                            | 要点                               |
| ---- | --------------------------------------------------------------- | ---------------------------------- |
| 1    | `docs/implementation_tasks/README.md`                           | Round 顺序；GLOBAL 索引            |
| 2–5  | `GLOBAL_*.md`（4）                                              | 执行/测试/资源/模板                |
| 6    | `ROUND_3_MODELING_LAYERS/README.md`                             | `019`→`020`→`021` 顺序             |
| 7    | `021_implement_layer3_snapshot_builder.md`                      | snapshot + Layer5 mapping view     |
| 8    | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4                  | `021` as_of + lineage 主题         |
| 9    | `docs/modules/layer3_industry_shock_anchor.md` §8.6/8.12        | snapshot 表 + daily snapshot 流程  |
| 10   | `specs/contracts/snapshot_lineage_contract.yaml`                | required_fields + validation_tests |
| 11   | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`                 | staged-only 强制                   |
| 12   | `archive/2026-06/06-23-round3-020-layer3-loader/MASTER.plan.md` | 020 模式参考                       |

## 前置依赖 / Batch 关系

| 前置                           | 状态     | 证据                                                  |
| ------------------------------ | -------- | ----------------------------------------------------- |
| `020` Layer3 loader            | merged   | `backend/app/layer3_chains/loader.py` + tests 绿      |
| `R3-B3-STAGED-DOWNSTREAM-GATE` | CLOSED   | `BATCH3_STAGED_DOWNSTREAM_GATE.md`                    |
| `R3-B23A-EVIDENCE-FOUNDATION`  | stable   | 最小 L5 引用契约；本任务用 staged fixture 不依赖 live |
| `R3-B2.75-REQ2-EM`             | DEFERRED | 硬约束；不得作 live 前提                              |

## 预期 AC 草稿（→ MASTER §2）

| AC       | 草稿                                                         |
| -------- | ------------------------------------------------------------ |
| AC-021-1 | loader 结果 + staged L5 bars → per-anchor snapshot 行        |
| AC-021-2 | lineage envelope 含 contract required_fields + source hashes |
| AC-021-3 | `no_future_data`：as_of 之后观测拒绝                         |
| AC-021-4 | `event_only` anchor 跳过价量字段                             |
| AC-021-5 | Layer5 mapping view（非 event_only）                         |
| AC-021-6 | staged-only；禁止 live L5 fetch                              |
| AC-021-7 | Tier A 验收命令全绿                                          |

## Plan Phase 顺序

P0 Boot → 1a 概览 → 2a prd → 2b spec AC → 3 grill-me → 3.5 vertical-slices → 1b GitNexus → 4 接口草图 → 5a/5b §8 → 5c ledger → 5d integration-audit → 冻结

## Phase P0 complete
