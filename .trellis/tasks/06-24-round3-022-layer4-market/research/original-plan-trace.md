# Original plan trace — 06-24-round3-022-layer4-market

| 字段           | 值                                                                                           |
| -------------- | -------------------------------------------------------------------------------------------- |
| Round / Batch  | Round 3 Batch 5                                                                              |
| Item ID        | `022`                                                                                        |
| 原计划任务卡   | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` |
| Batch map 条目 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 5 `022`                                         |
| Wave C gate    | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.3 + §8.2                                    |
| 前置 gate      | `021` merged + `R3-B3-STAGED-DOWNSTREAM-GATE` CLOSED                                         |
| 分支           | `feature/round3-022-layer4-market`                                                           |

## MASTER §2 AC 对照

| AC       | 任务卡来源                 | 验证                                                              |
| -------- | -------------------------- | ----------------------------------------------------------------- |
| AC-022-1 | §1 registry                | `test_marketRegistry_uniqueMarketIds`                             |
| AC-022-2 | module doc §10 calendar    | `test_marketCalendar_rejectsDuplicateTradeDate`                   |
| AC-022-3 | contract breadth model     | `test_marketBreadth_requiredFieldsPresent`                        |
| AC-022-4 | §15 lineage                | `test_marketSnapshot_lineageRequiredFieldsComplete`             |
| AC-022-5 | §15 as_of / 未来数据       | `test_marketSnapshotRejectsFutureInput`                           |
| AC-022-6 | §16 staged / MAP Wave C    | `test_marketAdapter_nonStagedSource_rejects`                      |
| AC-022-7 | D-09 / contract boundaries | `test_marketSnapshot_noLayer5HistoryFields`                       |
| AC-022-8 | §11 验收 + playbook §8.2   | §10 Tier A                                                        |

## Deferred / Register（§3.2）

| 项                                       | 022 in-scope                                      | 偿还 / 登记                          |
| ---------------------------------------- | ------------------------------------------------- | ------------------------------------ |
| `ADV-R3X-LINEAGE-001` L4 完整 DB 持久化   | envelope + pytest；可选 upstream L3 snapshot_id   | Batch 6 / ops repay                  |
| `R3Y-LINEAGE-VR-001` 三 registry VR 行   | MASTER 边界登记 only                              | registry hygiene slice               |
| 全量 8 MarketAdapter live 实现           | registry 种子 + 1 staged adapter                  | 后续 batch / ops                     |
| FastAPI `/api/layer4/*`                  | out                                               | Round 4+                             |

## 权威输入

- `layer4_market_structure.md` — adapter + 表 + 验收
- `layer4_market_contract.yaml` — **主契约**
- `snapshot_lineage_contract.yaml` — **只读**
- `backend/app/layer3_chains/snapshot_builder.py` — 021 上游模式
- `GLOBAL_*.md` / `staged_acceptance_policy.md` / playbook §3.1+§3.3
