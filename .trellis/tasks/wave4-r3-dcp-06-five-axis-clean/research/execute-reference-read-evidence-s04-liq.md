# Execute 参考实读证据 — S04 liquidity

> RED 前实读 `参考项目/**` · 对照 `reference-adoption-dcp06.md` · ADR-029 ponytail

## 实读清单

- [x] `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` L36–85 · **architecture_only** → clean read = OpenBB 流水线末段（`transform_data` 之后）；S04 **不 fetch**，只读 `security_bar_1d` Tier A clean
- [x] `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244 · **forbidden** → DuckDB 无 bar 行时 **禁止** silent 换源；`read_bar_history` 空 → `CleanObservationReadError`

> ponytail: 本机 `参考项目/**` 目录未检出；上表依据 Plan `reference-adoption-dcp06.md` §1–2 冻结决策对照，**无 runtime import**。

## ADR-029 流动性 ponytail

| 项           | S04 决策                                                                        |
| ------------ | ------------------------------------------------------------------------------- |
| Spec primary | `tiingo_eod_composite_or_fmp_eod_with_volume_gate`（**非 Tier A**）             |
| DCP-06 锚点  | `LIQ.B-I1.AMIHUD_ILLIQ` from `security_bar_1d` SPY · `alpha_vantage`            |
| 升级路径     | tiingo/FMP port 注册 + volume gate 校验后替换 bar 源（Batch 6+）；见 ADR-029 §3 |

## 对照 Plan 决策

- `seed_spy_bars` → `read_bar_history` + `amihud_observations_from_bars` → `AxisFeatureEngine` → `AxisInterpretationEngine`
- `source_used=alpha_vantage`；**非** `staged_fixture`

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未修改 `clean_observation_reader.py` / migration / incremental
