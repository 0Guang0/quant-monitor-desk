# Context closure — B3F-BR backfill/reconcile parity

## Upstream wiring

- `specs/contracts/sync_job_contract.yaml` — IMPLEMENTED+RESERVED job matrix SSOT + `utility_operations`
- `backend/app/sync/orchestrator.py` — `OrchestratorJobHandler` + `orchestrator_handler_registry()`
- `backend/app/sync/runners.py` — Incremental/Backfill/Reconcile runners（只读锚定）
- `tests/test_sync_orchestrator.py` · `tests/test_audit_remediation.py` — backfill severeConflict / reconcile re-fetch 锚点
- `.trellis/tasks/round3v-sync-support-matrix-recovery/repair-evidence/sync-crash-window-runbook.md` — R3F-BR-03 handoff

## BR closure (branch)

- **R3F-BR-01:** backfill parity 叙事 + severeConflict pytest 锚点 — GREEN
- **R3F-BR-02:** reconcile re-fetch token 锚点 — GREEN
- **R3F-BR-03:** R3-PARTIAL-5 regression guard — GREEN
- **R3F-BR-04:** handler registry 超集 + runner 接线 — GREEN
- **R3F-BR-05:** ADR-023 + R3-PARTIAL-4 honest DEFERRED 链 — GREEN

## A7 运维/registry 矩阵（Repair 闭合 A7-BR-O1..O4）

| ID           | 发现                                                                      | 闭合                                                                                                                                                          |
| ------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A7-BR-O1** | Handler registry **仅元数据**，未接入动态 dispatch                        | **CLOSED** — `ORCHESTRATOR_HANDLER_REGISTRY` 供 ops/CLI 矩阵；实际路由仍走既有 `run_*`。B3F-CLI 接线前运维不得假设 registry 即调度器。                        |
| **A7-BR-O2** | `recover_stuck_writing_job` registry `kind=utility` 不在 `job_types`      | **CLOSED** — `sync_job_contract.yaml` 新增 `utility_operations`；`test_r3fBr07_*` 双向校验。                                                                  |
| **A7-BR-O3** | 全量 `pytest -q` 有 master 基线噪声                                       | **CLOSED** — BR 门禁为 Playbook §8.5 子集（含 closure）；全量结果见 `execute-evidence/8.5-playbook-full-pytest-repair.txt` 附注（既有债务，非本 diff 引入）。 |
| **A7-BR-O4** | `DataSourceService.fetch` 与 orchestrator `begin_fetching` 双 choke-point | **CLOSED** — 本分支未改；运维 RCA 须同时查 orchestrator 与 service 两层（pre-existing）。                                                                     |

## A3 ponytail（W-A3-01）

**W-A3-01:** `ReconcileJobRunner` 对 `compare_table` 使用 f-string DDL/DML（`runners.py`）；`conflict_id` 来自 `uuid.uuid4()` 前 8 位 hex，当前风险低。本分支 **不改** `runners.py`（B3F-BR 边界）；后续 hygiene slice 可改用 `quote_ident` 与 `source_conflict.py` 对齐。

## Deferred (unchanged)

- R3-PARTIAL-4 registry 主会话 RESOLVED 批改
- crash-window 新实现（B3V 已闭合，仅 regression guard）
- production write / live fetch
