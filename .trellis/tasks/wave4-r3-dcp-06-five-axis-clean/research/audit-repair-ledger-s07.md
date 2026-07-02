# Audit Repair Ledger — S07 (DCP-06 doubt review gaps)

> Source: S07-REPAIR task table + `plan-doubt-review.md` + S06 Audit doubt pass  
> Disposition: **已修复** | **阶段外置** only for L3–L5 full chain

| #   | 原文定位                                                     | 标签         | disposition  | 证据                                                                                  |
| --- | ------------------------------------------------------------ | ------------ | ------------ | ------------------------------------------------------------------------------------- |
| 1   | K2/FR-4: S06 panel 流动性轴跳过 `AxisInterpretationEngine`   | BLOCKING     | **已修复**   | `test_layer1_five_axis_panel_clean_smoke.py` LIQ `liq_interp.boundary_reminder`       |
| 2   | K1/FR-6: P0 行仍 `sandbox_candidate`                         | BLOCKING     | **已修复**   | `layer1_source_whitelist.yaml` DGS10/BAA10Y/VIXCLS/SPY/088691 → `clean_replay_proven` |
| 3   | K1/FR-6: matrix 缺 DCP-06 行与 legend                        | BLOCKING     | **已修复**   | `model_input_readiness_matrix.md` legend + 5 proven rows                              |
| 4   | K1: 缺 `clean_replay_proven` 专用测试                        | BLOCKING     | **已修复**   | `test_layer1_p0_dcp06_cleanReplayProven`                                              |
| 5   | A4/FR-5: 仅 MagicMock ResourceGuard                          | BLOCKING     | **已修复**   | `test_layer1FiveAxisPanel_resourceGuardOnMigratedDb` 真 `ResourceGuard(con).check()`  |
| 6   | A4/FR-5: reader 无 whitelist `row_cap` 证明                  | BLOCKING     | **已修复**   | `P0_ROW_CAPS` + `test_layer1CleanReader_macroRespectsWhitelistRowCap` / bar cap test  |
| 7   | A4/FR-5: `window_len` 无 whitelist `window_cap` 对齐         | NON-BLOCKING | **已修复**   | `P0_WINDOW_CAPS` + `test_layer1FiveAxisPanel_windowLenWithinWhitelistCap`             |
| 8   | L1: `R3_DCP_TO_ISSUES_INDEX.md` §6.2 写 L1–5 full live       | BLOCKING     | **已修复**   | §6.2 → L1 ✅ partial + L3–L5 open                                                     |
| 9   | L1: `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 DCP-06 行误导 | BLOCKING     | **已修复**   | 行改为「L1 五轴 clean replay 子集」                                                   |
| 10  | L1: `MODULE_COMPLETION_RATING` K1/A4 证据滞后                | NON-BLOCKING | **已修复**   | K1 R3→R4 + A4 DCP-06 cap evidence 行                                                  |
| 11  | Doubt Q4: ACC-LAYER L3–L5 假全关风险                         | BLOCKING     | **阶段外置** | `待修复清单.md` ACC-LAYER-E2E-LIVE-001 L3–L5 → DCP-07/08/10 + R3H-05-GATE             |
| 12  | Doubt Q2: tiingo 流动性主路径未就绪                          | NON-BLOCKING | **阶段外置** | ADR-029 ponytail；Batch 6+ tiingo reconcile                                           |
| 13  | Doubt Q1/Q5: live 真网非关账必须 / 参考项目实读              | NON-BLOCKING | **已修复**   | replay clean e2e 政策维持；`execute-reference-read-evidence-s07-repair.md` 交叉引用   |

## 关账核对

- [x] 源表 13 项均有 disposition
- [x] 无「待修复」残留（本票 Repair 范围）
- [x] 阶段外置项已绑定 DCP-07/08/10 + R3H-05-GATE / Batch 6+
- [x] `uv run pytest -q` — 见 `execute-evidence/s07-green.txt`
