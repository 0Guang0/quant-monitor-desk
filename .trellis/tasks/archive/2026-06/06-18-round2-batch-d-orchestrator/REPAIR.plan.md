# REPAIR 计划 — Round 2 Batch D

> Repair 仅在 Audit PASS_WITH_FIXES / FAIL 时使用。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-18-round2-batch-d-orchestrator` |
| 输入 | `audit.report.md` §4.3 |
| 输出 | `REPAIR.report.md` |
| 禁止 | 扩大 scope；跳测假绿 |

---

## 1. Repair Skill freeze

| Skill | 本任务 | 触发 |
|-------|--------|------|
| trellis-repair | 必做 | 每项 §4.3 |
| diagnose | 必做 | failing test |
| tdd | 条件 | 缺测修复 |
| security | 条件 | 日志脱敏 |

---

## 2. Workflow

每项 §4.3：根因 → 失败测 → 最小修复 → 靶向 pytest → §10 相关 gate → `repair-evidence/{id}-red/green.txt`

---

## 3. Deferred policy

仅当：非 AC-1…AC-12 必需 + 明确后续 Round + 记入 `BATCH_D_STATUS.md` + 用户批准。

---

## 4. §4.3 checklist（Audit 填入）

| ID | 状态 | 摘要 |
|----|------|------|
| — | pending | （Audit 后填写） |

---

## 5. Final gates

```text
repair-evidence/final-gates.txt  # 复跑 MASTER §10 Tier C
```
