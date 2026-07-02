# 执行索引 — R3-DCP-09 bounded backfill CI（Plan v4.1）

> Execute 首读：`research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                                                                                                  |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| slug          | `07-02-wave4-r3-dcp-09-backfill-ci`                                                                                                 |
| protocol      | `4.1`                                                                                                                               |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                                                                                                    |
| source_card   | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3_DCP_09_BOUNDED_BACKFILL_CI.md` |
| frozen_card   | `frozen/R3_DCP_09_BOUNDED_BACKFILL_CI.md`                                                                                           |

## 1. 步骤与证据（Execute）

| Step  | 切片  | RED / GREEN 证据                                |
| ----- | ----- | ----------------------------------------------- |
| [x] 1 | S00   | `research/execute-evidence/s00-{red,green}.txt` |
| [x] 2 | S01   | `s01-`                                          |
| [x] 3 | S02   | `s02-`                                          |
| [x] 4 | S03   | `s03-`                                          |
| [x] 5 | S04   | `s04-`                                          |
| [x] 6 | S05   | `s05-`                                          |
| [x] 7 | S06   | `s06-`                                          |
| 8     | Audit | `research/audit-a*-report.md`                   |

切片 AC SSOT：`research/to-issues-slices.md`

## 2. AC ↔ 测试

| AC                   | 验证                                                                    |
| -------------------- | ----------------------------------------------------------------------- |
| 有界 backfill CLI    | Execute 新建 test_qmd_data_backfill_cli · test_bounded_backfill_cli_e2e |
| backfill runner 回归 | test_sync_orchestrator -k backfill（已有）                              |
| isolated quick       | Execute 新建 quick profile 契约测                                       |
| nightly network      | `.github/workflows/nightly.yml` + Execute 新建 manifest 测              |
| live findings gate   | Execute 新建 findings severity 测                                       |
| 全量                 | `uv run pytest -q`                                                      |

## 2.1 台账 ↔ 切片

| 台账 ID                       | 切片 | 关账条件摘要                                       |
| ----------------------------- | ---- | -------------------------------------------------- |
| `WAVE3-ACC-OPT-01`            | S03  | `--quick` 跳过 `pytest_full`；quick <5min          |
| `ACC-LIVE-NETWORK-CI-001`     | S04  | nightly `pytest --run-network` batch275 子集绿     |
| `ACC-LIVE-ACCEPT-NIGHTLY-001` | S05  | live acceptance `--fail-on-severity HIGH,CRITICAL` |
| `LIVE-NETWORK-GATE-001`       | S04  | nightly workflow 接 `--run-network`（§4 交叉引用） |

## 3. 必须读原文（manifest）

| path                                                            | manifest  | for  |
| --------------------------------------------------------------- | --------- | ---- |
| `docs/decisions/ADR-030-bounded-backfill-cap-and-ci-nightly.md` | must-read | S00  |
| `R3_DCP_09_BOUNDED_BACKFILL_CI.md`                              | must-read | BOOT |
| `docs/modules/data_sync_orchestrator.md`                        | must-read | S00+ |

## 4. 已并入冻结任务卡

v4.1 薄指针 — 规格在 Execution Bundle。

## 5. Audit 追溯集

| 类别   | 文件                                      |
| ------ | ----------------------------------------- |
| frozen | `frozen/R3_DCP_09_BOUNDED_BACKFILL_CI.md` |
| entry  | `research/00-EXECUTION-ENTRY.md`          |
| index  | 本文件                                    |
| slices | `research/to-issues-slices.md`            |
