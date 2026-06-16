# MASTER 计划 — 005 Schema 初始化

> **Execute 入口** · Audit → `AUDIT.plan.md` · Repair → `REPAIR.plan.md`（Execute 不读）

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-16-005-schema-init` |
| Audit | `AUDIT.plan.md` |
| Repair | `REPAIR.plan.md`（Audit 后按需） |
| demo | 代码已实现 |

Execute：见 **§0.1 门控**；6.pre → §8 证据 → §9 → §10 → §11 交接 Audit。

### 0.1 门控（摘要）

- **6.pre：** `research/gitnexus-execute-summary.md`（research 例外可读）
- **怎么测：** §9 四层；B/C = prod-path
- **怎么验收：** §10 Execute 专用；Audit 见 AUDIT **§2**
- **什么叫过：** §8 证据 + §10 勾；任务完成 = Audit → Repair? → Finish

---

## 1. 目标

幂等 migration 建 5 张 foundation 表 + `schema_version`。

---

## 2. 预期结果（A5 trace-ac 追溯用）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| AC-1 | 5 表存在 | §10 A + test_schema_migration |
| AC-2 | migration 幂等 | §10 B 复跑 |
| AC-3 | checksum fail-fast | test modifiedFile |
| AC-4 | init_db 写锁 | §10 B prod-path + 代码审查 |

---

## 7. Red Flags

| Red Flag | 预防 |
|----------|------|
| 整库 schema.sql | DECISIONS §3 |
| :memory: 代 prod 验收 | §9/§10 Tier B/C prod-path |

---

## 8. 实现步骤

### 8.1 失败测试

| 字段 | 内容 |
|------|------|
| Skill | test-driven-development |
| 验证命令 | `pytest tests/test_schema_migration.py -v` |
| **通过条件** | FAIL（模块不存在） |
| **环境** | local |
| **证据** | demo 已 GREEN |
| 已执行 | [x] |

### 8.2 migration 实现

| 字段 | 内容 |
|------|------|
| Skill | TDD + incremental-implementation |
| 验证命令 | `pytest tests/test_schema_migration.py -v` |
| **通过条件** | 7 passed |
| **环境** | local → prod-path |
| **证据** | demo 7 passed |
| 已执行 | [x] |

---

## 9. 测试层次（四层必做）

| 层次 | 必做 | 环境 | 命令 | 通过条件 | 文件 |
|------|------|------|------|----------|------|
| 单元 | ✅ | local | pytest test_schema_migration | 7 passed | tests/test_schema_migration.py |
| 集成 | ✅ | local | pytest -q | exit 0 | tests/ |
| 管道 | ✅ | prod-path | init_db + migrate 复跑 | 幂等 | scripts/init_db.py |
| smoke | ✅ | prod-path | pytest -q 全库 | exit 0 | — |

---

## 10. 验收 Tier 表（Execute 专用 · Plan 冻结）

> Audit 见 `AUDIT.plan.md` §2；本表 **仅 Execute**。

| Tier | 环境 | 命令 | 通过条件 | Execute 证据 | Execute 勾 |
|------|------|------|----------|--------------|------------|
| A | ci | `pytest tests/test_schema_migration.py -v` | 7 passed | demo log | [x] |
| A | ci | `ruff check .` | 0 | demo | [x] |
| B | prod-path | `python scripts/init_db.py` | 库+migration | demo DATA_ROOT | [x] |
| B | prod-path | 再跑 init_db | applied none | demo 幂等 log | [x] |
| C | prod-path | `pytest -q` | exit 0 | demo | [x] |

---

## 11. Execute 交接 DoD（≠ 任务完成）

- [x] §8 证据齐
- [x] §9/§10 Execute 勾
- [x] §12 Execute skill 勾
- [ ] **交接 Audit**（勿 finish-work）

---

## 12. Execute Skill 冻结

| Skill | 本任务 | 绑定 | 已执行 |
|-------|--------|------|--------|
| test-driven-development | 必做 | 8.x | [x] |
| incremental-implementation | 必做 | 8.x | [x] |
| source-driven-development | 条件 | 8.2 DuckDB | [x] |
| systematic-debugging | 条件 | RED | [ ] |
| trellis-implement | 不用 | inline | — |

**Audit → `AUDIT.plan.md` §1 Skill + §2 验证矩阵**
