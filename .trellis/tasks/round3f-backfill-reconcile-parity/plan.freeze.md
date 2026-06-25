# Plan 冻结 — round3f-backfill-reconcile-parity (B3F-BR)

> 补 Plan 冻结追溯 Execute 已交付 · 待协调者批准前禁止 `task.py start`

## 1. Plan Phase

| Phase | 产出 | [x] |
|-------|------|-----|
| P0 | plan-boot, source-index, original-plan-trace | [x] |
| 1a–5d | project-overview, prd, MASTER, AUDIT, manifests | [x] |

## 2. 必需文件

| 文件 | [x] |
|------|-----|
| MASTER.plan.md | [x] |
| AUDIT.plan.md | [x] |
| implement.jsonl / audit.jsonl / check.jsonl | [x] |

## 3. 冻结自检

### 3.0 双契约

| 契约 | 冻结位置 |
|------|----------|
| 验收 | MASTER §8–§10 |
| Audit | AUDIT §1 |

### 3.0b 原计划包门禁

| [x] | GLOBAL×3 + Batch hardening 已摘要 |
| [x] | Roadmap 3F.4 + Playbook §3.6 已索引 |
| [x] | MASTER §1.5 §1.6 §5 已填 |
| [x] | R3-PARTIAL-5 guard only 已标注 |

### 3.0c Context Packing v3

| [x] | source-index §C 索引完整 |
| [x] | integration-ledger ≥5 rows |
| [x] | integration-audit PASS |
| [x] | manifest_protocol_version: "3" |

### 3.1 MASTER

| [x] | §8 垂直切片 + 交付物 |
| [x] | §9 RED/GREEN |
| [x] | §5 测试契约 |
| [x] | §2 Playbook §8.5 AC |

### 3.2 AUDIT

| [x] | 无未替换占位符 |
| [x] | A6 SKIP 已记录 |

### 3.6 validate-plan-freeze

```text
Plan freeze validation passed
(exit 0 — 2026-06-25 · python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3f-backfill-reconcile-parity)
```

## 4. Manifest Gate / Context Packing Gate

| [x] | `implement.jsonl` 第一条 = MASTER |
| [x] | `integration-ledger.md` 在 implement.jsonl |
| [x] | `audit.jsonl` 第一条 = AUDIT.plan.md |
| [x] | `plan-skill-reads` 覆盖 freeze skills |
| [x] | MASTER §0.3 + §9.0 → implement + ledger |
| [x] | `validate-plan-freeze` exit 0 |

## 5. 批准

- [ ] 用户/协调者批准 Plan
- [ ] `task.py start` 后进入 Execute
