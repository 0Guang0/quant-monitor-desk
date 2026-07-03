# R3-DCP-08 Plan Boot

> **Phase P0 complete** · 2026-07-02 · worktree `quant-monitor-desk-wt-dcp08` · branch `feature/wave4-r3-dcp-08-layer4`

## 活卡 §1–§3 摘要（Wave 级 · 不迁入 research 全文）

| 维度          | 内容                                                                                                                                     |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal**      | Layer4 **一个** P0 `market_id` 从 Tier A clean + 真日历读入 → market structure snapshot → pytest 绿                                      |
| **价值**      | Wave 4 G4 最小竖切；承接 `ACC-EASTMONEY-TAXONOMY-001`（部分）、`ACC-MOOTDX-DRYRUN-ROUTE-001`、`ACC-LAYER-E2E-LIVE-001` L4 子集           |
| **约束**      | 输入 SSOT = Tier A clean + `TradingCalendar`（R3H-07 US）；禁止 staged 冒充 PASS；**不关** `R3-B2.75-REQ2-EM`；registry 改动主会话 merge |
| **前置**      | R3H-07 ✅ · R3-DCP-05 ✅ · R3-DCP-06 ✅                                                                                                  |
| **Plan 定案** | P0 `market_id` = **`US_EQ`**（见 `plan-doubt-review.md` Cycle 1 · ADR-033）                                                              |

## P0 必读完成

- [x] `agent-toolchain.md` + `trellis-plan` SKILL + `plan-skill-paths.yaml`
- [x] 活卡 `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` §1–§7
- [x] `docs/modules/layer4_market_structure.md` · `backend/app/layer4_markets/` · `tests/test_layer4_market_structure.py`
- [x] R3H-07 trace：`us_trading_calendar.py` · `market_structure.py` US_EQ 分支
- [x] 台账 §4：`ACC-EASTMONEY-TAXONOMY-001` · `ACC-MOOTDX-DRYRUN-ROUTE-001` · `ACC-LAYER-E2E-LIVE-001` L4
- [x] DCP-05/06 仓内模式 trace（不进 L 梯）

## 下一步

Phase 1a/1b GitNexus → trellis-research → 3.5 to-issues → 5a–5c' → 5e 打包 → `validate-plan-freeze`
