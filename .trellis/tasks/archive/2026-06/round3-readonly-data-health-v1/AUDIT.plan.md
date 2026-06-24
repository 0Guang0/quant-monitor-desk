# AUDIT 计划 — round3-readonly-data-health-v1

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段            | 值                                      |
| --------------- | --------------------------------------- |
| 任务 slug       | `round3-readonly-data-health-v1`        |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3-dh-audit-prod-equiv` |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务        | 已执行 |
| --- | ---------------- | --------------------------------------------------------- | ------------- | ------ |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做          | [ ]    |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做          | [ ]    |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做          | [ ]    |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做          | [ ]    |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做          | [ ]    |
| A6  | audit-perf       | doubt-driven-development                                  | **不用** SKIP | [ ]    |
| A7  | audit-ops        | doubt-driven-development                                  | 必做          | [ ]    |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做          | [ ]    |
| A9  | 主会话           | —                                                         | 必做          | [ ]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                        | 环境            | 通过条件                   | 已执行 |
| --- | --------------- | -------------------------------------------------- | --------------- | -------------------------- | ------ |
| A1  | read-only       | 对照 R3Y 任务卡、data_quality_rules、playbook §8.1 | local           | 无 scope 泄漏              | [ ]    |
| A2  | review-only     | ponytail-review `data_health.py` + tests           | local           | 最小 diff；复用 validators | [ ]    |
| A3  | static          | 无 prod DB 写 / fetch / forbidden 路径             | local           | 无 mutation                | [ ]    |
| A4  | review-only     | report schema + rule_id 覆盖                       | local           | 无阻断质量问题             | [ ]    |
| A5  | trace-ac        | AC-DH-\* ↔ §8 evidence                             | local           | 全 AC 可追溯               | [ ]    |
| A5  | cli-sandbox     | 复跑 `test_ops_data_health.py`                     | audit-sandbox   | 与 Execute 一致            | [ ]    |
| A6  | —               | **SKIP** — 无 hot path SLA                         | —               | SKIP                       | [ ]    |
| A7  | cli-sandbox     | 无 migration/DB 写                                 | audit-sandbox   | 无 prod 写                 | [ ]    |
| A8  | pytest-isolated | 五字段 docstring + 语义断言抽检                    | audit-sandbox   | 无 call-only 主路径        | [ ]    |
| A8  | audit-prod-path | MAP §2.2 邻接 pytest                               | audit-prod-path | 全绿                       | [ ]    |

### 2.2 A6 SKIP

本任务跳过性能审计 — evidence-path 检查无 full-market scan。

## 3. Audit Source Trace

| Item            | 原文                             | AC                | 证据                      |
| --------------- | -------------------------------- | ----------------- | ------------------------- |
| R3Y 任务卡      | `R3Y_readonly_data_health_v1.md` | AC-DH-\*          | `test_ops_data_health.py` |
| PROMPT_20       | 九切片边界                       | AC-DH-SLICE       | §8 evidence               |
| data_quality    | `data_quality_rules.yaml`        | AC-DH-RULES       | rule tests                |
| staged evidence | v2 execute-evidence              | AC-DH-BIZ         | §8.9                      |
| playbook §8.1   | PASS 表                          | AC-DH-PLAN..BOUND | MASTER §2                 |
| ops 邻接        | db_inspector / staged_pilot      | AC-DH-MAP         | 邻接 pytest               |
| Wave C 铁律     | playbook §2.2–2.3                | AC-DH-TEST        | docstring 抽检            |

## 4. Audit DoD

- [ ] 7.pre gitnexus query
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总
- [ ] 未改 registry / layer4 / staged_evidence
