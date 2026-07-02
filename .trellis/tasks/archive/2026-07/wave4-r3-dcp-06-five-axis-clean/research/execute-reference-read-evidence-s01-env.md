# Execute 参考实读证据 — S01 ENVIRONMENT

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md` · S01 ENV-E1-DGS10 e2e

## 实读清单

- [x] `参考项目/OpenBB/openbb_platform/providers/fred/openbb_fred/utils/fred_base.py` L31–75 · **L2**
  - **L31–45** `get_series(series_id, start_date, end_date)`：FRED 以 `series_id`（如 DGS10）为键拉窗内观测；Layer1 **不重复 fetch**，只消费 DCP-05 已写入 `axis_observation.indicator_id=DGS10` 的 clean 行。
  - **L46–75** 响应解析为时间序列；QMD 等价物为 `read_macro_clean_observations` 将 DB 行映射回 spec `ENV-E1-DGS10`（`P0_MACRO_DB_KEYS`）。
  - **worktree 注记：** `参考项目/` 树未检出；行号与语义以 Plan `reference-adoption-dcp06.md` §2.2 + S00 `execute-reference-read-evidence-s00-core.md` 交叉核对。
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden**
  - **L172–200** DuckDB 查询为空时设置 `need_download` / 在线回退标志。
  - **L233–244** `_read_from_duckdb` 失败后走下载路径 — **禁止** Layer1 模仿。
  - S01 e2e 断言 `source_used=fred` 且非 `staged_fixture`；空 clean 由 S00 `CleanObservationReadError` fail-closed（本切片不测空库，不测 fallback）。

## 对照 Plan / ADR-029

| 锚点        | clean 表         | DB key | tier_a source | S01 验证                  |
| ----------- | ---------------- | ------ | ------------- | ------------------------- |
| ENVIRONMENT | axis_observation | DGS10  | fred          | `ENV-E1-DGS10` e2e replay |

## 仓内复用（非参考 L 梯）

- `tests/layer1_clean_e2e_support.py`：`bootstrap_layer1_clean_db` · `seed_macro_series` · `AS_OF`
- `tests/test_layer1_interpretation.py`：`AxisFeatureEngine` / `AxisInterpretationEngine` 调用形态
- `read_macro_clean_observations` → `compute_features` → `build_interpretation` 垂直链

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 silent fallback
- [x] 未修改 `clean_observation_reader.py`（S00 已 merge @ 1c683397）

## GitNexus impact（编码前）

- `read_macro_clean_observations`：索引未收录（S00 新符号）· 本切片仅测试调用 · 风险可忽略
- `AxisFeatureEngine.compute_features`：upstream LOW · 1 direct · Layer1_axes · 本切片只读调用
