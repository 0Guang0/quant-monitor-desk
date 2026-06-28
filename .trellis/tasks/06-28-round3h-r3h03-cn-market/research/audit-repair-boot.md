# Audit Repair Boot — R3H-03（零遗留）

**日期：** 2026-06-28 · **Repair agent：** trellis-implement (composer-2.5)

## 修复前理解清单

| 项 | 回答 |
| --- | --- |
| **目标** | R3H-03 十源 CN market adapters 达到 `READY_WITH_EVIDENCE`；Repair 闭合八维 A1–A8 全部发现，审计 PASS、零遗留 |
| **价值** | 未闭合项会阻塞 Round4 生产入口决策、主会话 P6 commit/archive、以及与 R3H-04 并行合并 |
| **完成条件** | BLOCKING=0、NON-BLOCKING=0、P0–P3 全 CLOSED；`audit.report.md` PASS；`validate-execute-handoff` 通过；`uv run pytest -q` exit 0 |
| **边界** | 仅修 audit 发现；十源 registry/port；不改 R3H-04 三源；不削弱测试目的 |
| **架构** | cap/route → port + `reject_over_cap`；auth → `license_gate` + `route_planner._platform_allows`；Layer3 → `cn_market_bundle_layer3_preview`；ponytail 去重 → `cn_validation_mock` / `qmt_mock_common` / `tdx_fetch_guards` |
| **完成程度** | 十源仍满足 frozen §11；Q8 mootdx/xqshare 已实现；Q12 G2/G17 日历本卡闭合；Q13 cninfo PDF live capped |
| **修复范围** | 合并去重 **38** 项（P0:0 P1:2 P2:3 P3:3 BLOCKING:0 NON-BLOCKING:2 A8-G:9 A2:4 A6-NB:1 A7:1） |

## 用户 Grill-me（已确认，Repair 不重复询问）

- Q8: mootdx/xqshare 先实现（无 ADR）
- Q12: 本卡完整闭合 G2/G17 交易日历
- Q13: cninfo PDF live capped

## implement.jsonl

已读条数 / 总条数：与 frozen + EXECUTION_INDEX + context_pack + audit.jsonl 对齐（Repair boot 完成）。
