# 执行索引 — R3-DCP-07 Layer2 跨资产真 clean（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                              |
| ------------- | --------------------------------------------------------------- |
| slug          | `07-02-wave4-r3-dcp-07-layer2`                                  |
| protocol      | `4.1`                                                           |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                |
| source_card   | `docs/implementation_tasks/.../R3_DCP_07_LAYER2_CROSS_ASSET.md` |
| frozen_card   | `frozen/R3_DCP_07_LAYER2_CROSS_ASSET.md`                        |

## 1. 步骤与证据（Execute）

### 1.1 S00-CORE-READER

| 已执行 | [x] |

`Layer2CleanObservationReader` + `test_layer2_clean_reader.py`

### 1.2 S01-VIX-CLEAN-E2E

| 已执行 | [x] |

`tests/test_layer2_vix_clean_e2e.py`

### 1.3 S02-INTEGRATION

| 已执行 | [x] |

`audit-repair-ledger-s02.md` · ACC-LAYER L2 子集 · 全量 pytest

| Step | 切片  | 证据路径                              |
| ---- | ----- | ------------------------------------- |
| 1    | S00   | `test_layer2_clean_reader.py`         |
| 2    | S01   | `test_layer2_vix_clean_e2e.py`        |
| 3    | S02   | `research/audit-repair-ledger-s02.md` |
| 4    | Audit | `research/audit-a*-report.md`         |

切片 AC SSOT：`research/to-issues-slices.md`

## 2.1 复验命令（Repair / Audit 关账）

```bash
uv run pytest tests/test_layer2_sensor_loader.py -q
uv run pytest tests/test_layer2_vix_clean_e2e.py -q
uv run pytest -q
```

## 2. AC ↔ 测试

| AC                | 验证                                                            |
| ----------------- | --------------------------------------------------------------- |
| P0 clean snapshot | `test_layer2_vix_clean_e2e`（Execute 新建）                     |
| lineage           | `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes` 契约对齐 |
| ACC L2 子集       | S02 台账 + repair ledger                                        |
| 全量              | `uv run pytest -q`                                              |

## 3. 必须读原文（manifest）

| path                                                    | manifest  | for  |
| ------------------------------------------------------- | --------- | ---- |
| `docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md` | must-read | S00+ |
| `R3_DCP_07_LAYER2_CROSS_ASSET.md`                       | must-read | BOOT |
| `docs/modules/layer2_cross_asset_sensor.md`             | must-read | S00+ |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                                     |
| ------ | ---------------------------------------- |
| frozen | `frozen/R3_DCP_07_LAYER2_CROSS_ASSET.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`         |
| index  | 本文件                                   |
| slices | `research/to-issues-slices.md`           |
