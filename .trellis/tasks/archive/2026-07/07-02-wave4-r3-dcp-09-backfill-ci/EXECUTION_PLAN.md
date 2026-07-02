# EXECUTION_PLAN — R3-DCP-09（薄指针）

> **Execute SSOT：** [`research/00-EXECUTION-ENTRY.md`](research/00-EXECUTION-ENTRY.md)  
> **切片 SSOT：** [`research/to-issues-slices.md`](research/to-issues-slices.md)  
> **活卡：** [`R3_DCP_09_BOUNDED_BACKFILL_CI.md`](../../docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_09_BOUNDED_BACKFILL_CI.md)

## GAP（仅列 Plan 与现状差）

1. 无 `qmd data backfill` CLI
2. 无 invocation-level `max_shards` cap contract
3. `wave3_isolated_production_acceptance.py` 无 `--quick`
4. 无 `.github/workflows/nightly.yml`
5. `wave3_live_production_acceptance.py` findings 未按 severity 硬门禁
6. 台账四 ID 未关账

## 下一步

1. `task.py freeze-task-card`（Plan 已做）
2. Execute S00 RED → GREEN
