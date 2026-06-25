# Integration Ledger — B3F-SH

> Plan 5c · v3 context packing

## 打包策略

| 策略 | 含义 |
| ---- | ---- |
| inline | MASTER §0/§3 已摘要 |
| summary+pointer | MASTER 摘要 + 原稿 |
| pointer | implement extract/for 精读 |

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
| ------ | -------- | -------- | ------------- | --------------- | ----------- |
| `research/integration-ledger.md` | rule | inline | MASTER §0.3 | v3 boot routing | §9.0 |
| `docs/schema/MIGRATION_008_PLAN.md` | decision | summary+pointer | MASTER §1.6 | SH-01 MIG 协调 | AC-SH-01 |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` | rule | summary+pointer | MASTER §0 Batch 3F 边界 | §2.5/§2.6 文件锁 | 全 AC |
| `BATCH_3F_HARDENING_RULES.md` | rule | summary+pointer | MASTER §0 | live/validation 硬约束 | AC-SH-06/07 |
| `R3F_verified_audit_ops_perf_hygiene.md` | business | pointer | MASTER §2 | VR-DATAHEALTH-001 | AC-SH-05 |
| `014_implement_data_sync_orchestrator.md` | business | pointer | MASTER §2 | runner 矩阵 | AC-SH-02/03 |
| `docs/modules/data_sources.md` | architecture | pointer | MASTER §4 | snapshot 列定义 | AC-SH-01 |
| `backend/app/ops/data_health.py` | wiring | pointer | MASTER §4 | DH2 只读基线 | AC-SH-05 |
| `backend/app/sync/orchestrator.py` | wiring | inline | MASTER §4 | defer entrypoints（Execute 改；不进 implement） | §9.2–9.3 |
| `specs/contracts/ops_health_check_contract.yaml` | contract | pointer | MASTER §5 | health 契约 | AC-SH-01 |
| `specs/contracts/sync_job_contract.yaml` | contract | pointer | MASTER §5 | job types | AC-SH-02/03 |
| `fred_live_authorization_2026-06-25.yaml` | evidence | pointer | MASTER §9.6 | FRED live caps | AC-SH-06 |
| `docs/quality/batch3f_fred_live_pilot_authorization_2026-06-25.md` | rule | summary+pointer | MASTER §0 | 用户授权记录 | AC-SH-06 |
| `tests/test_ops_data_health.py` | wiring | pointer | MASTER §5 | DH2 回归 | §9.5 |

## inline 清单

- §0 B3F-SH owns / must-not + MIG 协调
- §3.2 defer：migrations SQL → B3F-MIG；registry commit → 主会话
- SH-06 强制引用授权 YAML 路径
