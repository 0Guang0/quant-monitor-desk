# Execute 参考实读证据 — R3-DCP-07（S00–S02）

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp07.md`  
> **worktree 注记：** `参考项目/` 树未检出；行号与语义以 Plan `reference-adoption-dcp07.md` §1–2 + DCP-06 `execute-reference-read-evidence-s00-core.md` / `s03-risk.md` 交叉核对。

## 实读清单

- [x] `参考项目/OpenBB/.../fetcher.py` L36–85 · **architecture_only** → Layer2 只读 DCP-05 clean；不拷贝 Fetcher；不新 fetch
- [x] `参考项目/OpenBB/.../fred_base.py` L31–75 · **L2** · `series_id` ↔ `indicator_id=VIXCLS`；registry `FRED:VIXCLS` 标签映射
- [x] `参考项目/OpenBB/.../series.py` L18–26 · **L2 概念** · symbol ↔ series_id 别名（仓内 `instrument_id` 前缀解析）
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–250 · **forbidden** · DuckDB 空 → 在线回退；`Layer2CleanObservationReader` 空行 → `Layer2CleanObservationReadError`
- [x] `参考项目/EasyXT/.../unified_data_interface.py` L233–237 · **forbidden** · 降级后再下载；clean 缺行不得换源
- [x] `参考项目/TradingAgents-astock/.../quality_gate.py` · **architecture_only** · 多层 quality gate 概念；对齐仓内 `DbValidationGate` + VR 链

## 对照 Plan 决策

- ADR-032 P0 = `L2-VIX` / `VIXCLS` / `axis_observation` / `production_clean_replay`
- DCP-06 S03 先例：`read_macro_clean_observations` + `seed_macro_series` replay 种子可复用
- `reference-adoption-dcp07.md` §3 仓内承接：`sensor_loader` P0 mode · `snapshot_builder` · `lineage` 契约不变

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 silent fallback
- [x] 未修改 DCP-05 forbidden 路径（incremental / migrations / clean_write_targets）
- [x] 未修改 DCP-06 `layer1_axes/**` 所有权文件
