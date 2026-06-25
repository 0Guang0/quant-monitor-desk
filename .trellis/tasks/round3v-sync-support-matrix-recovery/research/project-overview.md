# Project Overview — B3V-SYNC (GitNexus 1a)

## 模块

- **Sync**：`backend/app/sync/orchestrator.py` 门面；`runners.py` 增量/回填/对账；`jobs.py` 状态机
- **契约**：`specs/contracts/sync_job_contract.yaml`
- **写路径（只读）**：`WriteManager` + `SyncWritePipeline`；crash-window 在 runner _finalize 后

## 已实现 job 入口

| job_type | orchestrator 方法 | runner |
|----------|-------------------|--------|
| incremental | `run_incremental` | `IncrementalJobRunner` |
| backfill | `run_backfill` | `BackfillShardRunner` |
| reconcile | `run_reconcile` | `ReconcileJobRunner` |

## 预留 job

| job_type | 现状 |
|----------|------|
| full_load | `run_full_load` → `NotImplementedError` |
| data_quality | `run_data_quality` → `NotImplementedError` |
| revision_audit | 可 `create_job`，无 `run_revision_audit` |

## 影响面（Plan 预判）

- 改 `orchestrator` deferred 方法 → 更新 `test_r3x_residual_open_items_closure.py::test_advA3_016_*`
- 新增契约 loader/常量 → 新 parity 测试
- crash-window → 主要 `runners.py` 注入 hook + `test_sync_orchestrator.py`
