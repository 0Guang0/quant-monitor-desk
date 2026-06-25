# Audit 计划 — B3V-OPS Contract Drift

| 字段 | 值 |
| ---- | -- |
| slug | `round3v-contract-drift-write-modes` |
| audit.jsonl | 第一条 = 本文件 |

## 0.1 Trace Authority Set

| 类别 | 文件 | 用途 |
| ---- | ---- | ---- |
| 原始任务卡 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_01_contract_drift_and_write_modes.md` | scope / AC |
| Manifest | `BATCH_3V_TASK_CARD_MANIFEST.md` | C01 |
| Hardening | `BATCH_3V_HARDENING_RULES.md` | 禁措辞 |
| VR 索引 | `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR-OPS/WRITE |
| source-index | `research/source-index.md` | 血缘 |
| integration-ledger | `research/integration-ledger.md` | packing |

**必须读原文：** `B02_01_contract_drift_and_write_modes.md`

## Audit Source Trace

| 类别 | 路径 | Audit 用途 |
| ---- | ---- | ---------- |
| 任务卡 | `B02_01_contract_drift_and_write_modes.md` | A5 AC 对照 |
| MASTER | `MASTER.plan.md` §2 §5 §9 | A5 抽检 |
| diff | `db_inspector.py` · `write_contract.yaml` | A1/A4 |
| 测试 | `test_contract_drift_ops_write.py` · `test_ops_db_inspector.py` | A8 |
| hardening | `BATCH_3V_HARDENING_RULES.md` | A3 |

## 1. 验证覆写

| 维 | 本任务 | 命令 / 检查 | 通过条件 |
| -- | ------ | ----------- | -------- |
| A1 | 必做 | diff vs 任务卡 allowed/forbidden | 无 scope creep |
| A3 | 必做 | rg 本 diff 无 `INSERT`/`writer()` 于 db_inspector；无 production-live 措辞 | 只读 + 措辞 |
| A6 | **SKIP** — 无 SLA 热路径 | — | 记录 SKIP |
| A7 | 必做 | 无 migration 文件变更 | 零 schema |
| A8 | 必做 | `uv run pytest tests/test_contract_drift_ops_write.py tests/test_ops_db_inspector.py tests/test_write_manager.py -q --basetemp=.audit-sandbox/pytest` | exit 0 |

## 2. DoD

- [ ] A1–A8 报告
- [ ] 对抗性零 OPEN
- [ ] PASS 前不 finish-work
