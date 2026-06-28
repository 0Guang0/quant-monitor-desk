# Plan 冻结 — round3v-sync-support-matrix-recovery (B3V-SYNC)

> 待用户/协调者批准前禁止 `task.py start`

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
| [x] | B02_04 + Playbook §3.1+§3.5 已索引 |
| [x] | MASTER §1.5 §1.6 §5 已填 |
| [x] | OPS write 契约只读依赖已标注 |

### 3.0c Context Packing v3

| [x] | source-index §C 索引完整 |
| [x] | integration-ledger ≥5 rows |
| [x] | integration-audit PASS |
| [x] | manifest_protocol_version: "3" |

### 3.1 MASTER

| [x] | §8 垂直切片 + 交付物 |
| [x] | §9 RED/GREEN |
| [x] | §5 测试契约 |
| [x] | §2 Playbook §8.4 AC |

### 3.2 AUDIT

| [x] | 无未替换占位符 |
| [x] | A6 SKIP 已记录 |

### 3.6 validate-plan-freeze

```text
2026-06-28 B3V-SYNC Plan 质检: python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3v-sync-support-matrix-recovery → exit 0
（Plan 基线 1290b2e · SYNC-06A/B/C → §9.6/9.7/9.8）
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
