# Execute 参考实读证据 — S05 sentiment

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md` · ADR-029 SENTIMENT 锚点

## 实读清单

- [x] `参考项目/digital-oracle/digital_oracle/providers/fear_greed.py` L50–62 · **L2 概念** · `ProviderParseError` fail-closed；**不采纳 CNN 源**；情绪 P0 走 CFTC COT clean
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden** · DuckDB 空 → 在线回退；本切片断言 `source_used=cftc_cot` 且非 `staged_fixture`
- [x] `backend/app/ops/cftc_incremental_run.py` · 仓内承接 · `axis_observation.indicator_id` = market code `088691`；`SOURCE_ID=cftc_cot`；`DATA_DOMAIN=cot_positioning`

## 对照 Plan 决策

- ADR-029：`SEN-S1-COT_LF_NET` ← DB `088691` ← `cftc_cot`
- `P0_MACRO_DB_KEYS` 已在 S00 绑定；本切片只追加 e2e 测
- 周频 COT → `AxisFeatureEngine(frequency="weekly", …)` ponytail 窗口缩小以满足 tmp_path 种子

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 未修改 `clean_observation_reader.py` / migration / incremental
- [x] 无 CNN fear/greed 数据源
