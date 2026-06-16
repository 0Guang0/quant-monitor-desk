# MASTER 计划 — Round 1 数据底座（005–010 · retrospective）

> **Execute 入口** · Audit → `AUDIT.plan.md` · Repair → `REPAIR.plan.md`

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round1-foundation-audit` |
| 关联 Round | `ROUND_1_DATA_FOUNDATION`（005–010） |
| retrospective | 93/93 tests（2026-06） |

### 0.1 门控

- **6.pre：** `research/gitnexus-execute-summary.md`
- **Execute DATA_ROOT：** `data/`（prod-path）
- **Audit sandbox：** `.audit-sandbox/data`（≠ Execute DATA_ROOT）

---

## 1. 目标

本地数据底座：migration、ResourceGuard、ConnectionManager、WriteManager（stub ValidationGate）、RawStore、foundation smoke。

---

## 2. 预期结果（A5 trace-ac）

| # | 预期结果 | 验证链 |
|---|----------|--------|
| AC-1 | 5 foundation 表 + schema_version | test_schema_migration |
| AC-2 | migration 幂等 + checksum | §10 B |
| AC-3 | ResourceGuard 判定/落库 | test_resource_guard |
| AC-4 | ConnectionManager 锁 + reader CM | test_duckdb_connection |
| AC-5 | WriteManager + audit | test_write_manager |
| AC-6 | RawStore hardening | test_raw_store |
| AC-7 | foundation smoke E2E | test_foundation_smoke |
| AC-8 | stub ValidationGate 契约 | DECISIONS §9 |

---

## 7. Red Flags

整库 schema.sql；:memory: 代 prod；绕过 WriteManager；SQL 注入；own_transaction 误 ROLLBACK。

---

## 8. 实现步骤（005–010 · 已执行 [x]）

见 `docs/implementation_tasks/ROUND_1_DATA_FOUNDATION/plans/` 各 plan。

---

## 9. 测试层次

单元 67+ / 集成 93/93 / 管道 init_db 幂等 / smoke foundation。

---

## 10. 验收 Tier（Execute · DATA_ROOT=data/）

| Tier | 命令 | Execute 勾 |
|------|------|------------|
| A | pytest -q; ruff; compileall | [x] |
| B | init_db ×2 幂等 | [x] |
| C | test_foundation_smoke | [x] |

---

## 11. Execute 交接

- [x] 交接 Audit（勿 finish-work）

---

## 12. Execute Skill

TDD + incremental 必做 [x]；source-driven 条件 [x]；systematic-debugging 审计修复 [x]。
