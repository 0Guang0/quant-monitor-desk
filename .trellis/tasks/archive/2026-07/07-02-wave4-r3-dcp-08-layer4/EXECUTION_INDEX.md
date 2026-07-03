# 执行索引 — R3-DCP-08 Layer4 US_EQ clean（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                                                                                      |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| slug          | `wave4-r3-dcp-08-layer4`                                                                                                                |
| protocol      | `4.1`                                                                                                                                   |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                                                                                        |
| P0 market_id  | `US_EQ`                                                                                                                                 |
| source_card   | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` |
| frozen_card   | `frozen/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`                                                                                           |

## 1. 步骤与证据（Execute · v4.1 code-first）

| Step | 切片              | 证据                                                                                                |
| ---- | ----------------- | --------------------------------------------------------------------------------------------------- |
| 1    | S08-BOOT          | `tests/layer4_clean_e2e_support.py` + `tests/test_catalog.yaml` [x]                                 |
| 2    | S08-READ..ADAPTER | `tests/test_layer4_clean_read.py` · `research/execute-evidence/s08-02-{red,green}.txt` [x]          |
| 3    | S08-BUILD..E2E    | `tests/test_layer4_us_equity_clean_e2e.py` · `research/execute-evidence/s08-06-{red,green}.txt` [x] |
| 4    | S08-REG-\*        | registry apply + `tests/test_qmd_data_sync_tier_a_router.py -k mootdx` · `s08-reg-*-green.txt` [x]  |
| 5    | S08-CLOSE         | `research/execute-evidence/s08-close-green.txt` [x]                                                 |
| 6    | Audit + Repair    | `research/audit-a*-report.md` · `audit.report.md` [x]                                               |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC                 | 验证                                                                                    |
| ------------------ | --------------------------------------------------------------------------------------- |
| US_EQ clean e2e    | `tests/test_layer4_us_equity_clean_e2e.py`                                              |
| 022 无回归         | `tests/test_layer4_market_structure.py`                                                 |
| mootdx dry-run     | `tests/test_qmd_data_sync_tier_a_router.py -k mootdx`                                   |
| eastmoney taxonomy | `tests/test_source_registry.py::test_sourceRegistry_eastmoney_accTaxonomy_notesPresent` |
| 全量               | `uv run pytest -q`                                                                      |

## 2.1 Tier 验证矩阵（Repair 复验）

| Tier              | 命令                                                                   | 用途                        |
| ----------------- | ---------------------------------------------------------------------- | --------------------------- |
| US_EQ clean e2e   | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q`            | P0 竖切闭环                 |
| Layer4 clean read | `uv run pytest tests/test_layer4_clean_read.py -q`                     | S08-READ/ADAPTER/BUILD 负向 |
| mootdx dry-run    | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` | ACC-MOOTDX                  |
| 全量              | `uv run pytest -q`                                                     | S08-CLOSE                   |

## 3. 必须读原文（manifest）

| path                                                       | manifest  | for            |
| ---------------------------------------------------------- | --------- | -------------- |
| `docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md`  | must-read | S08-E2E        |
| `docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md` | must-read | S08-READ       |
| `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`                     | must-read | BOOT           |
| `docs/modules/layer4_market_structure.md`                  | must-read | S08-READ       |
| `research/registry_proposed_delta.yaml`                    | must-read | S08-REG-MOOTDX |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别        | 文件                                          |
| ----------- | --------------------------------------------- |
| frozen      | `frozen/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` |
| entry       | `research/00-EXECUTION-ENTRY.md`              |
| index       | 本文件                                        |
| slices      | `research/to-issues-slices.md`                |
| integration | `research/integration-audit.md`               |
| audit plan  | `AUDIT.plan.md`                               |
