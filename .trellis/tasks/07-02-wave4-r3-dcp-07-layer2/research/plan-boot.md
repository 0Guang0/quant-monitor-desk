# Plan Boot — R3-DCP-07 Layer2 跨资产真 clean（G2）

> **轨道：** Wave 4c · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `R3_DCP_07_LAYER2_CROSS_ASSET.md`  
> **前置：** R3-DCP-05 ✅ · R3-DCP-06 ✅

---

## Phase P0 complete

### 1. 做什么

选 **一条** P0 cross-asset 传感器（**L2-VIX / VIXCLS**），从 DCP-05 写入的 Tier A **`axis_observation`** clean 读真市况 → `CrossAssetSnapshotBuilder` 产出可断言 snapshot + lineage → pytest 绿；闭合 `ACC-LAYER-E2E-LIVE-001` **L2 子集**。

### 2. 价值

- Wave 4 **R3-DCP-07**；G2 `R3→R4`（`MODULE_COMPLETION_RATING`）
- 为 DCP-08/10 与 Wave 5 `R3H-05-GATE` 提供 L2 真 clean 证据

### 3. 约束

| 约束 | 要求 |
|------|------|
| P0 锚点 | `L2-VIX` · `indicator_id=VIXCLS` · `axis_observation` |
| 输入 SSOT | Tier A clean；禁止 staged fixture 冒充 PASS |
| 无 DDL | R3H-06 + 015 已封 |
| 范围 | **单传感器**竖切；禁止五资产一次落地 |
| 参考 L 梯 | 仅 `参考项目/**` |
| 台账 | `ACC-LAYER-E2E-LIVE-001` L2 子集关账；L3–L5 阶段外置 |

### 4. 架构触点

`axis_observation` (VIXCLS) → `Layer2CleanObservationReader` → `CrossAssetSnapshotBuilder` → `Layer2LineageBuilder` → e2e pytest

### 5. 成功标准

活卡 §5 + `validate-plan-freeze` exit 0 + Execute 后 `uv run pytest -q`

### 6. P0 已读清单

- [x] `R3_DCP_07_LAYER2_CROSS_ASSET.md`
- [x] `R3_DCP_TO_ISSUES_INDEX.md` §6.3
- [x] `docs/modules/layer2_cross_asset_sensor.md`
- [x] `docs/generated/project_map.generated.md`（G2 layer2_sensors）
- [x] `backend/app/layer2_sensors/{sensor_loader,snapshot_builder,lineage,observation}.py`
- [x] `tests/test_layer2_sensor_loader.py`
- [x] `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`
- [x] `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`（VIXCLS 先例）
- [x] `backend/app/ops/sandbox_clean_write/clean_write_targets.py`（macro → axis_observation）
- [x] `docs/quality/待修复清单.md` §4 `ACC-LAYER-E2E-LIVE-001`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] 参考项目实读：OpenBB fetcher + fred_base, EasyXT unified_data_interface
- [x] GitNexus query + impact(`CrossAssetSnapshotBuilder`) — LOW

### 7. 与 DCP-06 差异

| 项 | DCP-06 | DCP-07 |
|----|--------|--------|
| 层 | Layer1 五轴 | Layer2 **单**跨资产传感器 |
| clean 表 | axis_observation + security_bar_1d | **axis_observation**（VIXCLS） |
| 并行度 | 五轴 + core | S00 core + S01 e2e + S02 台账 |
| 评级 | G1/K2 | **G2** |
