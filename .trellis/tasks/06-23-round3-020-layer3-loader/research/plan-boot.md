# Plan Boot — 06-23-round3-020-layer3-loader

## 用户目标摘要

交付 Round 3 Batch 4 **`020`** Layer 3 产业链配置 loader：加载 chain/anchor/node/edge/cross-chain edge，执行 `layer3_loader_contract.yaml` 硬校验；**staged-only**，不得声称 production-live。模式参考已 merge 的 `019` `sensor_loader.py`（staged_fixture_only）。

## 原计划已读（ROUND + NNN 任务卡 + GLOBAL）

| 顺序 | 路径 | 要点 |
| ---- | ---- | ---- |
| 1 | `docs/implementation_tasks/README.md` | Round 顺序；GLOBAL 索引 |
| 2–5 | `GLOBAL_*.md`（4） | 执行/测试/资源/模板 |
| 6 | `ROUND_3_MODELING_LAYERS/README.md` | `017`–`023` 顺序；019 gate 后 020 |
| 7 | `020_implement_layer3_industry_chain_loader.md` | loader 五表、校验、staged |
| 8 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4 | `020`/`021` 边界 |
| 9 | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` | staged-only 强制引用 |
| 10 | `research/worktree-slices.md` | allowed/forbidden 文件边界 |

## 前置依赖 / Batch 关系

| 前置 | 状态 | 证据 |
| ---- | ---- | ---- |
| `019` Layer2 sensor staged | merged | `archive/2026-06/06-22-round3-019-layer2-sensor` |
| `R3-B3-STAGED-DOWNSTREAM-GATE` | CLOSED | `BATCH3_STAGED_DOWNSTREAM_GATE.md` |
| `R3-B2.75-REQ2-EM` | **DEFERRED** | 硬约束；不得作 live 前提 |
| `021` snapshot builder | 后续 | 本任务不实现 snapshot/lineage 写入 |

## 预期 AC 草稿（→ MASTER §2）

| AC | 草稿 |
| -- | ---- |
| AC-020-1 | 五类 registry 经 staged fixture 加载为 typed result |
| AC-020-2 | contract 硬规则：唯一性、边引用、anchor.node_id |
| AC-020-3 | `event_only` 私有公司不得当日价锚 |
| AC-020-4 | `P0_CORE`/`P0_EVENT` 须有 `source_keys` |
| AC-020-5 | `staged_fixture_only` 模式；禁止 production-live registry |
| AC-020-6 | Tier A 验收命令全绿 |

## Plan Phase 顺序

P0 Boot → 1a 概览 → 2a prd → 2b spec AC → 3 grill-me → 3.5 vertical-slices → 1b GitNexus → 4 接口草图 → 5a/5b §8 → 5c ledger → 5d integration-audit → 冻结

## 路径纠偏

| 任务卡/契约 | 实际 |
| ----------- | ---- |
| registry 包路径 `specs/layer3_global_industry_chains_v1_2/` | 仓库为 `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/` |
| 运行时加载 | Execute 使用 `tests/fixtures/layer3_*` staged 子集，非生产 registry 直读 |

## Phase P0 complete
