# Audit 计划 — B3F-HYG hygiene / perf / ingestion split

| 字段        | 值                             |
| ----------- | ------------------------------ |
| slug        | `round3-batch6-technical-debt` |
| audit.jsonl | 第一条 = 本文件                |

## 0.1 Trace Authority Set

| 类别            | 文件                                                           | 用途                    |
| --------------- | -------------------------------------------------------------- | ----------------------- |
| 协调包          | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.7、§8.6                  | scope / PASS 命令       |
| Roadmap         | `PROJECT_IMPLEMENTATION_ROADMAP.md` R3F-HYG-\*                 | AC                      |
| VR scope        | `R3F_verified_audit_ops_perf_hygiene.md`                       | VR-PERF-001 / VR-RG-001 |
| context-closure | `research/context-closure.md`                                  | 血缘                    |
| rollback        | `docs/architecture/layer1_ingestion_refactor_rollback_plan.md` | R2b DONE                |

## Audit Source Trace

| 类别      | 路径                                                                                                       | Audit 用途 |
| --------- | ---------------------------------------------------------------------------------------------------------- | ---------- |
| MASTER    | `MASTER.plan.md` §8                                                                                        | A5 抽检    |
| diff      | `perf_budget.py`, `sandbox_bootstrap.py`, `production_equivalent_smoke.py`                                 | A1/A4/A6   |
| 测试      | `test_production_equivalent_smoke_budget.py`, `test_layer1_sandbox_bootstrap.py`, `test_resource_guard.py` | A8         |
| forbidden | playbook §3.7 migration 列 / live source                                                                   | A3/A7      |

## 1. 验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                              | 通过条件               |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| A3  | 必做   | diff 无 production clean write；无 migration 列                                                                                                                          | 零写库路径             |
| A6  | 必做   | `production_equivalent_smoke.py --write-artifact` + perf budget 负向测                                                                                                   | FAIL artifact + exit≠0 |
| A7  | 必做   | 无 `source_health_snapshot` migration；无 orchestrator handler diff                                                                                                      | forbidden 零 diff      |
| A8  | 必做   | `uv run pytest tests/test_resource_guard.py tests/test_production_equivalent_smoke_budget.py tests/test_layer1_sandbox_bootstrap.py -q --basetemp=.audit-sandbox/pytest` | exit 0                 |

## 2. DoD

- [x] A1–A8 报告 + `audit_matrix.json`
- [x] perf budget 负向：pytest_steps / shard_count / guard_status / bad YAML
- [x] sandbox_bootstrap 二次 prepare 幂等测
- [x] PASS 前不 finish-work
- [x] registry 闭合由 B3F-REG / 主会话验证（非本 Audit 必达）
