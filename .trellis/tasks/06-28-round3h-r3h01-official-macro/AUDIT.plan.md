# Audit 计划 — R3H-01 Official Macro Disclosure Adapters

> **读者：** 主会话 + A1–A8  
> **索引：** `EXECUTION_INDEX.md` §5

| 字段        | 值                                   |
| ----------- | ------------------------------------ |
| slug        | `06-28-round3h-r3h01-official-macro` |
| audit.jsonl | 第一条 = 本文件                      |

---

## 0.1 Trace Authority Set

| 类别                | 文件                                                                                                                                            | 用途            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 原始任务卡          | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` | scope / AC      |
| task README         | `docs/implementation_tasks/README.md`                                                                                                           | 入口合规        |
| task input index    | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                                         | 必读上下文      |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                    | G10 等          |
| project map         | `MIGRATION_MAP.md`                                                                                                                              | docs/specs 边界 |
| round map           | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5                                                                                                          | Batch 3H        |
| 执行索引            | `EXECUTION_INDEX.md`                                                                                                                            | 血缘 + manifest |
| 3G gaps             | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`                            | G10/G14         |
| omission-check      | `research/project-map-omission-check.md`                                                                                                        | 地图倒查        |
| integration-ledger  | `research/integration-ledger.md`                                                                                                                | context packing |
| batch playbook      | `BATCH_3H_COORDINATOR_PLAYBOOK.md`                                                                                                              | registry 合并   |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                                                                                                | 环境          | 通过条件       | 已执行 |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------- | -------------- | ------ |
| A1  | 必做   | 对照活卡 §9–§12、六源终态、§2.8 主库禁止                                                                                                                                                                                                   | local         | 无 scope 漏/扩 | [ ]    |
| A3  | 必做   | rg `参考项目` import；rg `live_evidence_bridge._write_sandbox` 生产路径；SEC 无 User-Agent 拒绝                                                                                                                                            | local         | fail-closed    | [ ]    |
| A4  | 必做   | FRED 未授权 / cap 溢出 / route DISABLED 负例                                                                                                                                                                                               | audit-sandbox | 对抗 fixture   | [ ]    |
| A6  | 不用   | **SKIP** — 无 hot path SLA；低频官方 API                                                                                                                                                                                                   | —             | —              | [ ]    |
| A7  | 必做   | 无新增写主库 CLI；既有 `sandbox-clean-write promote` 仍拒 canonical DB                                                                                                                                                                     | audit-sandbox | CLI 边界       | [ ]    |
| A8  | 必做   | `pytest tests/test_official_macro_adapters.py tests/test_sec_edgar_adapter.py tests/test_source_route_planner.py -q -k "fred or treasury or sec_edgar or cftc or bis or world_bank or evidence or layer" --basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿           | [ ]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `research/gitnexus-audit-summary.md`
- [ ] 派发 A1–A8 → `audit.report.md`
- [ ] PASS / PASS_WITH_FIXES / FAIL
