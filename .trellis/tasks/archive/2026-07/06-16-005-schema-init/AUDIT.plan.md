# Audit 计划 — 005 Schema 初始化（示范）

> **读者：** 主会话 + A1–A8 · 必读本文 + `audit.jsonl` · 各维 **§2** · A5 读 MASTER **§2** · A1 读 `check.jsonl`

---

## 0. 元信息

| 字段        | 值                      |
| ----------- | ----------------------- |
| slug        | `06-16-005-schema-init` |
| audit.jsonl | 第一条 = 本文件         |

**编排：** 7.pre → 7.0 汇总 §2 → A1–A8 执行 §2 → A9 主会话 §4。

---

## 1. 维度 — Agent — Skill 冻结清单

| 维度   | Agent ID         | 执行者     | Skill                          | 本任务   | GitNexus | `@` 指令    | 产出 | 已执行 |
| ------ | ---------------- | ---------- | ------------------------------ | -------- | -------- | ----------- | ---- | ------ |
| A1     | audit-spec       | 子 agent   | trellis-check                  | 必做     | 必用     | 执行 §2 A1  | §3.1 | [ ]    |
| A2     | audit-ponytail   | 子 agent   | ponytail-review                | 必做     | 建议     | 执行 §2 A2  | §3.2 | [ ]    |
| A3     | audit-security   | 子 agent   | security-and-hardening         | 必做     | 必用     | 执行 §2 A3  | §3.3 | [ ]    |
| A4     | audit-quality    | 子 agent   | code-review-and-quality        | 必做     | 建议     | 执行 §2 A4  | §3.4 | [ ]    |
| A5     | audit-completion | 子 agent   | verification-before-completion | 必做     | 必用     | 执行 §2 A5  | §3.5 | [ ]    |
| A6     | audit-perf       | 子 agent   | —                              | **不用** | —        | §2.2 已跳过 | §3.6 | —      |
| A7     | audit-ops        | 子 agent   | —                              | 必做     | 必用     | 执行 §2 A7  | §3.7 | [ ]    |
| A8     | audit-test-gap   | 子 agent   | —                              | 必做     | 必用     | 执行 §2 A8  | §3.8 | [ ]    |
| **A9** | **—**            | **主会话** | —                              | 必做     | 已刷新   | 汇总 §4     | §4   | [ ]    |

---

## 2. 维度验证矩阵（005 已任务化 · 非 MASTER §10 复跑）

| 维     | 验证类型        | 命令 / 检查                                                                          | 环境          | 隔离策略                                        | 通过条件                                    | 证据 →    | 已执行   |
| ------ | --------------- | ------------------------------------------------------------------------------------ | ------------- | ----------------------------------------------- | ------------------------------------------- | --------- | -------- | ---- | --- |
| A1     | read-only       | trellis-check；diff vs check.jsonl；GitNexus query migrate.py 调用链                 | local         | 无写                                            | 无 spec 偏离                                | §3.1      | [ ]      |
| A2     | review-only     | ponytail-review diff                                                                 | —             | —                                               | Lean already 或列 §4.3                      | §3.2      | [ ]      |
| A3     | static          | 威胁面；`rg -i "password                                                             | secret        | api_key" backend/app/db/`；migration SQL 注入点 | local                                       | 无写      | 无 P0/P1 | §3.3 | [ ] |
| A4     | review-only     | code-review-and-quality：migrate.py + tests                                          | —             | —                                               | 无阻塞项                                    | §3.4      | [ ]      |
| A5     | trace-ac        | AC-1..4 ↔ §8/§9/§10 验证链；证据 1–5 分                                              | local         | 无写                                            | 均 ≥4                                       | §3.5      | [ ]      |
| **A6** | —               | **本任务跳过** — schema 初始化无 hot path/SLA                                        | —             | —                                               | N/A（Plan 已记录）                          | §3.6 SKIP | —        |
| A7     | cli-sandbox     | `DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2；查日志                 | audit-sandbox | `.audit-sandbox/data`                           | 第二次 applied=[]                           | §3.7      | [ ]      |
| A8     | pytest-isolated | `pytest tests/test_schema_migration.py -k checksum --basetemp=.audit-sandbox/pytest` | audit-sandbox | tmp                                             | Red Flag :memory: 未违规；测非 tautological | §3.8      | [ ]      |

---

## 3. 工具要求

### 3.0 7.pre

→ `research/gitnexus-audit-summary.md`

### 3.1 各 agent

读 audit 摘要；跑 §2 本维；≥1 GitNexus/CodeGraph query。

---

## 4. 验收汇总（7.0）

→ `audit.report.md` §2（§2 各维 + Execute §10 证据索引只读）

---

## 5. Audit DoD

- [ ] 7.pre；§2 各行（A6 除外 SKIP）已执行
- [ ] A9 §4 已写

---

## 6. 开场白

```text
005 demo Audit：7.pre → 按 §2 派发 A1–A8（A6 SKIP）→ A9 汇总。
不复跑 MASTER §10；A7/A8 用 .audit-sandbox/。
```
