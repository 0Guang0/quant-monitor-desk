# Original plan trace — 06-24-round3-021-layer3-snapshot

| 字段           | 值                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------- |
| Round / Batch  | Round 3 Batch 4                                                                              |
| Item ID        | `021`                                                                                        |
| 原计划任务卡   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md` |
| Batch map 条目 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 4 `021`                                         |
| 前置 gate      | `020` merged + `R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED                                         |
| 分支           | `feature/round3-021-layer3-snapshot`                                                         |

## MASTER §2 AC 对照

| AC       | 任务卡来源                    | 验证                                                      |
| -------- | ----------------------------- | --------------------------------------------------------- |
| AC-021-1 | §1 snapshot 行                | `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success` |
| AC-021-2 | §15 lineage 字段              | `test_snapshotLineageContainsSourceHashes`                |
| AC-021-3 | §15 as_of / 未来数据          | `test_snapshotRejectsFutureInput`                         |
| AC-021-4 | §8.12.6 event_only            | `test_layer3Snapshot_eventOnly_skipsPriceFields`          |
| AC-021-5 | §2 Layer5 边界 / mapping view | `test_layer3Snapshot_layer5MappingView_nonEventOnly`      |
| AC-021-6 | §16 staged-only               | `test_layer3Snapshot_nonStagedL5Source_rejects`           |
| AC-021-7 | §11 验收命令                  | §10 Tier A                                                |

## Deferred / Register（§3.2）

| 项                                       | 021 范围                               | 偿还                   |
| ---------------------------------------- | -------------------------------------- | ---------------------- |
| `ADV-R3X-LINEAGE-001` 全量 L3/L4 lineage | staged skeleton + contract pytest only | `022`/Batch 5          |
| `R3Y-LINEAGE-VR-001` 三 registry VR 行   | MASTER 边界登记 only                   | registry hygiene slice |

## 权威输入

- `layer3_industry_shock_anchor.md` — snapshot 表与流程
- `snapshot_lineage_contract.yaml` — **只读**
- `backend/app/layer3_chains/loader.py` — 020 输出
- `backend/app/layer2_sensors/snapshot_builder.py` — 模式参考
- `GLOBAL_*.md` / `staged_acceptance_policy.md`
