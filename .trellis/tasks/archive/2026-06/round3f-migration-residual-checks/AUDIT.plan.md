# Audit 计划 — B3F-MIG migration residuals

| 字段        | 值                                  |
| ----------- | ----------------------------------- |
| slug        | `round3f-migration-residual-checks` |
| audit.jsonl | 第一条 = 本文件                     |

## 0.1 Trace Authority Set

| 类别               | 文件                                                          | 用途              |
| ------------------ | ------------------------------------------------------------- | ----------------- |
| 协调包             | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §8.1                       | scope / PASS 命令 |
| Roadmap            | `PROJECT_IMPLEMENTATION_ROADMAP.md` R3F-MIG-\*                | AC                |
| source-index       | `research/source-index.md`                                    | 血缘              |
| integration-ledger | `research/integration-ledger.md`                              | packing           |
| adversarial        | `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` B3F-AUD-VS-02 | MIG-01 负向       |

## Audit Source Trace

| 类别      | 路径                                                             | Audit 用途 |
| --------- | ---------------------------------------------------------------- | ---------- |
| MASTER    | `MASTER.plan.md` §2 §5 §9                                        | A5 抽检    |
| diff      | `012_migration_residuals.sql`, `source_registry.py`, schema docs | A1/A4      |
| 测试      | `test_round3f_migration_residuals.py`                            | A8         |
| forbidden | playbook §2.6 source_health_snapshot                             | A7         |

## 1. 验证覆写

| 维  | 本任务                                   | 命令 / 检查                                                                                                                                                  | 通过条件          |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| A3  | 必做                                     | diff 无 production clean write                                                                                                                               | 零写库路径        |
| A6  | **SKIP** — migration/doc 任务无 SLA 热点 | —                                                                                                                                                            | 记录 SKIP         |
| A7  | 必做                                     | 无 `source_health_snapshot` migration；无 registry 三件套 diff                                                                                               | forbidden 零 diff |
| A8  | 必做                                     | `uv run pytest tests/test_round3f_migration_residuals.py tests/test_schema_contract.py tests/test_migration_coverage.py -q --basetemp=.audit-sandbox/pytest` | exit 0            |

## 2. DoD

- [x] A1–A8 报告 + `audit_matrix.json`
- [x] MIG-01 verify-only：无重复 009 CHECK migration（B3F-AUD-VS-02）
- [x] PASS 前不 finish-work
- [x] registry 闭合由 B3F-REG / 主会话验证（非本 Audit 必达）
