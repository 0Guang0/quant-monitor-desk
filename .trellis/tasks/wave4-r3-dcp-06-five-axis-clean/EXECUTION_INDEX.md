# 执行索引 — R3-DCP-06 Layer1 五轴真 clean（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                  |
| ------------- | ------------------------------------------------------------------- |
| slug          | `wave4-r3-dcp-06-five-axis-clean`                                   |
| protocol      | `4.1`                                                               |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                    |
| source_card   | `docs/implementation_tasks/.../R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md` |
| frozen_card   | `frozen/R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`                        |

## 1. 步骤与证据（Execute）

| Step | 切片    | 证据路径                                        |
| ---- | ------- | ----------------------------------------------- |
| 1    | S00     | `research/execute-evidence/s00-{red,green}.txt` |
| 2    | S01–S05 | `s01-` … `s05-`                                 |
| 3    | S06     | `s06-`                                          |
| 4    | Audit   | `research/audit-a*-report.md`                   |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC             | 验证                                                    |
| -------------- | ------------------------------------------------------- |
| 五轴 clean e2e | Execute 新建 test*layer1*\*\_clean_e2e 模块 ×5          |
| 五轴集成       | test_layer1_five_axis_panel_clean_smoke（Execute 新建） |
| §3.5.1         | 路线图清单 + S06 证据                                   |
| 全量           | uv run pytest -q                                        |

## 3. 必须读原文（manifest）

| path                                                          | manifest  | for  |
| ------------------------------------------------------------- | --------- | ---- |
| `docs/decisions/ADR-029-dcp06-layer1-five-axis-clean-read.md` | must-read | S00+ |
| `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`                         | must-read | BOOT |
| `docs/modules/layer1_global_regime_panel.md`                  | must-read | S00+ |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                                         |
| ------ | -------------------------------------------- |
| frozen | `frozen/R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`             |
| index  | 本文件                                       |
| slices | `research/to-issues-slices.md`               |
