# Audit A5 — 验收 / 完成度（R3-DCP-01 baostock incremental）

| 字段            | 值                                                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 维度            | A5 verification / completion                                                                                             |
| 任务            | `.trellis/tasks/06-30-wave3-r3-dcp-01-baostock`                                                                          |
| 活卡            | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md` §5                                                                                   |
| 分支 / worktree | `feature/wave3-r3-dcp-01-baostock` · `quant-monitor-desk-wt-dcp01`                                                       |
| 协议            | debt-lite · `DEBT.plan.md` 切片 S01–S06                                                                                  |
| 审计日期        | 2026-06-30                                                                                                               |
| GitNexus        | MCP `context`/`query` 未索引 `watermark.py` 新符号；已用 Execute 摘要 `gitnexus-execute-summary.md` + 仓库 `grep` 补追溯 |

---

## 维度证据

### 1. 独立复验（Audit 必做）

| 命令                                                                                                                                                                   | exit  | 结果                                                                       |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------------------------------------------------------------------------- |
| `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py tests/test_sync_runners.py -q` | **0** | **12 passed**                                                              |
| `uv run pytest tests/test_baostock_incremental_e2e.py tests/test_qmd_data_sync_baostock.py -q`（DEBT merge gate 弱行）                                                 | **0** | **6 passed**                                                               |
| `uv run pytest -q`（活卡 §5 末条 AC）                                                                                                                                  | **1** | 2 failed：`test_batch25_production_data_gate` ×2（canonical `data/` 污染） |

靶向套件与 Execute `slice-status.md` 声称的 12 passed **一致**。全量 pytest **不满足**活卡 `uv run pytest -q exit 0`。

### 2. execute-evidence 交叉验证

| 声称（`slice-status.md`）                        | 磁盘实查                                               | 交叉验证                            |
| ------------------------------------------------ | ------------------------------------------------------ | ----------------------------------- |
| `research/execute-evidence/s01-s05-green.txt`    | **不存在**（`execute-evidence/` 仅 `slice-status.md`） | **无法**对照 txt 与独立 pytest 输出 |
| DEBT.plan 各片 `s01-green.txt` … `s05-green.txt` | **均不存在**                                           | RED→GREEN 文本证据链断裂            |
| 靶向 12 passed                                   | 独立复跑 12 passed                                     | **一致**（仅 pytest 侧可验证）      |

### 3. 活卡 §5 AC → 测试五字段 → 实现追溯

| 活卡 AC                                | 评分          | 测试（五字段 docstring）                                                                                                           | 实现锚点                                                                                       | 备注                                                                      |
| -------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| watermark 单测：空表 / 有数据 / 边界日 | **5**         | `test_watermark_emptyTable_*` · `test_watermark_withData_*` · `test_watermark_boundaryDay_*` · `test_watermark_instrumentFilter_*` | `backend/app/sync/watermark.py` `read_bar_trade_date_watermark` · `compute_incremental_window` | 边界 `max=2026-06-28` → `date_start=2026-06-29` 已断言                    |
| incremental 集成测（replay / 隔离库）  | **5**         | `test_baostockIncremental_e2e_writesSecurityBar1d` · `test_baostockPort_replayFiltersByFetchWindow`                                | `DataSyncOrchestrator.run_incremental` + `DataSourceService` + `baostock_port` mock/replay     | `tmp_path` 隔离 DB；`ResourceGuard` monkeypatch                           |
| 重复跑行数不增（幂等）                 | **5**         | `test_baostockIncremental_repeatRun_noRowGrowth`                                                                                   | `write_mode=upsert_by_pk` · PK `(instrument_id, trade_date, adjustment_type)`                  | 两次 COMPLETED；`COUNT(*)==2`                                             |
| CLI help + dry-run 可审计              | **4**         | `test_qmdData_syncBaostock_dryRun_*` · `test_qmdData_syncPlan_cnEquity_*`                                                          | `data_commands.sync_baostock_incremental` · `cli/main.py` parser `help=`                       | dry-run payload 含 watermark/window/clean_table；**无** `--help` 自动化测 |
| Plan 调研 L1/L2/L3                     | **5**（文档） | —                                                                                                                                  | `research/reference-adoption-dcp01.md` §L1/L2/L3 总表                                          | Plan 交付物存在                                                           |
| Audit A1–A8 + Repair ledger            | —             | —                                                                                                                                  | —                                                                                              | 本维外；A1–A3 已落盘                                                      |
| `uv run pytest -q` exit 0              | **1**         | —                                                                                                                                  | —                                                                                              | **未满足**（见 §计划内 A5-P1-001）                                        |

**S02 接线（DEBT S02）：** `test_incrementalRunner_injectsDateWindowIntoFetchRequest`（五字段）→ `IncrementalJobRunner` 将 `spec.date_*` 注入 `FetchRequest.start_time/end_time`（`runners.py`）。

### 4. 边界用例核对

| 场景                    | 测试                                                                                          | 独立复验 |
| ----------------------- | --------------------------------------------------------------------------------------------- | -------- |
| 空 watermark + lookback | `test_watermark_emptyTable_returnsNullAndLookbackWindow`                                      | pass     |
| max+1 日窗              | `test_watermark_withData_returnsMaxPlusOne` · `test_watermark_boundaryDay_startIsDayAfterMax` | pass     |
| 幂等重跑                | `test_baostockIncremental_repeatRun_noRowGrowth`                                              | pass     |

### 5. 五字段 docstring（AUDIT.plan A5）

本轨**新增** `test_*`（11 个）：`test_baostock_incremental_watermark.py`×4 · `test_baostock_incremental_e2e.py`×3 · `test_qmd_data_sync_baostock.py`×3 · `test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest`×1 — 均含「覆盖范围 / 测试对象 / 目的/目标 / 验证点 / 失败含义」。

`tests/test_catalog.yaml` 已登记：`test_baostock_incremental_watermark.py` · `test_baostock_incremental_e2e.py` · `test_qmd_data_sync_baostock.py` · `test_sync_runners.py`。

### 6. diff / scope（silent 扩大）

未提交变更集中在 DEBT.plan allowed 组：`watermark.py`（新）· `runners.py` · `data_commands.py` · `baostock_port.py` · `adapters/baostock.py` · 本轨 `test_*` · `test_catalog.yaml`。未见 `fred_port` / `orchestrator.py` 大改。与切片 scope **对齐**。

### 7. GitNexus

- `query("baostock incremental watermark sync")`（project MCP）：返回通用 orchestration 流程，**未**命中新建 `watermark.py` 符号（索引滞后）。
- `context(read_bar_trade_date_watermark)` / `context(compute_incremental_window)`：**Symbol not found**。
- Execute 阶段 `research/gitnexus-execute-summary.md` 记录 `IncrementalJobRunner` impact **LOW**；本审计以代码 + pytest 为准。

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                  | 锚点                                                         | 根因                                                                                                                                               | 修复方案                                                                                                             | 验证                                                                                     |
| --------- | --- | ------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| A5-P1-001 | P1  | 活卡全量 pytest AC 未绿               | 活卡 §5 `uv run pytest -q exit 0` · `slice-status.md` L22–24 | canonical `data/duckdb/quant_monitor.duckdb` 含 `fetch_log` 残留；`data/raw` 含无 `source_used` 的 baostock 写入（Execute 自述为未隔离 CLI smoke） | 清理 canonical `data/` 污染；确保所有真跑路径强制 `QMD_DATA_ROOT` 隔离；复跑全量                                     | `uv run pytest -q` exit 0                                                                |
| A5-P2-001 | P2  | execute-evidence txt 缺失无法交叉验证 | `DEBT.plan.md` S01–S05 Evidence 列 · `slice-status.md` L5    | Execute 登记 `s01-s05-green.txt` 但未落盘；RED→GREEN 文本证据链断裂                                                                                | 补写各片 `research/execute-evidence/s0N-green.txt`（含 pytest 命令 + exit 0 摘要）或更正 `slice-status` 并附等效证据 | `glob research/execute-evidence/s*-green.txt` 非空；内容与独立 `uv run pytest … -q` 一致 |

---

## 计划外发现

| ID        | P   | 标题                               | 锚点                                               | 根因                                               | 修复方案                                                                          | 验证                                                    |
| --------- | --- | ---------------------------------- | -------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- |
| A5-P3-001 | P3  | CLI `--help` 无自动化覆盖          | 活卡 §5「CLI help + dry-run」· `cli/main.py:23-24` | parser `help=` 存在但未测；仅 dry-run payload 有测 | 增 `test_qmdData_sync_help_*` 断言 `qmd data sync --help` 含 domain/ dry-run 说明 | `uv run pytest tests/test_qmd_data_sync_baostock.py -q` |
| A5-P3-002 | P3  | GitNexus 索引未含 watermark 新符号 | `backend/app/sync/watermark.py`                    | 索引滞后于 worktree 未提交新文件                   | merge 后 `node .gitnexus/run.cjs analyze`                                         | `context(compute_incremental_window)` 可解析            |

已对抗搜索：`execute-evidence/` 全目录 · 活卡 §5 全条 AC · 靶向/全量 pytest · `test_catalog.yaml` baostock 登记 · `data_commands.sync_baostock_incremental` 实现 · 边界三场景测试 · GitNexus query/context。
