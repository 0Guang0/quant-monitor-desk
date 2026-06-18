# REPAIR 计划 — Round 2 Batch C validation/conflict

> Repair 入口。仅在 Audit verdict 为 PASS_WITH_FIXES 或 FAIL 时使用。  
> Repair 执行者必须先读 `audit.report.md` §4.3，再读本文件与 `repair.jsonl`。  
> 原则：修根因，不兜底；所有 Audit §4.3 必须关闭，或 §4.4 明确 Deferred 且用户批准。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-c-validation-conflict` |
| 输入 | `audit.report.md` |
| 输出 | `REPAIR.report.md` 或更新后的 handoff |
| 允许阶段 | Phase 8 Repair |
| 禁止 | 不得新增未审计 scope，不得通过跳测假绿 |

---

## 1. Repair Skill freeze

| Skill | 本任务 | 触发 | 指令 |
|-------|--------|------|------|
| `trellis-repair` | 必做 | 每项 §4.3 | `@trellis-repair 按 audit.report §4.3 逐项修复并保存证据。` |
| `diagnose` | 必做 | 每个 failing test / bug | `@diagnose 复现→缩小→根因→最小修复→回归。` |
| `tdd` | 条件 | 发现缺失测试 | `@tdd 先补失败测试，再实现修复。` |
| `security` | 条件 | 脱敏/status 映射问题 | `@security 验证敏感字段不入日志。` |

---

## 2. Repair workflow

For each Audit §4.3 item:

1. Copy finding into checklist.
2. Identify root cause.
3. Add or update failing test.
4. Apply minimal fix.
5. Run targeted test.
6. Run relevant §10 gate.
7. Save evidence under:

```text
.trellis/tasks/06-17-round2-batch-c-validation-conflict/repair-evidence/
```

8. Mark item closed only when test and code review support it.

---

## 3. Required evidence

```text
repair-evidence/{finding-id}-red.txt
repair-evidence/{finding-id}-green.txt
repair-evidence/final-gates.txt
```

---

## 4. Deferred policy

A finding may be deferred only if all are true:

- It is not required for Batch C AC-1 through AC-11.
- It belongs clearly to Batch D / Round 3 / Round 4 / Round 5.
- It is recorded in `BATCH_C_REPAIR_STATUS.md`.
- User explicitly accepts the deferral.

---

## 6. Audit §4.3 checklist（2026-06-17 对抗审计录入）

| ID | 状态 | 摘要 |
|----|------|------|
| R-C-01 | closed | `_persist_report` 多 instrument key 错误（P1） |
| R-C-02 | closed | layer1/layer3 YAML 规则已实现（P1） |
| R-C-03 | closed | Reconcile-first + `record_unresolved_reconcile`（P1） |
| R-C-04 | closed | `MISSING_SOURCE_USED` rule_id（P2） |
| R-C-05 | closed | gate/E2E 测试补强（P2） |
| R-C-07 | closed | DECISIONS/BATCH_C_REPAIR_STATUS 文档对齐（P2） |
| R-C-08 | closed | task 目录 pytest 残留已清理或已记录（P2） |

详见 `audit.report.md` §4.3。

```bash
pytest tests/test_data_quality_validator.py \
       tests/test_source_conflict_validator.py \
       tests/test_db_validation_gate.py \
       tests/test_ingestion_validation_migration.py \
       tests/test_batch_c_validation_flow.py -q

pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
python scripts/check_doc_links.py
```

---

## 6. Repair output

Final repair response must include:

1. Closed findings.
2. Remaining findings, if any.
3. Deferred findings with stage and user approval status.
4. Commands run and results.
5. Evidence paths.
6. `READY_FOR_REAUDIT: yes/no`.
