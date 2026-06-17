# Audit 计划 — Round 2 Batch A（011+012）

> **读者：** 主会话 + A1–A8 · 必读本文 + `audit.jsonl` · 各维 **§2** · A5 读 MASTER **§2**

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-a-sources` |
| audit.jsonl | 第一条 = 本文件 |
| Execute prod-path | `QMD_DATA_ROOT` 未设时默认 `<repo>/data`（只读索引） |
| Audit sandbox | `QMD_DATA_ROOT=.audit-sandbox/data` |

**编排：** 7.pre → 7.0 汇总 §2 → A1–A8 执行 §2 → A9 主会话 §4。

---

## 1. 维度 — Agent — Skill 冻结清单

| 维度 | Agent ID | 执行者 | Skill | 本任务 | GitNexus | `@` 指令 | 产出 | 已执行 |
|------|----------|--------|-------|--------|----------|----------|------|--------|
| A1 | audit-spec | 子 agent | trellis-check | 必做 | 必用 | 执行 §2 A1 | §3.1 | [x] |
| A2 | audit-ponytail | 子 agent | ponytail-review | 必做 | 建议 | 执行 §2 A2 | §3.2 | [x] |
| A3 | audit-security | 子 agent | security-and-hardening | 必做 | 必用 | 执行 §2 A3 | §3.3 | [x] |
| A4 | audit-quality | 子 agent | code-review-and-quality | 必做 | 建议 | 执行 §2 A4 | §3.4 | [x] |
| A5 | audit-completion | 子 agent | verification-before-completion | 必做 | 必用 | 执行 §2 A5 | §3.5 | [x] |
| A6 | audit-perf | 子 agent | — | **不用** | — | §2.2 已跳过 | §3.6 | — |
| A7 | audit-ops | 子 agent | — | 必做 | 必用 | 执行 §2 A7 | §3.7 | [x] |
| A8 | audit-test-gap | 子 agent | — | 必做 | 必用 | 执行 §2 A8 | §3.8 | [x] |
| **A9** | **—** | **主会话** | — | 必做 | 已刷新 | 汇总 §4 | §4 | [x] |

---

## 2. 维度验证矩阵（Batch A 已任务化）

| 维 | 验证类型 | 命令 / 检查 | 环境 | 隔离策略 | 通过条件 | 证据 → | 已执行 |
|----|----------|-------------|------|----------|----------|--------|--------|
| A1 | read-only | trellis-check；diff vs check.jsonl + DECISIONS §4；GitNexus query `SourceRegistry` 依赖 | local | 无写 | 无未授权 spec 偏离 | §3.1 | [x] |
| A2 | review-only | ponytail-review：`backend/app/datasources/` diff | — | — | 无必删 bloat 或已列 §4.3 | §3.2 | [x] |
| A3 | static | `grep -riE "WriteManager|write_manager" backend/app/datasources/`（期望无输出）；YAML 路径穿越；SQL 标识符 | local | 无写 | Adapter 不写 clean；无 P0 注入 | §3.3 | [x] |
| A4 | review-only | code-review-and-quality：registry + base_adapter + fetch_log | — | — | 模板方法保证 log 不变量 | §3.4 | [x] |
| A5 | trace-ac | AC-1..8 ↔ §8/§9/§10 验证链；证据 1–5 分 | local | 无写 | 均 ≥4 | §3.5 | [x] |
| **A6** | — | **本任务跳过** — 源注册/契约层无 hot path SLA | — | — | N/A | §3.6 SKIP | — |
| A7 | cli-sandbox | `QMD_DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2；`SHOW TABLES` 含 source_registry/fetch_log | audit-sandbox | `.audit-sandbox/data` | 幂等；003 存在 | §3.7 | [x] |
| A8 | pytest-isolated | `pytest tests/test_source_registry.py tests/test_data_adapter_contract.py -k "Legacy or NETWORK or disabled" --basetemp=.audit-sandbox/pytest` | audit-sandbox | tmp | Red Flags 有覆盖或列 §4.3 | §3.8 | [x] |

---

## 3. 工具要求

### 3.0 7.pre

→ `research/gitnexus-audit-summary.md`（Execute 交接后、派发 A1–A8 前）

### 3.1 各 agent

读 audit 摘要；跑 §2 本维；≥1 GitNexus query/context on `BaseDataAdapter` / `apply_migrations`。

---

## 4. 验收汇总（7.0）

→ `audit.report.md` §2

---

## 5. Audit DoD

- [x] 7.pre 完成
- [x] §2 各行（A6 SKIP 除外）已执行
- [x] A9 §4 已写

---

## 6. 开场白

```text
Round 2 Batch A Audit：7.pre → A1–A8 按 §2（A6 SKIP）→ A9。
不复跑 MASTER §10 全表；A7/A8 用 .audit-sandbox/。
重点：LegacyRoleError、fetch 失败仍 log、Adapter 不写 clean。
```
