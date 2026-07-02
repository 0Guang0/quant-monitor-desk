# Execute 参考实读证据 — S07 repair

> RED 前实读 · S07 K2/K1/A4/L1 关账切片

## 参考项目目录

- **`参考项目/` 缺失**（workspace glob 0 hits；S00 证据引用路径不可在本 worktree 复读）
- **交叉引用：** `research/reference-adoption-dcp06.md` §1–§3 + `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md`
- **缺口说明：** 本 repair 不新增 fetch；caps/interpretation 对齐仓内 `AxisFeatureEngine` / `ResourceGuard` 既有模式

## 采纳对照（S07 触点）

| 触点               | 参考/ADR                                       | S07 决策                                                       |
| ------------------ | ---------------------------------------------- | -------------------------------------------------------------- |
| K2 FR-4 流动性解读 | ADR-029 §2 LIQUIDITY                           | 与 macro 轴同链：`AxisInterpretationEngine` after feature      |
| K1 FR-6 readiness  | ADR-029 §Consequences                          | P0 五轴绑定行 → `clean_replay_proven`（非 production-live）    |
| A4 FR-5 caps       | `reference-adoption-dcp06.md` §3 ResourceGuard | `P0_ROW_CAPS` + 真 `ResourceGuard(con).check()` on migrated DB |
| L1 ledger          | `plan-doubt-review.md` Q4                      | L1 子集关账；L3–L5 阶段外置                                    |

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 未改 forbidden DEBT files（registry / migrations / data_commands / clean_write_targets）
- [x] 未削弱 B01-FRED sandbox_candidate 测试目的（T10Y3M/SP500/DFII10 仍 sandbox）
