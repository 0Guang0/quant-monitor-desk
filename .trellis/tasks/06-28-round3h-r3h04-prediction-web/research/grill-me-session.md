# Grill-me Session — R3H-04

> **Phase 3 complete** · 2026-06-28

## Q&A 记录

| # | 问题 | 回答 / 决定 | 落点 |
| --- | --- | --- | --- |
| Q1 | 预测市场能否写 clean 表？ | **否** — hardening §4；负例测试必须存在 | frozen §8 / §10 |
| Q2 | mock/replay 能否算 READY？ | **是** — 对齐 R3H-01/02；replay fixture + route + evidence | frozen §1.1 |
| Q3 | kalshi/polymarket live API 是否本卡必须？ | **否（默认）** — mock-first；live 须用户显式 gate + API key | frozen §2.8 |
| Q4 | web_search 用哪个搜索后端？ | **待定 → 默认 mock stub**（见未决 #1） | §9.4 |
| Q5 | 能否从预测价格推断事件已发生？ | **禁止** — 无 `resolved_outcome` / factual 字段 | frozen §8 |
| Q6 | web_search 能否跳过 manual review？ | **禁止** — `need_human_review=true` | frozen §8 |
| Q7 | 能否改 CN market registry？ | **禁止** — R3H-03 拥有 | BRANCH |
| Q8 | OpenBB agent 参考边界？ | 仅 bounded artifact 形状；禁止 runtime | frozen §14 |
| Q9 | ADR 何时允许？ | API/terms 真受阻；须 `docs/adr/` + registry ADR_DISABLED | frozen §8.1 |
| Q10 | resource_guard 是否必改？ | **否** — BRANCH 未授权；端口内 cap | frozen §7 |
| Q11 | 合并顺序？ | R3H-04 建议先于 R3H-03（源少） | COORDINATOR |
| Q12 | Layer 范围？ | L5 smoke only；非 R3H-05 | §9.7 |

## 采纳的默认（无用户反对前 Execute 可执行）

1. 三源均 mock/replay-first `READY_WITH_EVIDENCE`
2. `web_search` 使用 deterministic mock 搜索结果（非网络）
3. 端口 cap 见活卡 §7

## 须用户确认（Grill-me 未闭合）

见 `plan.freeze.md` §2 未决清单 #1（web_search 真实搜索 API 需求）
