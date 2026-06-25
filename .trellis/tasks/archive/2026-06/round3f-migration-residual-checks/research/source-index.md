# 来源索引 — B3F-MIG migration residuals

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                             |
| ------------- | ---------------------------------------------- |
| Round / Batch | Round 3F · `BATCH_3F_BATCH6_DATA_GOVERNANCE`   |
| Playbook ID   | `B3F-MIG`                                      |
| Roadmap       | `R3F-MIG-01..06`                               |
| 协调包        | `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.3 + §8.1 |
| gate / 分支   | `feature/round3f-migration-residual-checks`    |
| 合并顺序      | **§7.2 序 1** — B3F-SH 依赖本分支 migration    |

### AC 映射 → MASTER §4

| Roadmap ID | MASTER AC | 验证链                         |
| ---------- | --------- | ------------------------------ |
| R3F-MIG-01 | AC-MIG-01 | MIG-01 → §9.1 verify-only      |
| R3F-MIG-02 | AC-MIG-02 | MIG-02 → §9.2 ADR + DDL        |
| R3F-MIG-03 | AC-MIG-03 | MIG-03 → §9.3 012 rebuild      |
| R3F-MIG-04 | AC-MIG-04 | MIG-04 → §9.4 lifecycle列      |
| R3F-MIG-05 | AC-MIG-05 | MIG-05 → §9.5 路由文档         |
| R3F-MIG-06 | AC-MIG-06 | MIG-06 → §9.6 regression guard |

### 路径纠偏

- `source_health_snapshot` → **B3F-SH** owns；本任务 forbidden。
- `D2-P3-1` 列 migration 本任务 owns；sync 语义与 B3F-HYG 不混同一 PR。

---

## B. 输入 manifest

| 路径                                    | 类别 | manifest | extract / for       |
| --------------------------------------- | ---- | -------- | ------------------- |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`      | 协调 | required | §3.3 §8.1 边界      |
| `MIGRATION_008_PLAN.md`                 | 架构 | required | R3F-MIG-05 路由     |
| `MIGRATION_COVERAGE.md`                 | 架构 | required | 009/3F 桶           |
| `009_status_check_constraints.sql`      | 接线 | required | R3F-MIG-01 只读对照 |
| `012_migration_residuals.sql`           | 接线 | required | MIG-03/04           |
| `ADR-002-db-check-vs-app-validation.md` | 决策 | required | MIG-02              |
| `source_registry.py`                    | 接线 | required | MIG-04 sync         |
| `test_round3f_migration_residuals.py`   | 测试 | required | §5.1 六用例         |
| `test_schema_contract.py`               | 测试 | required | playbook §8.1 基线  |
| `test_migration_coverage.py`            | 测试 | required | playbook §8.1 基线  |

---

## C. 六类覆盖自检

| 类别 | 路径                                                | [x] |
| ---- | --------------------------------------------------- | --- |
| 决策 | `ADR-002-db-check-vs-app-validation.md`             | [x] |
| 规则 | `GLOBAL_*.md` ×3 + `BATCH_3F_HARDENING_RULES.md`    | [x] |
| 架构 | `MIGRATION_COVERAGE.md`, `MIGRATION_008_PLAN.md`    | [x] |
| 需求 | `PROJECT_IMPLEMENTATION_ROADMAP.md` R3F-MIG-\*      | [x] |
| 契约 | migration SQL + ADR-002                             | [x] |
| 接线 | `012_migration_residuals.sql`, `source_registry.py` | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger required
