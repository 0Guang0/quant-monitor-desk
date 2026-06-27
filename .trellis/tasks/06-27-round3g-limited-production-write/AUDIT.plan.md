# Audit 计划 — R3G-03 Limited Production Clean Write

> **读者：** 主会话 + A1–A8  
> **编排：** `complex-task-planning-protocol.md` Phase 7  
> **索引：** `EXECUTION_INDEX.md` §5

| 字段        | 值                                       |
| ----------- | ---------------------------------------- |
| slug        | `06-27-round3g-limited-production-write` |
| audit.jsonl | 第一条 = 本文件                          |

---

## 0.1 Trace Authority Set

| 类别                | 文件                                                                                                                          | 用途            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 原始任务卡          | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md` | scope / AC      |
| task README         | `docs/implementation_tasks/README.md`                                                                                         | 入口合规        |
| task input index    | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                       | 必读上下文      |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                  | 未闭合项        |
| project map         | `MIGRATION_MAP.md`                                                                                                            | docs/specs 边界 |
| round map           | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                          | batch scope     |
| 执行索引            | `EXECUTION_INDEX.md`                                                                                                          | 血缘 + manifest |
| omission-check      | `research/project-map-omission-check.md`                                                                                      | 地图倒查        |
| integration-ledger  | `research/integration-ledger.md`                                                                                              | context packing |
| R3G-01/02 归档      | `.trellis/tasks/archive/2026-06/06-27-06-27-round3g-*/`                                                                       | 前置证据链      |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                                                     | 环境          | 通过条件       | 已执行 |
| --- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------------- | ------ |
| A1  | 必做   | 对照活卡 §9–§11、§3 reference、BATCH_3G manifest；用户授权≠approval artifact                                                                                                                    | local         | 无 scope 漏/扩 | [ ]    |
| A3  | 必做   | rg `参考项目` import；rg `agent_triggered`；promote 缺 approval CLI 拒绝                                                                                                                        | local         | fail-closed    | [ ]    |
| A4  | 必做   | approval/audit 字段 equality；rollback dry_run 不删非目标 keys                                                                                                                                  | audit-sandbox | 对抗 fixture   | [ ]    |
| A6  | 不用   | **SKIP** — 无 hot path SLA；单次 promote caps ≤10 symbols                                                                                                                                       | —             | —              | [ ]    |
| A7  | 必做   | `qmd data sandbox-clean-write promote --help`；rehearse/audit 仍拒生产写                                                                                                                        | audit-sandbox | CLI 边界正确   | [ ]    |
| A8  | 必做   | `pytest tests/test_round3g_limited_production_clean_write.py tests/test_round3g_limited_production_rollback.py tests/test_reference_adoption_guardrails.py -q --basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿           | [ ]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `gitnexus-audit-summary.md`
- [ ] 派发 A1–A8 → `audit.report.md`
- [ ] PASS / PASS_WITH_FIXES / FAIL
