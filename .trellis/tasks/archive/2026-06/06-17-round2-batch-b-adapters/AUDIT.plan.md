# Audit 计划 — Round 2 Batch B（013 adapter skeletons）

> **读者：** 主会话 + A1–A8 · v1.1（post 对抗审计 F20–F22）

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-b-adapters` |
| Execute prod-path | `QMD_DATA_ROOT` 默认 `<repo>/data` |
| Audit sandbox | `QMD_DATA_ROOT=.audit-sandbox/data` |

---

## 1. 维度 — Skill 冻结

| 维度 | Agent | Skill | 本任务 | 已执行 |
|------|-------|-------|--------|--------|
| A1 | audit-spec | trellis-check | 必做 | [x] |
| A2 | audit-ponytail | ponytail-review | 必做 | [x] |
| A3 | audit-security | security-and-hardening | 必做 | [x] |
| A4 | audit-quality | code-review-and-quality | 必做 | [x] |
| A5 | audit-completion | verification-before-completion | 必做 | [x] |
| A6 | — | — | **不用** SKIP | — |
| A7 | audit-ops | — | 必做 | [x] |
| A8 | audit-test-gap | — | 必做 | [x] |
| A9 | **主会话** | — | 必做 | [x] |

---

## 2. 维度验证矩阵

| 维 | 验证类型 | 命令 / 检查 | 环境 | 通过条件 | 已执行 |
|----|----------|-------------|------|----------|--------|
| A1 | read-only | trellis-check；diff vs check.jsonl + DECISIONS **§9 Batch B 偿还项** + remediation 表；GitNexus `create_adapter` | local | 无偏离；F01/F02 已偿还 | [x] |
| A2 | review-only | ponytail-review：`adapters/` | — | 无 bloat | [x] |
| A3 | static | grep WriteManager/requests/httpx in adapters/；无 secret | local | P0 清洁 | [x] |
| A4 | review-only | SkeletonAdapterBase + PortError 映射 | — | 模板 fetch 不变 | [x] |
| A5 trace-ac | trace-ac | AC-1..10 ↔ §8/§10；**audit-sandbox** 抽检：`pytest test_adapter_skeletons -k FileRegistry` + 读 `data/raw` 或 tmp 路径 | audit-sandbox | ≥4 分 | [x] |
| **A6** | — | **跳过** — skeleton 无 perf SLA | — | N/A | — |
| A7 | cli-sandbox | `QMD_DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2 + **ci_ingestion_smoke** | audit-sandbox | 幂等 | [x] |
| A8 | pytest-isolated | `pytest tests/test_adapter_skeletons.py --basetemp=.audit-sandbox/pytest`（**全文件**，非 -k 子集） | audit-sandbox | Red Flags 覆盖 | [x] |

### 2.2 A6 SKIP

Skeleton 层无 hot path；与 Batch A 同口径。

---

## 3. 7.pre

→ `research/gitnexus-audit-summary.md`；query `SkeletonAdapterBase` / `create_adapter`

---

## 4. 开场白

```text
Batch B Audit v1.1：7.pre → A1–A8（A6 SKIP）→ A9。
重点：FileRegistry 对齐、cninfo EMPTY、无 WriteManager、ci_ingestion_smoke、全量 adapter 测试。
```
