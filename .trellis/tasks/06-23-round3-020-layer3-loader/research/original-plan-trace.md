# Original plan trace — 06-23-round3-020-layer3-loader

| 字段 | 值 |
| ---- | -- |
| Round / Batch | Round 3 Batch 4 |
| Item ID | `020` |
| 原计划任务卡 | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` |
| Batch map 条目 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4 `020` |
| 前置 gate | `019` merged + `R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED |
| 分支 | `feature/round3-020-layer3-loader` |
| 协调 slice | `research/worktree-slices.md` |

## MASTER §2 AC 对照

| AC | 任务卡来源 | 验证 |
| -- | ---------- | ---- |
| AC-020-1 | §1 加载五类 registry | `test_layer3Loader_loadsStagedFixture_success` |
| AC-020-2 | §9 校验 node/edge 引用；contract hard rules | `test_layer3Loader_*_rejectsInvalidRef` |
| AC-020-3 | §9 私有公司 event_only | `test_layer3Loader_eventOnlyPrivate_notDailyPriceAnchor` |
| AC-020-4 | §9 P0 来源完整；contract source_keys | `test_layer3Loader_p0Anchor_missingSourceKeys_rejects` |
| AC-020-5 | §16 staged-only；slice boundary | `test_layer3Loader_nonStagedMode_rejects` |
| AC-020-6 | §11 验收命令 | §10 Tier A |

## Deferred（非本任务）

| 项 | 偿还 |
| -- | ---- |
| `industry_chain_daily_snapshot` / Layer5 view | `021` |
| lineage 持久化 / `snapshot_lineage_contract` 写 | `021`+ / 023A |
| production registry 全量加载 | 未来 batch |
| WriteManager sandbox sync | 可选 defer；本 MASTER 不强制 DB 写 |
| `R3-B2.75-REQ2-EM` live 源 | DEFERRED |

## 权威输入

- `layer3_industry_shock_anchor.md` — 模块权威
- `layer3_loader_contract.yaml` — 硬校验
- `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/**` — registry 形态（fixture 子集）
- `snapshot_lineage_contract.yaml` — **只读**（023A 写权限）
- `GLOBAL_*.md` / `staged_acceptance_policy.md`
- `backend/app/layer2_sensors/sensor_loader.py` — 019 staged loader 模式
