<!-- FROZEN: Plan protocol v4.1 · thin pointer · source: docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_09_BOUNDED_BACKFILL_CI.md · frozen_at: 2026-07-02T09:21:33Z -->

# FROZEN — R3-DCP-09 — 有界 backfill + 连网验收 CI 分层

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **活卡（冻结时点）：** `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_09_BOUNDED_BACKFILL_CI.md`  
> **禁止：** 在此复制 `to-issues-slices.md` 或 `research/` 包正文

## 8. 边界 / 停止条件

见 `research/00-EXECUTION-ENTRY.md` §2 与活卡「不在范围」；偏离铁律即停。

## 9. 实现步骤

切片 AC 与步骤：`research/to-issues-slices.md`；RED/GREEN 与证据：`EXECUTION_INDEX.md` §1。

| Step | 切片 | 说明                                |
| ---- | ---- | ----------------------------------- |
| 9.0  | Boot | ENTRY + reference read              |
| 9.1  | S00  | cap contract + plan_backfill_shards |
| 9.2  | S01  | qmd data backfill CLI               |
| 9.3  | S02  | replay e2e                          |
| 9.4  | S03  | isolated --quick                    |
| 9.5  | S04  | nightly workflow                    |
| 9.6  | S05  | live findings gate                  |
| 9.7  | S06  | registry + loop_maintain            |

### 9.0 Boot

| 已执行 | [x] |

### 9.1 S00-cap-contract

| 已执行 | [x] |

### 9.2 S01-cli-backfill

| 已执行 | [x] |

### 9.3 S02-backfill-e2e

| 已执行 | [x] |

### 9.4 S03-acc-quick

| 已执行 | [x] |

### 9.5 S04-ci-nightly

| 已执行 | [x] |

### 9.6 S05-live-gate

| 已执行 | [x] |

### 9.7 S06-registry

| 已执行 | [x] |

### 9.0 Boot（说明）

先 Read `research/00-EXECUTION-ENTRY.md` §5.2 + `EXTERNAL-INDEX.md` §A，再按 `to-issues-slices.md` 当前切片 § 执行。
