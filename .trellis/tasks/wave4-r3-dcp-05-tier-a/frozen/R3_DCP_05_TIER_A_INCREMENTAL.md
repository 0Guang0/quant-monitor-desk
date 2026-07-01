<!-- FROZEN: Plan protocol v4.1 · thin pointer · source: docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_05_TIER_A_INCREMENTAL.md · frozen_at: 2026-07-01T16:32:02Z -->

# FROZEN — R3-DCP-05 — Tier A 全源增量 + 产品真网 + 11/11 clean 写入

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **活卡（冻结时点）：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_05_TIER_A_INCREMENTAL.md`  
> **禁止：** 在此复制 `to-issues-slices.md` 或 `research/` 包正文

## 8. 边界 / 停止条件

见 `research/00-EXECUTION-ENTRY.md` §2 与活卡「不在范围」；偏离铁律即停。

## 9. 实现步骤

切片 AC 与步骤：`research/to-issues-slices.md`；RED/GREEN 与证据：`EXECUTION_INDEX.md` §1。

### 9.0 Boot

先 Read `research/00-EXECUTION-ENTRY.md` §5.2 + `EXTERNAL-INDEX.md` §A，再按 `to-issues-slices.md` 当前切片 § 执行。
