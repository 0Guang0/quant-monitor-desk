# Plan Boot — R3-DCP-06 Layer1 五轴真 clean（G12）

> **轨道：** Wave 4b · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`  
> **前置：** R3-DCP-05 ✅ @ `c2258363`

---

## Phase P0 complete

### 1. 做什么

让 Layer1 **五轴**各至少一条 P0 指标从 **Tier A clean 表**（非 staged fixture）读入 → 特征/解释 → pytest 绿；闭合路线图 §3.5.1 PASS 硬门禁与 `ACC-LAYER-E2E-LIVE-001` L1 子集。

### 2. 价值

- Wave 4 **R3-DCP-06** 硬交付；G1/K2 R3→R4
- 正式 PASS 前置（仍待 Wave 5 GATE 与 L3–L5 余票）

### 3. 约束

| 约束   | 要求                                                 |
| ------ | ---------------------------------------------------- |
| 输入   | DCP-05 clean：`axis_observation` + `security_bar_1d` |
| 无 DDL | R3H-06 + 015 已封                                    |
| 参考   | L1/L2/L3 仅 `参考项目/**`                            |
| 台账   | `ACC-LAYER-E2E-LIVE-001` 部分关；L3–L5 阶段外置      |
| 硬约束 | 不关 `B2.5-O-05`                                     |

### 4. 架构触点

`layer1_axes` clean reader → feature_engine → interpretation → snapshot lineage

### 5. 成功标准

活卡 §5 + §3.5.1 全 [x] + `uv run pytest -q`

### 6. P0 已读清单

- [x] `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1、§3.5.2
- [x] `R3_DCP_TO_ISSUES_INDEX.md` §6.2
- [x] `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`
- [x] `docs/modules/layer1_global_regime_panel.md`
- [x] `specs/layer1_axes/restructured_axes_v1_1/**`（五轴 + common）
- [x] `specs/contracts/layer1_axis_contract.yaml`
- [x] `specs/model_inputs/layer1_source_whitelist.yaml`
- [x] `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`
- [x] `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`
- [x] `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md`
- [x] `backend/app/layer1_axes/{ingestion,feature_engine,axis_loader}.py`
- [x] `docs/quality/待修复清单.md` §4 `ACC-LAYER-E2E-LIVE-001`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] 参考项目实读：OpenBB fetcher + fred_base, digital-oracle fear_greed, EasyXT unified_data_interface
- [x] GitNexus query + impact(`Layer1ObservationIngestionService`) — LOW

### 7. 与 DCP-05 差异

| 项        | DCP-05           | DCP-06                     |
| --------- | ---------------- | -------------------------- |
| 域        | 数据同步写 clean | Layer1 **读** clean + 算轴 |
| migration | 015              | **无**                     |
| 并行      | 按源 11 路       | 按轴 5 路 + core           |
| PASS      | 数据面前置       | **五轴硬门禁**             |
