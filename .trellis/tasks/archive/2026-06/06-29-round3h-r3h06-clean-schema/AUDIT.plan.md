# Audit 计划 — R3H-06 Clean Schema (Wave 1)

> **读者：** 主会话 + A1–A8  
> **索引：** `EXECUTION_INDEX.md` §5

| 字段        | 值                                 |
| ----------- | ---------------------------------- |
| slug        | `06-29-round3h-r3h06-clean-schema` |
| audit.jsonl | 第一条 = 本文件                    |

---

## 0.1 Trace Authority Set

| 类别              | 文件                                     | 用途              |
| ----------------- | ---------------------------------------- | ----------------- |
| 原始任务卡        | `R3H_06_CLEAN_SCHEMA.md`                 | scope / AC        |
| PASS 计划         | `R3H_PASS_EXECUTION_PLAN.md`             | Wave 1 / DDL 独占 |
| 3G gaps           | `R3G_MASS_REHEARSAL_OPEN_GAPS.md`        | G3–G6             |
| schema SSOT       | `specs/schema/schema.sql`                | DDL 对照          |
| migration 矩阵    | `docs/schema/MIGRATION_COVERAGE.md`      | 013 DONE          |
| 执行索引          | `EXECUTION_INDEX.md`                     | 血缘 + manifest   |
| omission-check    | `research/project-map-omission-check.md` | 地图倒查          |
| integration-audit | `research/integration-audit.md`          | 5d 对抗           |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                         | 环境          | 通过条件       | 已执行 |
| --- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------------- | ------ |
| A1  | 必做   | 活卡 §9–§12；§5.0.1 三项 CLOSED 证据；无 Wave 2+ DDL                                                                                                                | local         | 无 scope 漏/扩 | [ ]    |
| A2  | 必做   | migration 013 ↔ schema.sql ↔ MIGRATION_COVERAGE 一致                                                                                                                | local         | 无漂移         | [ ]    |
| A3  | 必做   | cninfo 无 bar 形写入；禁止主库 mutation proof                                                                                                                       | local         | fail-closed    | [ ]    |
| A4  | 必做   | 重复 promote idempotency；OHLCV 列非空路径                                                                                                                          | audit-sandbox | 对抗测绿       | [ ]    |
| A6  | 不用   | **SKIP** — schema 任务无 hot path                                                                                                                                   | —             | —              | [ ]    |
| A7  | 必做   | promote 仍拒 canonical DB；无新写主库 CLI                                                                                                                           | audit-sandbox | CLI 边界       | [ ]    |
| A8  | 必做   | `pytest tests/test_r3h06_clean_schema.py tests/test_round3g_limited_production_clean_write.py tests/test_migration_coverage.py -q --basetemp=.audit-sandbox/pytest` | audit-sandbox | 全绿           | [ ]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `research/gitnexus-audit-summary.md`
- [ ] 派发 A1–A8 → `audit.report.md`
- [ ] PASS / PASS_WITH_FIXES / FAIL

## 3. §5.0.1 交叉项审计清单

| ID                      | 审计证据                         |
| ----------------------- | -------------------------------- |
| SCHEMA-G3G4             | 9.1+9.3+9.4 测 + migration 013   |
| CNINFO-DISCLOSURE-SHAPE | 9.2+9.5 测 + capabilities 列对齐 |
| G6-IDEMPOTENCY          | 9.6+9.7 测 + `upsert_by_pk`      |
