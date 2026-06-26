# Audit 计划 — R3FR-07 Legacy Wrapper Cleanup

> **读者：** 主会话 + A1–A8  
> **slug:** `06-27-round3fr-cleanup-rehome`  
> **对抗性 Plan 审计：** `research/adversarial-plan-audit.report.md`（2026-06-27 PASS）

| 字段        | 值              |
| ----------- | --------------- |
| audit.jsonl | 第一条 = 本文件 |

---

## 0.1 Trace Authority Set

| 类别                | 文件                                                                                                                                                  |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 原始任务卡          | `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` |
| frozen SSOT         | `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md`                                                                                              |
| EXECUTION_INDEX     | `EXECUTION_INDEX.md`                                                                                                                                  |
| adversarial plan    | `research/adversarial-plan-audit.report.md`                                                                                                           |
| omission-check      | `research/project-map-omission-check.md`                                                                                                              |
| task README         | `docs/implementation_tasks/README.md`                                                                                                                 |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                          |
| project map         | `MIGRATION_MAP.md`                                                                                                                                    |
| round map           | `PROJECT_IMPLEMENTATION_ROADMAP.md` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                            |
| handoff             | `docs/ROUND3_HANDOFF.md`                                                                                                                              |
| integration-ledger  | `research/integration-ledger.md`                                                                                                                      |
| replacement 证据    | 归档 R3FR-02/03/05 `execute-evidence-summary.md`（三份）                                                                                              |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                           | 环境          | 通过条件         | 已执行 |
| --- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------- | ------ |
| A1  | 必做   | `EXECUTION_INDEX` §3 行数 ≥ 20；`implement.jsonl` 与 §3 一致                                                                                                          | local         | 无 manifest 遗漏 | [ ]    |
| A3  | 必做   | `rg "still returns.*not_implemented" docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md` → 0                                                     | local         | 无 stale 声称    | [ ]    |
| A3  | 必做   | `rg "Blocked by.*3F-R" docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md` → 0 或仅历史脚注                                 | local         | 3G 可入口        | [ ]    |
| A3  | 必做   | `pytest tests/test_reference_adoption_guardrails.py::test_r3fr01DownstreamCardsGovernanceBoundaries -q`                                                               | local         | 16 卡治理仍绿    | [ ]    |
| A6  | SKIP   | cleanup 无 perf 契约变更                                                                                                                                              | —             | —                | [ ]    |
| A7  | SKIP   | 无 init/migrate CLI 行为变更                                                                                                                                          | —             | —                | [ ]    |
| A8  | 必做   | `pytest tests/test_r3fr07_legacy_wrapper_cleanup.py tests/test_reference_adoption_guardrails.py tests/test_provider_catalog.py -q` `--basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿             | [ ]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `gitnexus-audit-summary.md`
- [ ] A1 核对 §3 manifest 与 `project-map-omission-check.md`
- [ ] A3 stale-doc rg + downstream governance
- [ ] A8 补测全绿 → `audit.report.md`
- [ ] PASS 前禁止 `finish-work`；禁止 production-live 声明
