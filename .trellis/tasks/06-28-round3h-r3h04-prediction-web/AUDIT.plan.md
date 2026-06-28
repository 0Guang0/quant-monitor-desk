# Audit 计划 — R3H-04 Prediction and Web Evidence Adapters

> **读者：** 主会话 + A1–A8  
> **索引：** `EXECUTION_INDEX.md` §5

| 字段        | 值                                      |
| ----------- | --------------------------------------- |
| slug        | `06-28-round3h-r3h04-prediction-web`    |
| audit.jsonl | 第一条 = 本文件                         |

---

## 0.1 Trace Authority Set

| 类别                | 文件                                                                                                                              | 用途            |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 原始任务卡          | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` | scope / AC      |
| task README         | `docs/implementation_tasks/README.md`                                                                                             | 入口合规        |
| task input index    | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                           | 必读上下文      |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                      | 未闭合项        |
| project map         | `MIGRATION_MAP.md`                                                                                                                | docs/specs 边界 |
| round map           | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0                                                                                          | Batch 3H        |
| 执行索引            | `EXECUTION_INDEX.md`                                                                                                              | 血缘 + manifest |
| parallel playbook   | `_tmp-r3h03-r3h04-parallel/BRANCH-R3H-04.md`                                                                                      | 文件边界        |
| omission-check      | `research/project-map-omission-check.md`                                                                                          | 地图倒查        |
| integration-ledger  | `research/integration-ledger.md`                                                                                                  | context packing |
| batch playbook      | `BATCH_3H_COORDINATOR_PLAYBOOK.md`                                                                                                | registry 合并   |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                                                                                    | 环境          | 通过条件       | 已执行 |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------- | -------------- | ------ |
| A1  | 必做   | 对照活卡 §9–§12、三源终态、禁止 clean write、禁止 resolve 事实、**frozen §2.8** 主库/CN 源/ mock-first gates                                                                                                                                                    | local         | 无 scope 漏/扩 | [ ]    |
| A3  | 必做   | rg `参考项目/agents-for-openbb` import；rg `resolved_outcome|factual_resolution`；web_search route 不得 clean writer；**禁止**改 R3H-03 CN port/registry 行                                                                                                            | local         | fail-closed    | [ ]    |
| A4  | 必做   | 三源 cap 溢出 / evidence-only route 负例 / manual_review 绕过负例 / polymarket `resolution_source` 非事实                                                                                                                                                              | audit-sandbox | 对抗 fixture   | [ ]    |
| A5  | 必做   | 对照 `original-plan-trace.md` + §10.1 三源负例；`9.5-manifest.md` 白名单仅 kalshi/polymarket/web_search                                                                                                                                                              | local         | AC 全链覆盖    | [ ]    |
| A6  | 不用   | **SKIP** — 无 hot path SLA；on-demand evidence API                                                                                                                                                                             | —             | —              | [ ]    |
| A7  | 必做   | 无新增写主库 CLI；既有 promote 仍拒 canonical DB                                                                                                                                                                                 | audit-sandbox | CLI 边界       | [ ]    |
| A8  | 必做   | `pytest tests/test_prediction_market_adapters.py tests/test_web_evidence_adapter.py tests/test_no_clean_write_for_web_evidence.py tests/test_r3h_source_final_decisions.py -q -k "kalshi or polymarket or web_search or layer or clean or resolve" --basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿           | [ ]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `research/gitnexus-audit-summary.md`
- [ ] 派发 A1–A8 → `audit.report.md`
- [ ] PASS / PASS_WITH_FIXES / FAIL
