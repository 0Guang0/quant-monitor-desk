# Original plan trace — 06-22-round3-019-layer2-sensor

| 字段 | 值 |
| ---- | -- |
| Round / Batch | Round 3 Batch 3 |
| Item ID | `019` |
| 原计划任务卡 | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md` |
| 并行提示词 | `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_07_feature_round3_019_layer2_sensor.md` |
| Batch map 条目 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` § Batch 3 `019` |
| 前置 gate | `R3-B3-STAGED-DOWNSTREAM-GATE` (PROMPT_01 closed) |
| 分支 | `feature/round3-019-layer2-sensor` |

## MASTER AC 对照

| AC | 任务卡来源 | 验证测试 |
| -- | ---------- | -------- |
| AC-019-1 | §9 registry loader | `test_crossAssetRegistryLoader_*` |
| AC-019-2 | §5 double_count_guard | `test_doubleCountGuard_*`, `test_vixAxisInput_*` |
| AC-019-3 | §15 no_future_data | `test_snapshotRejectsFuture*` |
| AC-019-4 | §15 lineage | `test_snapshotLineageContainsSourceHashes` |
| AC-019-5 | §6 futures roll | `test_futuresRollHandler_*` |
| AC-019-6 | §7 ResourceGuard | `test_crossAssetSnapshotBuilder_resourceGuard*` |
| AC-019-7 | §5 WriteManager | `test_layer2*writeViaWriteManager` |
| AC-019-8 | §4 observation | `test_layer2Observation_writeViaWriteManager` |

## Deferred pipeline steps (module §7)

| Step | Status |
| ---- | ------ |
| staging_cross_asset_observation | deferred Batch 4+ |
| DataQualityValidator | deferred |
| SourceConflictValidator | deferred |
| cross_asset_signal_snapshot | deferred |


- `BATCH3_STAGED_DOWNSTREAM_GATE.md` — staged-only，不解锁 production-live
- `docs/ROUND3_HANDOFF.md` — PILOT_FAIL_SOURCE，019 可 staged 开工
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` — R3-B2.75-01 DEFERRED，REQ2-EM open
- `layer2_cross_asset_sensor.md` — 表结构、防双算、roll 规则
- `layer2_sensor_contract.yaml` — registry/snapshot 必填字段
- `snapshot_lineage_contract.yaml` — lineage 必填（本分支只读）
- `GLOBAL_EXECUTION_RULES.md` / `GLOBAL_TESTING_POLICY.md` / `GLOBAL_RESOURCE_LIMITS.md`
- PROMPT_01 `merge_gate_report.md` — gate 关闭证据
