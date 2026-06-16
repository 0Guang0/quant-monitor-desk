# Audit 计划 — Round 0 脚手架（000–004 · retrospective）

> **读者：** 主会话 + A1–A8 · 必读本文 + `audit.jsonl` · 各维 **§2** · A5 读 MASTER **§2** · A1 读 `check.jsonl`

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round0-scaffold-audit` |
| audit.jsonl | 第一条 = 本文件 |
| Execute DATA_ROOT | N/A（无 DuckDB） |
| Audit sandbox | `.audit-sandbox/round0/` |

**编排：** 7.pre → 7.0 汇总 §2 → A1–A8 执行 §2 → A9 主会话 §4。

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

## 2. 维度验证矩阵（Round 0 · 非 MASTER §10 复跑）

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 证据 → | 已执行 |
|----|----------|-------------|------|----------|----------|--------|--------|
| A1 | read-only | trellis-check；对照 `check.jsonl`；GitNexus query `backend/app/main` 依赖链 vs implement.jsonl | local | 无写 | 无 spec 偏离；无 ghost 依赖 | §3.1 | [x] |
| A2 | review-only | ponytail-review：Round 0 产出（configs/ docs/ tests/ 骨架）；每项 Lxx + net lines | — | — | 无必删 bloat 或列 §4.3 | §3.2 | [x] |
| A3 | static | 威胁面；`rg -i "password|secret|api_key|token" configs/ backend/app/`；`.env.example` 无真实密钥 | local | 无写 | 无 P0/P1 | §3.3 | [ ] |
| A4 | review-only | code-review-and-quality：main.py config.py conftest + Round 0 tests | — | — | 无阻塞项 | §3.4 | [ ] |
| A5 | trace-ac | AC-1..5 ↔ §8/§9/§10；证据 1–5 分 | local | 无写 | 均 ≥4 | §3.5 | [ ] |
| **A6** | — | **本任务跳过** — 脚手架无 hot path/SLA | — | — | N/A | §3.6 SKIP | [x] |
| A7 | cli-sandbox | `python -m compileall backend scripts` ×2；`pytest tests/test_global_execution_rules.py tests/test_project_scaffold.py -q` @ `.audit-sandbox/round0`（仅读仓库，无 DATA_ROOT 写） | audit-sandbox | 独立工作目录标记 | 两次 compile 均 exit 0 | §3.7 | [ ] |
| A8 | pytest-isolated | `pytest tests/test_global_execution_rules.py tests/test_config_templates.py -q --basetemp=.audit-sandbox/round0/pytest`；查 Red Flag「只 assertNotNull」 | audit-sandbox | tmp | 全绿；无 tautological 唯一断言 | §3.8 | [ ] |

---

## 3. 工具要求

### 3.0 7.pre（必做 · 已完成主会话刷新）

→ `research/gitnexus-audit-summary.md`

### 3.1 各 agent

读 audit 摘要；跑 §2 本维；≥1 GitNexus/CodeGraph query。

---

## 5. Audit DoD

- [x] 7.pre 产出已写入（GitNexus + CodeGraph CLI）
- [x] §2 各行（A6 除外）已执行 + 证据
- [ ] A9 §4 已写

---

## 6. 开场白

```text
Round 0 retrospective Audit：7.pre 已完成 → 按 §2 派发 A1–A8（A6 SKIP）→ A9 汇总。
不复跑 MASTER §10 同行命令；A7/A8 用 .audit-sandbox/round0/。
```
