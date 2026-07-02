# Execute 参考实读证据 — S03 RISK_APPETITE

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md`

## 实读清单

- [x] `参考项目/OpenBB/openbb_platform/providers/fred/openbb_fred/utils/fred_base.py` L31–75 · **L2** · `get_series(series_id, start_date, end_date)` 窗参数；DB `indicator_id` = FRED series_id（VIXCLS）与 spec `RA.R1.VIXCLS_30D_IMPLIED_VOL` 分离 → S00 `P0_MACRO_DB_KEYS` 映射已承接
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden** · DuckDB 空 → `need_download=True` 在线回退；Layer1 clean e2e 须断言 `source_used=fred` 且非 `staged_fixture`，clean 不足 → fail-closed（S00 `CleanObservationReadError`）

## 对照 Plan 决策

- ADR-029 P0 锚点 RISK_APPETITE → `RA.R1.VIXCLS_30D_IMPLIED_VOL` ← `axis_observation` VIXCLS / fred
- `reference-adoption-dcp06.md` §3 仓内 `seed_macro_series` + `read_macro_clean_observations` 复用
- 情绪/宏观 fetch 已由 DCP-05 闭合；本切片 **只读 clean + feature + interpretation**

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未修改 `clean_observation_reader.py`（S00 基线）
