# 来源索引 — B3V-SYNC Sync Support Matrix

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段 | 值 |
|------|-----|
| Round / Batch | Round 3V · `BATCH_3V_VERIFIED_AUDIT_CLEANUP` |
| Item ID | B3V-C04 / Playbook B3V-SYNC |
| 任务卡 | `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_04_sync_job_support_and_recovery.md` |
| Batch 地图 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` · `R3V-B02-SYNC-01/02` |
| 分支 | `fix/round3v-sync-support-matrix-recovery` |
| Worktree | `../quant-monitor-desk-wt-b3v-sync` |

### AC 映射 → MASTER §4

| 任务卡 | MASTER AC | 验证链 |
|--------|-----------|--------|
| §2 VR-SYNC-002 | AC-SYNC-002 | §9.1–9.3 |
| §2 VR-SYNC-001 | AC-SYNC-001 | §9.5–9.6 |
| §6 测试 | AC-SYNC-TEST | §5 + §10 |
| §8 Done | AC-SYNC-CLOSE | §9.6 + registry delta |
| Playbook §8.4 | AC-SYNC-PLAYBOOK | §10 |

### 路径纠偏

| 原引用 | 纠偏 |
|--------|------|
| `tests/test_sync_runners.py` | **不存在** → `tests/test_sync_orchestrator.py` |
| `docs/modules/sync_jobs.md` | **不存在** → 契约 YAML + `docs/modules/data_sync_orchestrator.md`（若存在则只读对照） |

---

## B. 输入 manifest

| 路径 | 类别 | manifest | extract / for |
|------|------|----------|---------------|
| `B02_04_sync_job_support_and_recovery.md` | 任务卡 | required | Plan AC |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` | 协调 | required | §3.1+§3.5+§4 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` | 协调 | required | 依赖/锁 |
| `BATCH_3V_HARDENING_RULES.md` | 审计 | required | §1.5 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | 审计 | required | VR 路由 |
| `specs/contracts/sync_job_contract.yaml` | 契约 | required | SYNC-01 |
| `specs/contracts/write_contract.yaml` | 契约 | read-only | SYNC-05 只读 |
| `backend/app/sync/orchestrator.py` | 接线 | inherited | §9.2–9.3 |
| `backend/app/sync/runners.py` | 接线 | inherited | §9.5 |
| `backend/app/db/write_manager.py` | 接线 | read-only | §9.5 |
| `docs/decisions/ADR-001-*.md` | 决策 | required | SYNC-05 |
| `tests/test_sync_orchestrator.py` | 测试 | deferred | §5.1 |
| `tests/test_r3x_residual_open_items_closure.py` | 测试 | deferred | §9.4 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | registry | read-only | SYNC-04 proposed delta |

---

## C. 六类覆盖自检

| 类别 | 路径 | [x] |
|------|------|-----|
| 决策 | `ADR-001` · `BATCH_3V_HARDENING_RULES.md` | [x] |
| 规则 | `GLOBAL_*.md` ×3 | [x] |
| 架构 | `MIGRATION_MAP.md` · `authority_graph.yaml` | [x] |
| 需求 | `B02_04` + MASTER §3 | [x] |
| 契约 | `sync_job_contract.yaml` · `write_contract.yaml`（只读） | [x] |
| 接线 | orchestrator / runners / write_manager（只读） | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
