# Audit 计划 — B3V-DATA schema_hash fail-closed

| 字段 | 值 |
|------|-----|
| slug | `round3v-schema-hash-fail-closed` |
| audit.jsonl | 第一条 = 本文件 |

## 0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
|------|------|------|
| 原始任务卡 | `B02_02_schema_hash_fail_closed.md` | scope / AC |
| VR 索引 | `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR-DATA-001 |
| Batch | `BATCH_3V_HARDENING_RULES.md` | 禁措辞 / 边界 |
| source-index | `research/source-index.md` | 血缘 |
| integration-ledger | `research/integration-ledger.md` | packing |
| original-plan-trace | `research/original-plan-trace.md` | B02-DATA-05 deferred |

**必须读原文：** `B02_02` §6 测试 + §4 forbidden

## Audit Source Trace

| 类别 | 路径 | Audit 用途 |
|------|------|------------|
| 任务卡 | `B02_02_schema_hash_fail_closed.md` | A5 AC |
| MASTER | `MASTER.plan.md` §2 §5 §9 | A5 抽检 |
| diff | `validation_gate.py`, `skeleton_base.py`, contract md | A1/A4 |
| 测试 | §5.1 三文件 | A8 |
| adversarial | `BATCH_3V_ADVERSARIAL_AUDIT.md` B3V-AUD-05 | A2/A8 负向 |

## 1. 验证覆写

| 维 | 本任务 | 命令 / 检查 | 通过条件 |
|----|--------|-------------|----------|
| A3 | 必做 | diff 无 production clean write；无 live fetch 代码 | 零写库路径 |
| A6 | **SKIP** — 本地 schema 探测无 SLA 热点 | — | 记录 SKIP |
| A7 | 必做 | 无 migration / 无 registry 文件改动 | 零 schema/registry diff |
| A8 | 必做 | `uv run pytest tests/test_data_adapter_contract.py tests/test_db_validation_gate.py tests/test_adapter_skeletons.py -q --basetemp=.audit-sandbox/pytest` | exit 0 |

## 2. DoD

- [ ] A1–A8 报告 + `audit_matrix.json`
- [ ] 负向 gate 测试仍存在（B3V-AUD-05）
- [ ] PASS 前不 finish-work
- [ ] registry 闭合由主会话验证（非本 Audit 必达）
