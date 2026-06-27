# Audit 计划 — R3G-01 Sandbox Clean-Write Rehearsal

追溯：`EXECUTION_INDEX.md` §2 + §5 + `research/plan-adversarial-audit-closure.md`

| 字段        | 值                                      |
| ----------- | --------------------------------------- |
| slug        | `06-27-06-27-round3g-sandbox-rehearsal` |
| audit.jsonl | 第一条 = 本文件                         |

## 0.1 Trace Authority Set

| 类别                     | 文件                                                    |
| ------------------------ | ------------------------------------------------------- |
| 活任务卡 / frozen        | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`               |
| 索引                     | `EXECUTION_INDEX.md`                                    |
| 契约                     | `specs/contracts/sandbox_clean_write_contract.yaml`     |
| guardrails               | `specs/contracts/reference_adoption_guardrails.yaml`    |
| integration-ledger       | `research/integration-ledger.md`                        |
| round map                | `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                    |
| project map              | `docs/generated/project_map.generated.json`             |
| playbook                 | `BATCH_3G_COORDINATOR_PLAYBOOK.md`                      |
| TASK_INPUT_CONTEXT_INDEX | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md` |

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                                                                                                       | 环境          | 通过条件          |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ----------------- |
| A3  | 必做   | `rg "参考项目" backend/app/ops/sandbox_clean_write backend/app/cli/data_commands.py` + guardrails 测试                                                                                                                                            | local         | 无 runtime import |
| A6  | 不用   | SKIP — 无 perf SLA；sandbox 排练非 hot path                                                                                                                                                                                                       | —             | —                 |
| A7  | 必做   | `qmd data sandbox-clean-write rehearse --help`；缺 `--no-production-mutation` 须失败                                                                                                                                                              | audit-sandbox | fail-closed       |
| A8  | 必做   | `uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py tests/test_round3g_sandbox_rehearsal_loader.py tests/test_round3g_sandbox_rehearsal_report.py tests/test_reference_adoption_guardrails.py -q --basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿              |

## 2. DoD

- [ ] 7.pre → `gitnexus-audit-summary.md`
- [ ] A1–A8 派发 → `audit.report.md`
- [ ] PASS 前确认：无生产 mutation；FRED artifact 路径在报告中可追溯
- [ ] R3G-03 范围未提前打开
