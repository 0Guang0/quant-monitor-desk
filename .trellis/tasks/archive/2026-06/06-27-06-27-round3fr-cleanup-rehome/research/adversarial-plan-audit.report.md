# 对抗性 Plan 审计报告 — R3FR-07

> Agent: 主会话对抗性复核 · 2026-06-27  
> **修复状态：ADV-07-01..18 已闭合**（见 §2）

---

## §1 审计方法

对照以下来源交叉验证：

1. 活任务卡 §2–§3 cleanup targets 与 `BATCH_3FR_COORDINATOR_PLAYBOOK` §2 文件锁
2. 归档 Plan `06-26-round3fr-provider-catalog` / `06-26-round3fr-tdx-provider` 的 §3 manifest 基线
3. `test_reference_adoption_guardrails.py` 下游 16 卡治理 (`_R3FR01_DOWNSTREAM_REL`)
4. `specs/contracts/data_cli_contract.yaml` · `data_quality_rules.yaml` · `docs/ops/data_health_cli.md`
5. `context_pack.json`（当前 modules 为空）
6. `implement.jsonl` 仅 9 行 §3 条目（修复前）

---

## §2 发现与修复

### P0 — Execute 必读 manifest 遗漏（已修复）

| ID        | 缺口                                                                                       | 风险                               | 修复                          |
| --------- | ------------------------------------------------------------------------------------------ | ---------------------------------- | ----------------------------- |
| ADV-07-01 | 缺 `GLOBAL_RESOURCE_LIMITS.md`                                                             | cleanup 误触 live fetch / 无界扫描 | §3 must-read                  |
| ADV-07-02 | 缺 `MIGRATION_MAP.md`                                                                      | docs/specs vs backend 边界误判     | §3 must-read                  |
| ADV-07-03 | 缺 `data_cli_contract.yaml` + `data_health_cli.md`                                         | `health_check` redirect 偏离契约   | §3 must-read                  |
| ADV-07-04 | 缺 `data_quality_rules.yaml` (`ops_cli_profiles`)                                          | profile 名与 CLI 不一致            | §3 must-read                  |
| ADV-07-05 | 缺 `PROJECT_IMPLEMENTATION_ROADMAP` / `ROUND3_HANDOFF` / `ROUND3_BATCH_IMPLEMENTATION_MAP` | 9.5 改错章节或漏改 checkpoint      | §3 must-read                  |
| ADV-07-06 | 缺 `MODULE_COMPLETION_RATING.md`                                                           | provider catalog 评级瞎写          | §3 must-read                  |
| ADV-07-07 | 缺 `docs/implementation_tasks/README.md`                                                   | 执行顺序仍写 3F-R active           | §3 must-read                  |
| ADV-07-08 | 缺双 README（`ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md` + `BATCH_3FR.../README.md`）  | AC-07-01 只测一处                  | §3 + 扩展测试名               |
| ADV-07-09 | 缺 `BATCH_3FR_COORDINATOR_PLAYBOOK`（文件锁）                                              | 并行误改共享文件                   | §3 must-read；§4 移除错误内联 |
| ADV-07-10 | 缺 `BATCH_3FR_TASK_CARD_MANIFEST` / `BATCH_3G_TASK_CARD_MANIFEST`                          | manifest DONE 行漏改               | §3 must-read                  |
| ADV-07-11 | 缺 `BATCH_3G_COORDINATOR_PLAYBOOK.md`                                                      | 3G 仍写 blocked 未同步             | §3 + 9.5 允许文件             |
| ADV-07-12 | 缺 `UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                      | Execute 误关 B2.5-O-05 等          | §3 execute-required           |
| ADV-07-13 | 缺 `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`                                          | 与 guardrails「地图不是工单」冲突  | §3 must-read                  |
| ADV-07-14 | 缺归档 execute-evidence-summary（02/03/05）                                                | 「replacement stronger」无据可依   | §3 execute-required           |
| ADV-07-15 | 缺 `research/integration-ledger.md`                                                        | 允许/禁止文件漂移                  | §3 execute-required           |

### P1 — AC / 步骤 / 回归缺口（已修复）

| ID        | 缺口                                                        | 修复                                             |
| --------- | ----------------------------------------------------------- | ------------------------------------------------ |
| ADV-07-16 | AC-07-01 仅覆盖 parent README §3                            | 增 AC-07-07/08 + 多文件静态测试                  |
| ADV-07-17 | 9.0 未回归 `test_provider_catalog.py`                       | §1 Step 9.0 加入                                 |
| ADV-07-18 | 9.5 未列 `ROUND3_BATCH_IMPLEMENTATION_MAP` checkpoint       | AC-07-07 + 9.5 测试                              |
| ADV-07-19 | 9.6 未强制 `test_r3fr01DownstreamCardsGovernanceBoundaries` | 9.6 guardrails 全文件                            |
| ADV-07-20 | 9.2 未写 GitNexus `impact(check_daily_bars)`                | frozen §9.2 + §1 注记                            |
| ADV-07-21 | `loop_maintain --fix` 仅 Tier C 提及                        | 9.6 RED 含 `--fix`（新测登记）                   |
| ADV-07-22 | `context_pack.json` 空 modules                              | §6 注记：以 §3 manifest 为准；Boot 可复跑 router |

### P2 — Audit 追溯缺口（已修复）

| ID        | 修复                                                            |
| --------- | --------------------------------------------------------------- |
| ADV-07-23 | 新增 `research/project-map-omission-check.md`                   |
| ADV-07-24 | `AUDIT.plan.md` A3 扩 3 条 stale-doc rg + downstream governance |
| ADV-07-25 | `AUDIT.plan.md` §0.1 补 omission-check + integration-ledger     |

### P3 — 已知残留（不阻塞 Plan PASS）

| ID        | 说明                                       | 处置                                   |
| --------- | ------------------------------------------ | -------------------------------------- |
| ADV-07-R1 | Trellis 目录名 `06-27-06-27-*` 双日期      | 不 rename；路径写入 §0                 |
| ADV-07-R2 | `context_router` 未映射本任务 backend 模块 | Execute Boot 复跑；靠 §3 手工 manifest |
| ADV-07-R3 | 历史卡 `R3FR_06` 正文仍含 placeholder 措辞 | 9.1 加 redirect 头注，不删正文（证据） |

---

## §3 闭合判定

**Plan 对抗性审计：PASS（修复后）**

- §3 manifest：15 条 must-read / execute-required（修复前 5 条）
- AC：07-01..08（新增 07-07/08）
- 下游 16 卡：9.6 全量 guardrails 回归防 3G 文案破坏治理

用户审阅 `PLAN_REVIEW.md` 后批准 → `task.py start`。
