# Repair Adversarial Review — R3-DCP-01 (post-P6)

> **复审员：** Repair Adversarial Review Agent  
> **日期：** 2026-06-30  
> **worktree：** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-dcp01`  
> **branch：** `feature/wave3-r3-dcp-01-baostock`  
> **原则：** 不信 ledger / `audit.report.md` §5 自述；以代码 + 独立 pytest 为准

---

## §裁决

**PASS**

Ledger RB-01..RB-13 根因修复经代码核对与独立跑测可复现；RB-14 阶段外置绑定合理；forbidden 路径相对 `master` diff 为空。

---

## 独立验证（本复审执行）

| 命令                                                                                                                                                                                                          | 结果                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py tests/test_sync_runners.py tests/test_baostock_adapter_staging.py -q` | exit 0（24 passed）                    |
| `uv run pytest -q`                                                                                                                                                                                            | exit 0（全量绿）                       |
| `python .trellis/scripts/task.py validate-repair-close .trellis/tasks/06-30-wave3-r3-dcp-01-baostock`                                                                                                         | exit 0 — `validate-repair-close: OK`   |
| `git diff master -- fred_port orchestrator migrations`                                                                                                                                                        | 空（无越界）                           |
| `uv run pytest tests/test_baostock_incremental_watermark.py -q`                                                                                                                                               | exit 0（6 passed，对照 s01-green.txt） |
| `uv run pytest tests/test_baostock_incremental_e2e.py::test_baostockIncremental_repeatRun_noRowGrowth -q`                                                                                                     | exit 0（对照 s04-green.txt）           |

---

## RB 逐项表

| ID        | Repair 声称                                                         | 独立结论         | 证据                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --------- | ------------------------------------------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RB-01** | caught-up 倒置窗 no-op（watermark · runner SKIPPED · port 空 bars） | **确认**         | `incremental_window_is_empty()`（`watermark.py:25-27`）；`IncrementalJobRunner.run` 倒置窗 → `SKIPPED`（`runners.py:441-455`）；`baostock_port._filter_bars_by_window` `start>end` → `[]`（`baostock_port.py:51-53`）；`test_watermark_caughtUp_windowIsEmpty` · `test_incrementalRunner_caughtUp_skipsFetch` · `test_baostockPort_invertedWindow_returnsEmptyBars` · `test_qmdData_syncBaostock_caughtUpDryRun` 均绿 |
| **RB-02** | dry-run 零 DB 写                                                    | **确认**         | `sync_baostock_incremental` dry-run 在 `db.is_file()` 前只读 watermark、230-232 行早退无 migration；`test_qmdData_syncBaostock_dryRun_noDbFileCreated` 绿                                                                                                                                                                                                                                                             |
| **RB-03** | canonical DB fail-closed                                            | **确认**         | 真跑路径 `assert_sandbox_db_allowed(db, no_production_mutation=True)`（`data_commands.py:236`）；`test_qmdData_syncBaostock_refusesCanonicalDbPath` 绿                                                                                                                                                                                                                                                                |
| **RB-04** | cn_equity 真跑须 operator / sandbox                                 | **确认**         | `_require_baostock_sync_operator_or_sandbox` 抛 `CliFailure(error_code="USER_AUTH_REQUIRED")`（`data_commands.py:128-137`）；独立复现非 sandbox `DATA_ROOT` → `error_code=USER_AUTH_REQUIRED`；`test_qmdData_syncBaostock_operatorAuthRequired` 绿                                                                                                                                                                    |
| **RB-05** | `--instrument-id` + help                                            | **确认**         | `main.py:35` `--instrument-id`；sync parser help 含 baostock watermark 说明（`main.py:23-28`）；`test_qmdData_syncCli_instrumentIdPassedToSyncPlan` 绿                                                                                                                                                                                                                                                                |
| **RB-06** | 非法日期包装 CliFailure                                             | **确认**         | `_parse_sync_date` → `INVALID_INPUT`（`data_commands.py:117-125`）；lookback `ValueError` 包装（192-197）；`test_qmdData_syncBaostock_invalidInputDates` 绿                                                                                                                                                                                                                                                           |
| **RB-07** | L2 attribution 注释                                                 | **确认**         | `runners.py:436` · `baostock_port.py:3-4,40` · `adapters/baostock.py:3-4` 含 `L2 (R3-DCP-01)`                                                                                                                                                                                                                                                                                                                         |
| **RB-08** | watermark SQL 纵深（quote_ident + allowlist）                       | **确认**         | `_BAR_CLEAN_TABLES` + `quote_ident`（`watermark.py:15,59`）；`test_watermark_cleanTableRejectsUnknownTable` 绿                                                                                                                                                                                                                                                                                                        |
| **RB-09** | adapter staging 分叉有测                                            | **确认**         | `tests/test_baostock_adapter_staging.py` 存在且绿；adapter L2 文档（`baostock.py:3-4`）                                                                                                                                                                                                                                                                                                                               |
| **RB-10** | since 语义 + `parse_fetch_window_date` SSOT                         | **确认**         | `since` 覆盖 `date_start`（`data_commands.py:199-205`）；`baostock_port` 无 `_parse_window_date`（rg 0 命中），统一 `parse_fetch_window_date`；`test_qmdData_syncBaostock_sinceOverridesDateStart` 绿                                                                                                                                                                                                                 |
| **RB-11** | 全量 pytest 绿                                                      | **确认**         | 本复审 `uv run pytest -q` exit 0                                                                                                                                                                                                                                                                                                                                                                                      |
| **RB-12** | execute-evidence s01–s05                                            | **确认**         | `research/execute-evidence/s01-green.txt` … `s05-green.txt` 存在；命令与独立复跑结果一致                                                                                                                                                                                                                                                                                                                              |
| **RB-13** | dry-run date_start 精确断言                                         | **确认**         | `test_qmdData_syncBaostock_dryRun_includesWatermarkWindow` 断言 `date_start=="2024-05-31"`（`test_qmd_data_sync_baostock.py:42`）绿                                                                                                                                                                                                                                                                                   |
| **RB-14** | GitNexus 索引滞后                                                   | **阶段外置合理** | `audit.report.md` §4.4 绑定 merge 后 `gitnexus analyze`；无代码依赖阻塞本轨关账                                                                                                                                                                                                                                                                                                                                       |

---

## 边界 / 质量核对

| 检查项                                                         | 结论                                                                             |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| forbidden（`fred_port` · `orchestrator.py` · `migrations/**`） | `git diff master` 空                                                             |
| 五字段 docstring（靶向 `test_*`）                              | AST 扫描 5 个 baostock 相关测文件：0 缺失                                        |
| 测试目的未削弱                                                 | 关键断言（caught-up SKIPPED、dry-run 无库、date_start 精确值、since 覆盖）均保留 |
| caught-up 真跑 CLI 早退                                        | `data_commands.py:257-260` 存在；dry-run + runner + port 三层已测，行为一致      |

---

## 可选观察（不阻塞 PASS）

| 项                                                     | 说明                                                                                                              |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| RB-04 测试未显式断言 `error_code`                      | `test_qmdData_syncBaostock_operatorAuthRequired` 仅 `match="operator"`；代码与独立复现已确认 `USER_AUTH_REQUIRED` |
| `test_incrementalRunner_caughtUp_skipsFetch` docstring | 文内「验证点」写 `COMPLETED`，实际断言 `SKIPPED`（与实现一致）；建议后续顺手改 docstring，非功能缺口              |

---

## 与 DCP-02 PASS bar 对照

仓库内尚无 DCP-02 `repair-adversarial-review.md` 可对照；本复审按模板 §核查清单同等标准执行：**根因代码核对 + 独立 pytest + forbidden diff 空 + validate-repair-close + evidence 可复现**。满足同等 bar。

---

## 新 findings（RBR）

无。§裁决 **PASS**，不派发 re-repair。

---

## 主会话建议

1. 可 merge `feature/wave3-r3-dcp-01-baostock`（RB-14：merge 后跑 `gitnexus analyze`）。
2. 可选：修正 `test_incrementalRunner_caughtUp_skipsFetch` docstring 中 status 表述为 `SKIPPED`。
