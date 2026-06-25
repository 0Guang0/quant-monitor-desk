# 来源索引 — B3F-BR Backfill/Reconcile Parity

> Plan / Audit 读本文件 · Execute 只读 `implement.jsonl` + `context_pack.json`

---

## A. 血缘追溯

| 字段          | 值                                                               |
| ------------- | ---------------------------------------------------------------- |
| Round / Batch | Round 3F · `BATCH_3F_BATCH6_DATA_GOVERNANCE`                     |
| Item ID       | B3F-BR / Playbook §3.6                                           |
| Roadmap       | `PROJECT_IMPLEMENTATION_ROADMAP.md` Batch 3F.4 · `R3F-BR-01..05` |
| 分支          | `feature/round3-backfill-reconcile-parity`                       |
| Worktree      | `../quant-monitor-desk-wt-b3f-br`                                |

### AC 映射 → MASTER §4

| Roadmap ID    | MASTER AC      | 验证链 |
| ------------- | -------------- | ------ |
| R3F-BR-01     | AC-BR-01       | §9.1   |
| R3F-BR-02     | AC-BR-02       | §9.2   |
| R3F-BR-03     | AC-BR-03       | §9.3   |
| R3F-BR-04     | AC-BR-04       | §9.4   |
| R3F-BR-05     | AC-BR-05       | §9.5   |
| Playbook §8.5 | AC-BR-PLAYBOOK | §10    |

### 路径纠偏

| 原引用              | 纠偏                                                                                |
| ------------------- | ----------------------------------------------------------------------------------- |
| 独立 backfill ADR   | **不存在** → registry + `test_sync_orchestrator` severeConflict 族 + closure pytest |
| `R3-PARTIAL-5` 实现 | **B3V 已闭合** → `R3F-BR-03` regression guard only                                  |

---

## B. 输入 manifest

| 路径                                              | 类别     | manifest  | extract / for    |
| ------------------------------------------------- | -------- | --------- | ---------------- |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`                | 协调     | required  | §3.6+§8.5        |
| `BATCH_3F_TASK_CARD_MANIFEST.md`                  | 协调     | required  | B3F-BR ownership |
| `BATCH_3F_HARDENING_RULES.md`                     | 审计     | required  | §1.5             |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`               | 需求     | required  | R3F-BR-01..05    |
| `specs/contracts/sync_job_contract.yaml`          | 契约     | required  | BR-04 matrix     |
| `backend/app/sync/orchestrator.py`                | 接线     | deferred  | BR-04            |
| `backend/app/sync/runners.py`                     | 接线     | inherited | BR-04/§8.5       |
| `docs/adr/ADR-023-layer5-conflict-review-path.md` | 决策     | required  | BR-05            |
| `016_implement_source_conflict_validator.md`      | 需求     | required  | BR-02 reconcile  |
| `tests/test_r3f_br_backfill_reconcile_closure.py` | 测试     | deferred  | §5.1             |
| `tests/test_sync_runners.py`                      | 测试     | deferred  | §5.1             |
| `tests/test_sync_orchestrator.py`                 | 测试     | read-only | BR-01 anchor     |
| `tests/test_audit_remediation.py`                 | 测试     | read-only | BR-02 anchor     |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`              | registry | read-only | BR-03/05         |

---

## C. 六类覆盖自检

| 类别 | 路径                                        | [x] |
| ---- | ------------------------------------------- | --- |
| 决策 | `ADR-023` · `BATCH_3F_HARDENING_RULES.md`   | [x] |
| 规则 | `GLOBAL_*.md` ×3                            | [x] |
| 架构 | `MIGRATION_MAP.md` · `authority_graph.yaml` | [x] |
| 需求 | Roadmap 3F.4 + Playbook §3.6                | [x] |
| 契约 | `sync_job_contract.yaml`                    | [x] |
| 接线 | orchestrator / runners                      | [x] |

**索引完整**

---

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
