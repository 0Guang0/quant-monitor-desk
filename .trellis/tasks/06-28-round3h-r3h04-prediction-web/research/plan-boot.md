# Plan Boot — R3H-04 Prediction and Web Evidence Adapters

> **Phase P0 complete** · 2026-06-28

## 批次定位

| 项 | 值 |
| --- | --- |
| Batch | `ROUND_3_REAL_DATA_PRODUCTION_ENTRY` / Batch 3H |
| Task ID | `R3H-04` |
| Trellis slug | `06-28-round3h-r3h04-prediction-web` |
| 分支 | `feature/round3h-r3h04-prediction-web` |
| Worktree | `../quant-monitor-desk-wt-r3h04` |
| 协议 | v4 (`plan_protocol_version: "4"`) |
| 并行轨 | R3H-03（CN market）；**禁止**交叉改对方 source 行 |
| 前置 | R3H-01/02 CLOSED；R3H-03 并行中 |
| 禁止提前 | R3H-05；主库 `quant_monitor.duckdb` 写入 |

## 已读 P0 输入

| # | 文件 | 摘要 |
| --- | --- | --- |
| 1 | `agent-toolchain.md` | GitNexus impact/query；Plan→freeze→Execute |
| 2 | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0 | R3H-03~04 并行；R3H-04 建议先 merge |
| 3 | `docs/implementation_tasks/README.md` | Round 3H 执行入口 |
| 4 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | 历史索引；3H 权威见 Batch README |
| 5 | `BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md` | 全目标 source 须 READY 或 ADR |
| 6 | `BATCH_3H_TASK_CARD_MANIFEST.md` | R3H-04 拥有 kalshi/polymarket/web_search |
| 7 | `BATCH_3H_COORDINATOR_PLAYBOOK.md` | 并行 ownership + registry 合并 |
| 8 | `BATCH_3H_HARDENING_RULES.md` | 预测=概率；web=evidence only |
| 9 | `R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` | 活任务卡（3 source） |
| 10 | `GLOBAL_EXECUTION_RULES.md` | scope / 禁止 silent expand |
| 11 | `GLOBAL_TESTING_POLICY.md` | TDD + 五字段注释 |
| 12 | `GLOBAL_RESOURCE_LIMITS.md` | ResourceGuard / caps |
| 13 | `GLOBAL_TASK_TEMPLATE.md` | §9 步骤结构 |
| 14 | `BRANCH-R3H-04.md` | 文件边界与拥有源 |
| 15 | `.cursor/skills/trellis-plan/SKILL.md` | v4 冻结三件套 |

## 首切片问题（三源 baseline）

**问题：** 三源在 registry/capabilities 有定义，但 **无** fetch port、**无** `probability_signal` normalizer、**无** `manual_review_staging`、capabilities 仍为 `proposed_disabled_source`；测试文件尚未存在。

**R3H-04 目标：** mock/replay-first fetch port → probability/web evidence normalizer → evidence-only route → registry 三源终态；**零** clean factual table 写入路径。

## 任务边界（一句话）

将 `kalshi`、`polymarket`、`web_search` 从 proposed-disabled 推进到 `READY_WITH_EVIDENCE`（mock/replay 可执行证据路径）或 `ADR_DISABLED_OUT_OF_SCOPE`；预测市场仅概率信号，网页证据仅 manual-review staging。

## 明确不做

- 写 `data/duckdb/quant_monitor.duckdb`
- 运行时 import / 拷贝 `参考项目/agents-for-openbb/**` agent 运行时
- 修改 R3H-03 拥有的 CN market port 或 registry 行
- 用预测价格解析/确认事实事件结果
- web_search clean-table 写入
- R3H-05 全层审计
- 改 `backend/app/core/resource_guard.py`（BRANCH 未授权；端口内 cap）

## GitNexus（Plan 1a/1b）

- `query("prediction market evidence fetch port manual review")` — 命中 `DataSourceService`、layer5 foundation、`evidence_bundle` 模式
- **风险预判：** MEDIUM — 触及 route/capabilities/registry 共享文件 + 新 evidence 路径

## context_pack

```bash
uv run python scripts/context_router.py --task .trellis/tasks/06-28-round3h-r3h04-prediction-web
```

## Phase 3（grill-me）

- 产出：`research/grill-me-session.md`（**Phase 3 complete**）
- 活卡加固：`R3H_04_*.md` §7–§15
- 追溯：`research/original-plan-trace.md`
