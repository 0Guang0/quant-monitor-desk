# Audit 计划 — Round 3 Batch 1 Early Ops

> 读者：主会话 + A1–A8 子 agent  
> 必读：本文 + `audit.jsonl`；A5 另读 MASTER §2；Execute §10 证据只读。

---

## 0. 元信息

| 字段        | 值                              |
| ----------- | ------------------------------- |
| 任务 slug   | `06-20-round3-batch1-early-ops` |
| audit.jsonl | 第一条 = 本文件                 |

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID         | Skill                                                     | 本任务 | 产出 | 已执行 |
| ---- | ---------------- | --------------------------------------------------------- | ------ | ---- | ------ |
| A1   | audit-spec       | trellis-check + doubt-driven-development                  | 必做   | §3.1 | [x]    |
| A2   | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做   | §3.2 | [x]    |
| A3   | audit-security   | security-and-hardening + doubt-driven-development         | 必做   | §3.3 | [x]    |
| A4   | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做   | §3.4 | [x]    |
| A5   | audit-completion | verification-before-completion + doubt-driven-development | 必做   | §3.5 | [x]    |
| A6   | audit-perf       | systematic-debugging + doubt-driven-development           | 必做   | §3.6 | [x]    |
| A7   | audit-ops        | doubt-driven-development                                  | 必做   | §3.7 | [x]    |
| A8   | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做   | §3.8 | [x]    |
| A9   | —                | —                                                         | 必做   | §4   | [x]    |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                                                                                                        | 环境             | 隔离                                     | 通过条件                                              | 证据 → | 已执行 |
| --- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------- | ---------------------------------------- | ----------------------------------------------------- | ------ | ------ | -------------------------------------------- | ----- | ---- | ------------------------ | ---- | --- |
| A1  | read-only       | 对照 `ops_db_inspect_contract.yaml`、`db_inspect_cli.md` Phase A、MASTER §2                                                                                        | local            | 无写                                     | 无 scope 泄漏（017/migration/network）                | §3.1   | [x]    |
| A2  | review-only     | ponytail-review `backend/app/ops/` + `scripts/qmd_ops.py`                                                                                                          | local            | 无写                                     | 无冗余 abstraction                                    | §3.2   | [x]    |
| A3  | static          | `rg -n "writer\\(                                                                                                                                                  | apply_migrations | duckdb.connect\\([^)]*\\)(?!.*read_only) | --enable-qmt                                          | INSERT | UPDATE | DELETE " backend/app/ops scripts/qmd_ops.py` | local | 无写 | 无 mutation/SQL 注入路径 | §3.3 | [x] |
| A4  | review-only     | 审 error handling、path traversal guard、JSON serialization                                                                                                        | local            | 无写                                     | 无阻断质量问题                                        | §3.4   | [x]    |
| A5  | trace-ac        | AC-CLI/DB/DOC/E2E/BENCH/OPS ↔ §8 evidence ↔ registry                                                                                                               | local            | 无写                                     | 全 AC ≥4 分可追溯                                     | §3.5   | [x]    |
| A5  | cli-sandbox     | `.audit-sandbox/r3b1-audit` 独立复跑 `test_ops_db_inspector.py` + CLI                                                                                              | audit-sandbox    | 独立 data root                           | 与 Execute 一致                                       | §3.5   | [x]    |
| A5  | read-only       | 抽检 2 个 execute-evidence green 文件真实性                                                                                                                        | local            | 无写                                     | 非占位符                                              | §3.5   | [x]    |
| A6  | cli-sandbox     | `cp -r data → .audit-sandbox/r3b1-audit-prod-equiv/data`; `DbInspector(profile=eco).inspect()` on copy; measure elapsed + RSS; prod DB hash before/after unchanged | audit-prod-path  | copy only, read-only inspect             | elapsed ≤ 30s eco; RSS ≤ 1GB soft; prod DB unpolluted | §3.6   | [x]    |
| A7  | cli-sandbox     | 二次 `qmd_ops db-inspect` 确认 production DB 未修改；registry 与 inspect JSON 一致                                                                                 | audit-sandbox    | read-only 项目 DB                        | 无污染                                                | §3.7   | [x]    |
| A8  | pytest-isolated | 补 2 边界：超大 `--limit` cap、path outside data_root rejected                                                                                                     | audit-sandbox    | tmp                                      | 新测绿或 §4.3                                         | §3.8   | [x]    |

## 3. Audit Source Trace

| Item ID                     | 原文                              | AC         | 证据                                 |
| --------------------------- | --------------------------------- | ---------- | ------------------------------------ |
| `R3-EARLY-DB-INSPECT-CLI`   | `db_inspect_cli.md` §5–11         | AC-CLI-\*  | `test_ops_db_inspector.py`, CLI JSON |
| `DB-R3-001`                 | `UNRESOLVED_ISSUES_REGISTRY`      | AC-DB-1    | inspect `data_root.*_count`          |
| `DB-R3-002`                 | 同上                              | AC-DB-2    | `db.read_only_open`, `key_tables`    |
| `DOC-R3-001/002`            | handoff + early plan + UNRESOLVED | AC-DOC-\*  | doc diff + registry                  |
| `R3-PARTIAL-2`              | `AUDIT_DEFERRED_REGISTRY`         | AC-E2E-1   | vendor E2E + sync_jobs pytest        |
| `R3-EARLY-PROD-SCALE-BENCH` | `016F` + smoke script             | AC-BENCH-1 | smoke output file                    |
| `R2.6-IMPL-8`               | early close plan                  | AC-OPS-1   | registry DEFERRED + no enable flags  |

## 4. Audit DoD

- [x] 7.pre `gitnexus-audit-summary.md`
- [x] A1–A8 完成（A6 补跑 audit-prod-path perf）
- [x] A9 汇总 PASS / PASS_WITH_FIXES / FAIL
