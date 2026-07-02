<!-- FROZEN: Plan protocol v4.1 · thin pointer · source: docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md · frozen_at: 2026-07-02T09:23:09Z -->

# FROZEN — R3-DCP-08 — Layer4 市场结构 + US 日历绑真源（最小竖切）

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **活卡（冻结时点）：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`  
> **禁止：** 在此复制 `to-issues-slices.md` 或 `research/` 包正文

## 8. 边界 / 停止条件

见 `research/00-EXECUTION-ENTRY.md` §2 与活卡「不在范围」；偏离铁律即停。

## 9. 实现步骤

切片 AC 与步骤：`research/to-issues-slices.md`；RED/GREEN 与证据：`EXECUTION_INDEX.md` §1。

### 9.0 Boot

先 Read `research/00-EXECUTION-ENTRY.md` §5.2 + `EXTERNAL-INDEX.md` §A，再按 `to-issues-slices.md` 当前切片 § 执行。

| 已执行 | [x] |

### 9.1 S08-READ..ADAPTER

`clean_read.py` + `USEquityCleanMarketAdapter` + `test_layer4_clean_read.py`

| 已执行 | [x] |

### 9.2 S08-BUILD..E2E

`MarketStructureBuilder.build(source_mode=tier_a_clean)` + `test_layer4_us_equity_clean_e2e.py`

| 已执行 | [x] |

### 9.3 S08-REG-\*

`registry_proposed_delta.yaml` + mootdx dry-run `selected_source_id` test + eastmoney taxonomy notes

| 已执行 | [x] |

### 9.4 S08-CLOSE

`loop_maintain` + `uv run pytest -q` + `validate-execute-handoff`

| 已执行 | [x] |
