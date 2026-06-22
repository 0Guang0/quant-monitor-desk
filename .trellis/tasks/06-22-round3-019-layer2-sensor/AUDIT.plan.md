# AUDIT 计划 — round3-019-layer2-sensor (rev 2)

## Audit Source Trace

- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`（只读）
- `019_implement_layer2_cross_asset_sensor.md` §15–17
- `docs/modules/layer2_cross_asset_sensor.md` §5–7

## AC → 测试 → 证据映射

| AC | 测试 | 证据 |
| -- | ---- | ---- |
| AC-019-1 | `test_crossAssetRegistryLoader_*`, `test_layer2Registry_sync*` | `execute-evidence/8.1-green.txt` |
| AC-019-2 | `test_doubleCountGuard_*`, `test_snapshotBuilder_forModel_*`, `test_vixAxisInput_*` | `8.2-green.txt` |
| AC-019-3 | `test_snapshotRejectsFuture*` | `8.3-green.txt` |
| AC-019-4 | `test_snapshotLineageContainsSourceHashes`, `test_upstreamSnapshotIds_*` | `8.4-green.txt` |
| AC-019-5 | `test_futuresRoll*`, `test_rollEvent_integrated*` | `8.5-green.txt` |
| AC-019-6 | `test_crossAssetSnapshotBuilder_resourceGuard*`, `test_resourceGuard_real*` | `8.6-green.txt` |
| AC-019-7 | `test_layer2Snapshot_writeViaWriteManager` | `8.7-green.txt` |
| AC-019-8 | `test_layer2Observation_writeViaWriteManager` | `8.8-green.txt` |
| deterministic_rebuild | `test_snapshotDeterministicRebuild_*` | `8.4-green.txt` |

## 阻塞级检查

- [x] staged-only：无 production-live 代码路径（audit 2026-06-22；`merge_gate_report.md` rev 3）
- [x] no_future_data：trade_time / as_of_timestamp / fetch_time 三重边界
- [x] double_count：axis input 不可 for_model
- [x] roll event 必须持久化且 roll_event=true
- [x] lineage 写入 `axis_snapshot_lineage`（layer_id=layer2）
- [x] 未修改 `snapshot_lineage_contract.yaml`

## Deferred（非阻塞）

- 模块 §7 staging→DQ→conflict 全流水线
- FastAPI / divergence detector / production migration
