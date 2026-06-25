# 来源索引 — B3F-SH Source Health & Quality Runners

> **Plan / Audit 读本文件** · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                                                                |
| ------------- | ------------------------------------------------------------------------------------------------- |
| Round / Batch | Round 3F · `BATCH_3F_BATCH6_DATA_GOVERNANCE` · Playbook `B3F-SH`                                  |
| 任务卡        | `docs/implementation_tasks/ROUND_3_BATCH6_DATA_GOVERNANCE/R3F_verified_audit_ops_perf_hygiene.md` |
| Roadmap       | `PROJECT_IMPLEMENTATION_ROADMAP.md` § Batch 3F.3 · `R3F-SH-01..07`                                |
| 分支          | `feature/round3-source-health-and-quality-runners`                                                |
| 前置          | `round3-readonly-data-health-v2`（DH2 只读基线）                                                  |

### AC 映射 → MASTER §2

| Roadmap ID | MASTER AC | 验证链 |
| ---------- | --------- | ------ |
| R3F-SH-01  | AC-SH-01  | §9.1   |
| R3F-SH-02  | AC-SH-02  | §9.2   |
| R3F-SH-03  | AC-SH-03  | §9.3   |
| R3F-SH-04  | AC-SH-04  | §9.4   |
| R3F-SH-05  | AC-SH-05  | §9.5   |
| R3F-SH-06  | AC-SH-06  | §9.6   |
| R3F-SH-07  | AC-SH-07  | §9.7   |

### 路径纠偏

| 声明                                  | 纠偏                                     |
| ------------------------------------- | ---------------------------------------- |
| `backend/app/db/migrations/**` 新 SQL | **B3F-MIG 独占** — SH-01 先 ADR/测试骨架 |
| DH2 `data_health.py` 只读 profile     | **禁止** 在此分支建 snapshot 表          |
| ResourceGuard / perf                  | **B3F-HYG** — 本任务只读                 |

---

## B. 输入 manifest（E1 · implement.jsonl 来源）

| 路径                                      | 类别     | manifest         | extract / for      |
| ----------------------------------------- | -------- | ---------------- | ------------------ |
| `R3F_verified_audit_ops_perf_hygiene.md`  | 任务卡   | required         | AC / VR-DATAHEALTH |
| `014_implement_data_sync_orchestrator.md` | 任务卡   | required         | runner 矩阵        |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`        | 协调     | required         | §2.5/§2.6/§3.5     |
| `BATCH_3F_HARDENING_RULES.md`             | rule     | required         | live/validation    |
| `fred_live_authorization_2026-06-25.yaml` | evidence | execute-required | AC-SH-06           |
| `backend/app/ops/data_health.py`          | wiring   | inherited        | DH2 只读基线       |
| `backend/app/sync/orchestrator.py`        | wiring   | execute-required | §9.2–9.3           |
| `tests/test_ops_data_health.py`           | 测试     | inherited        | §9.5               |
| `tests/test_sync_orchestrator.py`         | 测试     | inherited        | defer 基线         |
| `docs/schema/MIGRATION_008_PLAN.md`       | 架构     | deferred         | SH-01 只读         |

---

## C. 六类覆盖自检

| 类别 | 路径                                                        | [x] |
| ---- | ----------------------------------------------------------- | --- |
| 决策 | `BATCH_3F_HARDENING_RULES.md` · `MIGRATION_008_PLAN.md`     | [x] |
| 规则 | GLOBAL×4 · `production_live_pilot_policy.md`                | [x] |
| 架构 | `docs/modules/data_sources.md` §5.8                         | [x] |
| 需求 | R3F 任务卡 + MASTER §3                                      | [x] |
| 契约 | `ops_health_check_contract.yaml` · `sync_job_contract.yaml` | [x] |
| 接线 | `data_health.py` · `orchestrator.py`                        | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。

## E. implement.jsonl 槽位

1. `MASTER.plan.md` · 2. `context_pack.json` · 3. `trellis-execute/SKILL.md` · 4+ ledger `required`
