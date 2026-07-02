# EXTERNAL-INDEX — R3-DCP-07

> 包外必读 · Execute 路由

---

## §A 切片开工前必读（外部）

| 路径 | 用途 |
|------|------|
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_07_LAYER2_CROSS_ASSET.md` | 活卡 scope / AC |
| `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_TO_ISSUES_INDEX.md` §6.3 | Wave 索引 |
| `docs/modules/layer2_cross_asset_sensor.md` | G2 模块设计 |
| `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md` | P0 锚点 |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | clean 表 |
| `specs/contracts/reference_adoption_guardrails.yaml` | L 梯铁律 |
| `docs/quality/待修复清单.md` §4 | `ACC-LAYER-E2E-LIVE-001` |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5 | Wave 4 波次 |

---

## §B 执行情境路由（外部）

| 情境 | 路径 |
|------|------|
| fred clean 种子 | `tests/test_fred_macro_incremental_e2e.py` |
| Layer1 VIXCLS 先例 | `tests/test_layer1_risk_appetite_clean_e2e.py` |
| staged L2 契约 | `tests/test_layer2_sensor_loader.py` |
| clean 写路由 | `backend/app/ops/sandbox_clean_write/clean_write_targets.py` |
| production live | `docs/quality/production_live_pilot_policy.md` |

---

## §C 源码/测试字典

| Symbol / 表 | 路径 |
|-------------|------|
| `CrossAssetRegistryLoader` | `backend/app/layer2_sensors/sensor_loader.py` |
| `CrossAssetSnapshotBuilder` | `backend/app/layer2_sensors/snapshot_builder.py` |
| `Layer2LineageBuilder` | `backend/app/layer2_sensors/lineage.py` |
| `axis_observation` | migration 015 / R3H-06 |
| `security_bar_1d` | bar clean（本票非 P0） |
| P0 registry fixture | `tests/fixtures/layer2_cross_asset_registry_fixture.yaml` |
