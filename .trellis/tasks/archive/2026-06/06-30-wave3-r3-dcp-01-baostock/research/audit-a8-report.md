# Audit A8 — Test Gap / testing-guidelines（R3-DCP-01 baostock incremental）

| 元信息   | 值                                                                 |
| -------- | ------------------------------------------------------------------ |
| 维度     | A8（测试矩阵 / testing-guidelines / 对抗性边界）                   |
| 任务     | `06-30-wave3-r3-dcp-01-baostock` · debt-lite                       |
| 活卡     | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`                                |
| 模板     | `agents/qa-expert.md` + `AUDIT.plan.md` §A8                        |
| 审计日期 | 2026-06-30                                                         |
| 模型     | composer-2.5                                                       |
| worktree | `quant-monitor-desk-wt-dcp01` · `feature/wave3-r3-dcp-01-baostock` |

---

## 维度证据 §3.8

### A8 隔离 pytest（Audit 独立复跑）

```bash
uv run pytest tests/test_baostock_incremental_watermark.py \
  tests/test_baostock_incremental_e2e.py \
  tests/test_qmd_data_sync_baostock.py \
  -q --basetemp=.audit-sandbox/pytest
```

| 项                       | 结果                                                                              |
| ------------------------ | --------------------------------------------------------------------------------- |
| **退出码**               | `0`                                                                               |
| **用例数**               | **10 passed**（watermark 4 · e2e 3 · CLI 3）                                      |
| **环境**                 | `QMD_DATA_ROOT` 由测内 `tmp_path` monkeypatch；`--basetemp=.audit-sandbox/pytest` |
| **AUDIT.plan A8 三边界** | 空表 lookback · max+1 · 幂等双跑 — **均有独立断言且绿**                           |

> **关联回归（非本命令范围，已存在）：** `tests/test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest`（S02 L2 runner 窗注入）；靶向全量 11 passed（+ runner 1）。

### 五字段 docstring 合规（testing-guidelines §9.1）

| 检查项                                                                | 结果       |
| --------------------------------------------------------------------- | ---------- |
| 靶向三文件 `test_*` 函数数                                            | **10**     |
| AST 扫描五字段（覆盖范围 / 测试对象 / 目的·目标 / 验证点 / 失败含义） | **0 缺失** |
| 目的/目标、失败含义为通俗中文                                         | **PASS**   |

### AUDIT.plan §A8 / 活卡 §5 边界矩阵

| AC / 边界                       | 期望                                            | 测                                                                                            | 覆盖                     |
| ------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------ |
| 空表 lookback                   | `watermark is None` → `date_start = end - N`    | `test_watermark_emptyTable_returnsNullAndLookbackWindow`                                      | **是**                   |
| watermark +1                    | `max(trade_date)+1` 为窗起点                    | `test_watermark_withData_returnsMaxPlusOne` · `test_watermark_boundaryDay_startIsDayAfterMax` | **是**                   |
| 幂等双跑                        | 两次 COMPLETED，行数不增                        | `test_baostockIncremental_repeatRun_noRowGrowth`                                              | **是**                   |
| E2E 金路径写库                  | service + `run_incremental` → `security_bar_1d` | `test_baostockIncremental_e2e_writesSecurityBar1d`                                            | **是**                   |
| Port 窗过滤（L2）               | replay 按 `FetchRequest` 窗过滤                 | `test_baostockPort_replayFiltersByFetchWindow`                                                | **是**                   |
| CLI dry-run 审计                | 暴露 watermark / window                         | `test_qmdData_syncBaostock_dryRun_includesWatermarkWindow`                                    | **部分**（见 A8-P3-001） |
| CLI replay 真跑                 | 隔离库 COMPLETED + 落库                         | `test_qmdData_syncBaostock_nonDryRun_replaySmoke`                                             | **是**                   |
| CLI 路由                        | `cn_equity_daily_bar` → baostock 子路径         | `test_qmdData_syncPlan_cnEquity_routesToBaostockIncremental`                                  | **是**                   |
| instrument 过滤 watermark       | 单票 max 不受他票影响                           | `test_watermark_instrumentFilter_ignoresOtherSymbols`                                         | **是**                   |
| caught-up（`watermark >= end`） | 空窗 / no-op / 不重拉已落库日                   | **无**                                                                                        | **否**                   |
| CLI `--help` / main 入口        | 活卡 §5「CLI help + dry-run 可审计」            | **无**                                                                                        | **否**                   |

### reference-adoption 测试追溯（`research/reference-adoption-dcp01.md`）

| 等级 | 采纳项                           | L1/L2 先例测                                                                              | 本轨测                                                      | 覆盖     |
| ---- | -------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------- |
| L1   | 幂等增量                         | `test_batch_d_orchestration_flow.py::test_incrementalJob_repeatRun_noDuplicatePrimaryKey` | `test_baostockIncremental_repeatRun_noRowGrowth`            | **是**   |
| L1   | service E2E                      | `test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath`       | `test_baostockIncremental_e2e_writesSecurityBar1d`          | **是**   |
| L2   | `baostock_port` 窗过滤           | reference-adoption §C                                                                     | `test_baostockPort_replayFiltersByFetchWindow`              | **是**   |
| L2   | CLI `sync_baostock_incremental`  | reference-adoption §D · `live_fetch` 门禁模式                                             | `tests/test_qmd_data_sync_baostock.py`（直调 API，非 main） | **部分** |
| L2   | Runner `date_*` → `FetchRequest` | reference-adoption §B                                                                     | `test_incrementalRunner_injectsDateWindowIntoFetchRequest`  | **是**   |
| L2   | 生产码 L2 attribution 注释       | A2 口径（port/runners 块）                                                                | **不测注释**；A2 已报 `A2-P2-001`/`A2-P2-002`               | **交叉** |

**Execute 参考实读：** `research/execute-reference-read-evidence.md` 已闭合 R1/R2 + 仓内四文件；与 port/CLI 变更测试对齐，**无** runtime import 测（正确 defer）。

**test_catalog：** 已登记三模块（`tests/test_catalog.yaml`）；用户指令 defer coordinator — **本维不列为 finding**。

### GitNexus

| 检查项                                | 结果                                                                                                                             |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `query`                               | `baostock incremental watermark run_incremental tests` → 命中 `test_batch_d_orchestration_flow` · `test_vendor_fetch_e2e` 等先例 |
| `context(compute_incremental_window)` | 符号未入索引（worktree 新文件，预期）                                                                                            |

### 弱断言 / mock 边界（testing-guidelines §1–§3）

| 测                                                         | 评估                                                                             |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `test_baostockIncremental_e2e_writesSecurityBar1d`         | 语义断言 `COMPLETED` + `close==1405.0`；ResourceGuard mock 在系统边界 — **PASS** |
| `test_baostockIncremental_repeatRun_noRowGrowth`           | `COUNT(*)==2` — **PASS**                                                         |
| `test_baostockPort_replayFiltersByFetchWindow`             | `row_count` + bars 列表长度 — **PASS**                                           |
| `test_qmdData_syncBaostock_dryRun_includesWatermarkWindow` | `date_start` 仅 truthy，未断言空表 lookback 精确日 — **弱**（A8-P3-001）         |
| `test_qmdData_syncBaostock_nonDryRun_replaySmoke`          | `COUNT >= 1` + `COMPLETED` — **PASS**                                            |

### execute-evidence 交叉验证

| 项                                        | 结果                                                                       |
| ----------------------------------------- | -------------------------------------------------------------------------- |
| `research/execute-evidence/s0*-green.txt` | **目录内无 txt**；仅 `slice-status.md` 自述 12 passed                      |
| Audit 独立 pytest                         | **10 passed**（三增量模块），与 slice-status 子集一致                      |
| 全量 `uv run pytest -q`                   | slice-status 记 2 failed（canonical 污染，非靶向模块）— **不纳入本维裁决** |

---

## §维度裁决

**FAIL**

（§计划内 1 行 + §计划外 2 行非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                              | 锚点                                                                      | 根因                                                                                                                                                                      | 修复方案                                                                                                                                                     | 验证                                                    |
| --------- | --- | --------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| A8-P2-001 | P2  | 活卡 §5「CLI help」无 pytest 契约 | `tests/test_qmd_data_sync_baostock.py` · `backend/app/cli/main.py:23-136` | reference-adoption L2 要求 CLI 可审计；现有测仅直调 `data_commands.sync_*`，未覆盖 `qmd data sync --help` 或 argparse 暴露 `cn_equity_daily_bar` / `--instrument-id` 语义 | 新增测：`subprocess` 或 `main` 模块调用 `--help` 输出含 baostock/watermark 说明；或 `argparse` 构造验证 `--instrument-id` 传入 `sync_plan`（对齐 A2-P2-003） | `uv run pytest tests/test_qmd_data_sync_baostock.py -q` |

活卡 §5 其余 watermark / 幂等 / dry-run 字段在靶向测中已覆盖；AUDIT.plan A8 列三边界均已绿。

---

## 计划外发现

| ID        | P   | 标题                                       | 锚点                                                                                             | 根因                                                                                                                                                              | 修复方案                                                                                                          | 验证                                                                                                              |
| --------- | --- | ------------------------------------------ | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A8-P2-002 | P2  | caught-up 水位（`watermark >= end`）无单测 | `watermark.py:51-65` · `baostock_port.py:48-64`                                                  | `compute_incremental_window` 在 `watermark==end` 时 `date_start > date_end`；port `min/max` 归一化可能重拉已落库日；对抗复验与 A1 `A1-P2-001` 同源，**零** pytest | 新增 `test_watermark_caughtUp_*`：断言空窗或 `date_start > date_end`；可选 e2e no-op；runner/CLI 早退行为与测对齐 | `uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py -q`            |
| A8-P3-001 | P3  | CLI dry-run 对 `date_start` 弱断言         | `tests/test_qmd_data_sync_baostock.py::test_qmdData_syncBaostock_dryRun_includesWatermarkWindow` | `assert window["date_start"]` 仅 truthy；空表 30 日 lookback 精确值未验，回归时 lookback 算错仍可能绿                                                             | 空库 dry-run 断言 `window["date_start"] == "2024-06-01"`（`end=2024-06-30`, lookback=30）或等价语义断言           | `uv run pytest tests/test_qmd_data_sync_baostock.py::test_qmdData_syncBaostock_dryRun_includesWatermarkWindow -q` |

已对抗搜索：`tests/` grep `caught-up|caught_up|watermark >=` · `baostock` 模块 `--help`/`main` · `empty_table_lookback_days` 负向 · `adjustment_type` watermark 过滤 · `compute_incremental_window` 全仓调用 · GitNexus query · `reference-adoption-dcp01.md` L1/L2 表逐行对照 · A1/A2 已报项去重后补 caught-up/CLI help 测试视角。
