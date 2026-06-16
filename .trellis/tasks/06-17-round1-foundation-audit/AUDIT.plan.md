# Audit 计划 — Round 1 数据底座（005–010 · retrospective）

> **读者：** 主会话 + A1–A8 · 必读本文 + `audit.jsonl` · 各维 **§2** · A5 读 MASTER **§2** · A1 读 `check.jsonl`

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round1-foundation-audit` |
| audit.jsonl | 第一条 = 本文件 |
| Execute DATA_ROOT | `data/` |
| Audit sandbox | `.audit-sandbox/data`（**≠** Execute DATA_ROOT） |

**编排：** 7.pre → 7.0 → A1–A8 → A9。

---

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID | 执行者 | Skill | 本任务 | GitNexus | `@` 指令 | 产出 | 已执行 |
|------|----------|--------|-------|--------|----------|----------|------|--------|
| A1 | audit-spec | 子 agent | trellis-check | 必做 | 必用 | 执行 §2 A1 | §3.1 | [x] |
| A2 | audit-ponytail | 子 agent | ponytail-review | 必做 | 建议 | 执行 §2 A2 | §3.2 | [x] |
| A3 | audit-security | 子 agent | security-and-hardening | 必做 | 必用 | 执行 §2 A3 | §3.3 | [ ] |
| A4 | audit-quality | 子 agent | code-review-and-quality | 必做 | 建议 | 执行 §2 A4 | §3.4 | [ ] |
| A5 | audit-completion | 子 agent | verification-before-completion | 必做 | 必用 | 执行 §2 A5 | §3.5 | [ ] |
| A6 | audit-perf | 子 agent | — | **不用** | — | §2.2 已跳过 | §3.6 | — |
| A7 | audit-ops | 子 agent | — | 必做 | 必用 | 执行 §2 A7 | §3.7 | [ ] |
| A8 | audit-test-gap | 子 agent | — | 必做 | 必用 | 执行 §2 A8 | §3.8 | [ ] |
| **A9** | **—** | **主会话** | — | 必做 | 已刷新 | 汇总 §4 | §4 | [ ] |

---

## 2. 维度验证矩阵（Round 1 · 非 MASTER §10 复跑）

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 证据 → | 已执行 |
|----|----------|-------------|------|----------|----------|--------|--------|
| A1 | read-only | trellis-check；对照 check.jsonl；GitNexus query WriteManager→ValidationGate→migrate 链 | local | 无写 | 符合 DECISIONS；无 ghost 依赖 | §3.1 | [x] |
| A2 | review-only | ponytail-review：db/ core/ storage/ 全 diff | — | — | Lean 或列 §4.3 | §3.2 | [x] |
| A3 | static | 威胁面；`rg -i "password|secret|api_key" backend/app/`；SQL 注入点（quote_ident / migrate SQL） | local | 无写 | 无 P0/P1 | §3.3 | [ ] |
| A4 | review-only | code-review-and-quality：migrate connection write_manager raw_store resource_guard | — | — | 无阻塞项 | §3.4 | [ ] |
| A5 | trace-ac | AC-1..8 ↔ §8/§9/§10；Execute 证据 1–5 分 | local | 无写 | 均 ≥4 | §3.5 | [ ] |
| A5 | cli-sandbox | **条件**：§10 B init_db 证据可疑时，`DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` 抽检 | audit-sandbox | 独立 DATA_ROOT | 与 Execute 声称一致 | §3.5 | [ ] |
| **A6** | — | **本任务跳过** — foundation 无 perf SLA（ResourceGuard 仅阈值读数） | — | — | N/A | §3.6 SKIP | [x] |
| A7 | cli-sandbox | `DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2；查 schema_version 幂等 | audit-sandbox | `.audit-sandbox/data` | 第二次 applied=[] | §3.7 | [ ] |
| A8 | pytest-isolated | `pytest tests/test_schema_migration.py -k checksum tests/test_write_manager.py -k own_transaction --basetemp=.audit-sandbox/pytest`；Red Flags :memory:/stub 弱断言 | audit-sandbox | tmp | 全绿或缺口入 §4.3 | §3.8 | [ ] |

---

## 3. 工具要求

### 3.0 7.pre（必做 · 已完成主会话刷新）

→ `research/gitnexus-audit-summary.md`

---

## 5. Audit DoD

- [x] 7.pre 产出已写入（GitNexus + CodeGraph CLI）
- [x] §2 各行已执行
- [ ] A9 §4 已写

---

## 6. 开场白

```text
Round 1 retrospective Audit：7.pre 已完成 → A1–A8（A6 SKIP）→ A9。
A7/A8/A5 抽检用 .audit-sandbox/data，禁止写 data/ Execute 证据库。
```
