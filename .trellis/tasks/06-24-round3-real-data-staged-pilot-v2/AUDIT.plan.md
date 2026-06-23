# AUDIT 计划 — B-19 staged pilot v2

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段            | 值                                        |
| --------------- | ----------------------------------------- |
| 任务 slug       | `06-24-round3-real-data-staged-pilot-v2`  |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3y-pilot-v2-audit-prod/` |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行 |
| --- | ---------------- | --------------------------------------------------------- | -------- | ------ |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]    |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]    |
| A3  | audit-security   | security-and-hardening + doubt-driven-development       | 必做     | [ ]    |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development      | 必做     | [ ]    |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]    |
| A6  | audit-perf       | doubt-driven-development                                  | **不用** | [ ]    |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]    |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]    |
| A9  | 主会话           | —                                                         | 必做     | [ ]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                                     | 环境            | 通过条件                  | 已执行 |
| --- | --------------- | ----------------------------------------------------------------------------------------------- | --------------- | ------------------------- | ------ |
| A1  | read-only       | 对照 R3Y 任务卡、AUD-08 控件、MASTER §2/§3                                                     | local           | 无 scope 泄漏             | [ ]    |
| A2  | review-only     | ponytail-review `backend/app/ops/staged_pilot.py` `mutation_proof.py`                         | local           | 最小 diff                 | [ ]    |
| A3  | static          | `rg` production clean write / sync `adapter=` 新增                                              | local           | 无 mutation 旁路          | [ ]    |
| A4  | review-only     | closeout 字段、evidence 命名 v2 一致性                                                          | local           | 无阻断质量问题            | [ ]    |
| A5  | trace-ac        | AC-SP2-01..09 + AC-MUT-001 ↔ §8 evidence                                                        | local           | 九切片可追溯              | [ ]    |
| A5  | cli-sandbox     | `.audit-sandbox/r3y-pilot-v2-audit/` 复跑 `test_staged_pilot.py`                                | audit-sandbox   | 与 Execute 一致           | [ ]    |
| A5  | read-only       | 抽检 `execute-evidence/8.8-green.txt` 与 `no_mutation_proof_v2.md`                              | local           | hash/count 明细非仅 VERIFIED | [ ]    |
| A5  | audit-prod-path | 复制树到 `AUDIT_PROD_ROOT`；`uv run pytest tests/test_staged_pilot.py -q`；prod data hash 不变   | audit-prod-path | 无污染                    | [ ]    |
| A6  | —               | **本任务跳过 — pilot 无 hot path/SLA；受控小样本**                                              | —               | SKIP                      | [ ]    |
| A7  | cli-sandbox     | 确认无 migration/DB clean write；sandbox 无 `data/` 污染                                        | audit-sandbox   | 无 prod 写                | [ ]    |
| A7  | audit-prod-path | `data/duckdb/` hash 审计前后不变                                                                | audit-prod-path | 无污染                    | [ ]    |
| A8  | pytest-isolated | 补边界：非 KEY 表 hash 变 / count 不变（若 Execute 未列）                                       | audit-sandbox   | 新测绿或记入 audit.report | [ ]    |
| A8  | audit-prod-path | 复跑 `test_production_live_pilot_policy.py`                                                     | audit-prod-path | 全绿                      | [ ]    |

### 2.2 A6 SKIP

本任务跳过性能审计 — 受控小样本 staged pilot，无 SLA。

## 3. Audit Source Trace

| Item | 原文 | AC | 证据 |
| ---- | ---- | -- | ---- |
| R3Y | `R3Y_real_data_staged_pilot_v2.md` | AC-SP2-\* | execute-evidence v2 |
| AUD-08 | `R3Y-AUD-08-go-no-go.md` | 控件 | closeout 字段 |
| AUD-04 | `R3Y-AUD-04-staged-pilot.md` | AC-MUT-001 | `mutation_proof.py` + 8.8 |
| v1 | PROMPT_14 evidence | 对照 | diff v2 |
| policy | `production_live_pilot_policy.md` | staged-only | policy tests |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
