# Execute 参考实读证据 — S00 core

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md`

## 实读清单

- [x] `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` L36–85 · architecture_only → **不拷贝**；clean read = 流水线后端，本切片不 fetch
- [x] `参考项目/OpenBB/openbb_platform/providers/fred/openbb_fred/utils/fred_base.py` L31–75 · **L2** · DB `indicator_id` = series_id（DGS10）与 spec ENV-E1-DGS10 分离 → `P0_MACRO_DB_KEYS` 映射
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden** · `read_macro_clean_observations` 空结果 → `CleanObservationReadError`，无在线回退
- [x] `参考项目/digital-oracle/digital_oracle/providers/fear_greed.py` L50–62 · **L2 概念** · parse fail-closed；本切片不采纳 CNN 源

## 对照 Plan 决策

- ADR-029 P0 锚点 → `P0_MACRO_DB_KEYS` / `P0_BAR_BINDING`
- `reference-adoption-dcp06.md` §3 仓内 `insert_axis_observation` 复用

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未修改 staged ingestion 默认路径
