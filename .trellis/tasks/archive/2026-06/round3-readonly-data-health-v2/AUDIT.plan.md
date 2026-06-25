# Audit 计划 — B01-DH2 Data Health v2

| 字段        | 值                               |
| ----------- | -------------------------------- |
| slug        | `round3-readonly-data-health-v2` |
| audit.jsonl | 第一条 = 本文件                  |

## 0.1 Trace Authority Set

| 类别               | 文件                                                                                         | 用途       |
| ------------------ | -------------------------------------------------------------------------------------------- | ---------- |
| 原始任务卡         | `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md` | scope / AC |
| legacy             | `R3Y_readonly_data_health_v1.md`                                                             | v1 边界    |
| Batch              | `BATCH_01_HARDENING_RULES.md`                                                                | 禁措辞     |
| source-index       | `research/source-index.md`                                                                   | 血缘       |
| integration-ledger | `research/integration-ledger.md`                                                             | packing    |

**必须读原文：** R3E 任务卡 + 四张兄弟 forward 卡摘要（MASTER Source Context Index）

## Audit Source Trace

| 类别      | 路径                                                 | Audit 用途 |
| --------- | ---------------------------------------------------- | ---------- |
| 任务卡    | `R3E_readonly_data_health_v2.md`                     | A5 AC 对照 |
| MASTER    | `MASTER.plan.md` §2 §5 §9                            | A5 抽检    |
| diff      | `data_health.py` / `data_health_cli.py`              | A1/A4      |
| 测试      | `test_ops_data_health.py` / `test_data_health_v2.py` | A8         |
| hardening | `BATCH_01_HARDENING_RULES.md`                        | A3 禁措辞  |

## 1. 验证覆写

| 维  | 本任务                                 | 命令 / 检查                                                                                                    | 通过条件       |
| --- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------- | --------------------------------------------- | ------------- |
| A3  | 必做                                   | rg `fetch                                                                                                      | httpx          | requests`in`data_health.py` diff；无 DB write | 零 live fetch |
| A6  | **SKIP** — 只读文件体检无 hot path SLA | —                                                                                                              | 记录 SKIP      |
| A7  | 必做                                   | 确认无 migration / `source_health_snapshot` DDL                                                                | 零 schema 变更 |
| A8  | 必做                                   | `uv run pytest tests/test_ops_data_health.py tests/test_data_health_v2.py -q --basetemp=.audit-sandbox/pytest` | exit 0         |

## 2. DoD

- [x] A1–A8 报告 + `audit_matrix.json`
- [x] 对抗性零 OPEN
- [ ] PASS 前不 finish-work
