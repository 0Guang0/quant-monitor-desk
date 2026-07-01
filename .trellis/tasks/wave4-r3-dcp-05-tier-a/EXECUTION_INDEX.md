# 执行索引 — R3-DCP-05 Tier A incremental（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                                                                                 |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| slug          | `wave4-r3-dcp-05-tier-a`                                                                                                           |
| protocol      | `4.1`                                                                                                                              |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                                                                                   |
| source_card   | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_05_TIER_A_INCREMENTAL.md` |
| frozen_card   | `frozen/R3_DCP_05_TIER_A_INCREMENTAL.md`                                                                                           |

## 1. 步骤与证据（Execute）

| Step | 切片    | 证据路径                                        |
| ---- | ------- | ----------------------------------------------- |
| 1    | S00     | `research/execute-evidence/s00-{red,green}.txt` |
| 2    | S01–S11 | `s01-` … `s11-`                                 |
| 3    | S12     | `s12-`                                          |
| 4    | S13     | `s13-`                                          |
| 5    | Audit   | `research/audit-a*-report.md`                   |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC              | 验证                                                             |
| --------------- | ---------------------------------------------------------------- |
| 11/11 clean e2e | 每源新建 e2e 测（先例 `tests/test_baostock_incremental_e2e.py`） |
| baostock live   | `tests/test_qmd_data_sync_baostock.py`                           |
| migration 015   | `tests/test_schema_migration.py`                                 |
| 全量            | `uv run pytest -q`                                               |

## 3. 必须读原文（manifest）

| path                                                            | manifest  | for  |
| --------------------------------------------------------------- | --------- | ---- |
| `docs/decisions/ADR-028-dcp05-tier-a-clean-domain-extension.md` | must-read | S00  |
| `R3_DCP_05_TIER_A_INCREMENTAL.md`                               | must-read | BOOT |
| `docs/modules/data_sync_orchestrator.md`                        | must-read | S00+ |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                                     |
| ------ | ---------------------------------------- |
| frozen | `frozen/R3_DCP_05_TIER_A_INCREMENTAL.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`         |
| index  | 本文件                                   |
| slices | `research/to-issues-slices.md`           |
