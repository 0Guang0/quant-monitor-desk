# Execute 参考实读证据 — S02 CREDIT_STRESS

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md` · ADR-029 P0 `CRD.CS1.BAA10Y`

## 实读清单

- [x] `参考项目/OpenBB/.../fred_base.py` L31–75 · **L2**（本 worktree 无参考树；与 S00 交叉核对 `reference-adoption-dcp06.md` §2.2）
  - `get_series(series_id, start_date, end_date)` 窗参数；DB `indicator_id` = FRED series code `BAA10Y`
  - QMD：`P0_MACRO_DB_KEYS["CRD.CS1.BAA10Y"] = "BAA10Y"`；Layer1 **只读** `axis_observation`，不重复 fetch
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden**
  - DuckDB 空 → `need_download = True` → 在线 QMT 回退（L172–244）
  - L233–237：`_read_from_duckdb` 失败后再下载
  - QMD 负向对齐：clean 缺行 → `CleanObservationReadError`；本切片 e2e 断言 `source_used==fred` 且非 `staged_fixture`
- [x] `specs/.../credit_stress_axis_indicator_spec.yaml` · 仓内 SSOT
  - P0 `CRD.CS1.BAA10Y` · `primary_source: FRED:BAA10Y` · `forbidden_substitutes: FRED:BAA absolute yield`

## S02 切片决策

| 项            | 决策                                                                               |
| ------------- | ---------------------------------------------------------------------------------- |
| spec → DB     | `CRD.CS1.BAA10Y` ← `axis_observation.indicator_id = BAA10Y`                        |
| tier_a_source | `fred`（DCP-05 replay seed via `seed_macro_series`）                               |
| 链路          | `read_macro_clean_observations` → `AxisFeatureEngine` → `AxisInterpretationEngine` |
| 禁止          | 修改 `clean_observation_reader.py`（S00 独占）；EasyXT 式 silent fallback          |

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未改 `clean_observation_reader.py` / migration / sync registry
