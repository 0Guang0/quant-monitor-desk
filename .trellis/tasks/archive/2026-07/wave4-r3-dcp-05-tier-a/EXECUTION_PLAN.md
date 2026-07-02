# EXECUTION_PLAN — R3-DCP-05（薄指针）

> **Execute SSOT：** [`research/00-EXECUTION-ENTRY.md`](research/00-EXECUTION-ENTRY.md)  
> **切片 SSOT：** [`research/to-issues-slices.md`](research/to-issues-slices.md)  
> **活卡：** [`R3_DCP_05_TIER_A_INCREMENTAL.md`](../../docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_05_TIER_A_INCREMENTAL.md)

## GAP（仅列 Plan 与现状差）

1. migration 015 未建
2. 9 个 Tier A 源缺 incremental ops/CLI（baostock/fred 仅有）
3. baostock sync `use_mock=True` 硬编码
4. `clean_write_targets` 未覆盖 ADR-028 全矩阵

## 下一步

1. `task.py freeze-task-card`
2. Execute S00 RED → GREEN
