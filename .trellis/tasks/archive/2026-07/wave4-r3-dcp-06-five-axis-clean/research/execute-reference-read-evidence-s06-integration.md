# Execute 参考实读证据 — S06 主会话集成收口

> 主会话 S06 · 五轴已 merge · 对照 `reference-adoption-dcp06.md`

## 实读清单

- [x] `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` L36-85 · 五轴 panel = 多条 clean 读链并行消费 transform 后段，本票不 fetch
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172-244 · panel smoke 断言无 staged_fixture 来源
- [x] `参考项目/digital-oracle/digital_oracle/providers/fear_greed.py` L50-62 · fail-closed 纪律；情绪轴仍走 COT clean

## S06 决策

- 集成测 `test_layer1_five_axis_panel_clean_smoke.py` 单库种子五轴 P0
- K1 增补 BAA10Y / SPY bar / COT 088691 行（P2 notes，不扩 LAYER1_P0_SERIES 五序列集）
- `ACC-LAYER-E2E-LIVE-001`：**L1 子集关账**；L3-L5 **阶段外置** DCP-07/08/10 + R3H-05-GATE
