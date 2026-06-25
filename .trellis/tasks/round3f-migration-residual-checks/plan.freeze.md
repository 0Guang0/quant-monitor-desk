# Plan 冻结 — round3f-migration-residual-checks (B3F-MIG)

> 待用户/协调者批准前禁止 `task.py start`

## 1. Plan Phase

| Phase | 产出 | [x] |
|-------|------|-----|
| P0 | plan-boot, source-index, original-plan-trace, context_pack | [x] |
| 1a–5d | project-overview, prd, MASTER, AUDIT, manifests | [x] |

## 2. 必需文件

| 文件 | [x] |
|------|-----|
| MASTER.plan.md | [x] |
| AUDIT.plan.md | [x] |
| implement.jsonl / audit.jsonl / check.jsonl | [x] |
| research/plan-qc-3.10.md | [x] |

## 3. 冻结自检

### 3.0 双契约

| 契约 | 冻结位置 |
|------|----------|
| 验收 | MASTER §8–§10 |
| Audit | AUDIT §1 |

### 3.0b 原计划包门禁

| [x] | GLOBAL×3 + BATCH_3F_HARDENING 已摘要 |
| [x] | Playbook §3.3 已索引；R3F-MIG-01..06 映射 |
| [x] | MASTER §1.5 §5 已填 |
| [x] | Playbook §3.1+§3.3 已入 Source Context Index |

### 3.0c Context Packing Gate v3

| [x] | source-index §C 索引完整 |
| [x] | integration-ledger ≥5 rows |
| [x] | integration-audit PASS |
| [x] | manifest_protocol_version: "3" |

### 3.1 MASTER

| [x] | §8 垂直切片 MIG-01..06 |
| [x] | §9 RED/GREEN |
| [x] | §5 测试契约含负向（MIG-01 verify-only） |
| [x] | §2 R3F-MIG 缺口分析 |

### 3.2 AUDIT

| [x] | Trace Authority Set |
| [x] | A6 SKIP 已记录 |

### 3.6 validate-plan-freeze

```text
2026-06-25 B3F-MIG Plan: python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/round3f-migration-residual-checks → exit 0
```

## 4. Manifest Gate

| [x] | implement.jsonl 第一条 = MASTER |
| [x] | integration-ledger 在 implement |
| [x] | audit.jsonl 第一条 = AUDIT |
| [x] | plan-skill-reads 覆盖 freeze skills |
| [x] | source_health_snapshot 不在 Execute 范围 |

## 5. 批准

- [ ] 用户/协调者批准 Plan
- [ ] `task.py start` 后进入 Execute
