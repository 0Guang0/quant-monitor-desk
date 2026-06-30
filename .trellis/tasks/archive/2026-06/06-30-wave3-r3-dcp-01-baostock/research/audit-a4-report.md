# Audit A4 — 代码质量（R3-DCP-01 baostock incremental）

| 元信息   | 值                                                      |
| -------- | ------------------------------------------------------- |
| 维度     | A4 代码质量（`agents/code-reviewer.md`）                |
| 任务     | `06-30-wave3-r3-dcp-01-baostock` · debt-lite            |
| 活卡     | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`                     |
| 模板     | `agents/code-reviewer.md` + `audit-skill-paths.yaml` A4 |
| 审计日期 | 2026-06-30                                              |
| 模型     | composer-2.5                                            |
| worktree | `quant-monitor-desk-wt-dcp01`                           |
| 分支     | `feature/wave3-r3-dcp-01-baostock`                      |

---

## 维度证据 §3.4

### 变更范围（工作树 · 对照 `DEBT.plan.md`）

> `git diff master...HEAD` 无 delta（变更未 commit）；下列为 `git diff master -- <scope>` + 工作树审读。

| 文件                                                   | 变更                           | 轨 A 归属                   |
| ------------------------------------------------------ | ------------------------------ | --------------------------- |
| `backend/app/sync/watermark.py`                        | 新建                           | ✅                          |
| `backend/app/sync/runners.py`                          | `spec.date_*` → `FetchRequest` | ✅ L2 注入                  |
| `backend/app/datasources/fetch_ports/baostock_port.py` | 窗过滤                         | ✅                          |
| `backend/app/datasources/adapters/baostock.py`         | staging 手写插入               | ⚠️ 非金路径（见 A4-P2-004） |
| `backend/app/cli/data_commands.py`                     | `sync_baostock_incremental`    | ✅                          |
| `backend/app/cli/main.py`                              | 无 baostock 专属参数           | ⚠️ 见 A4-P2-003             |
| `tests/test_baostock_incremental_*.py`                 | S01–S04                        | ✅                          |
| `tests/test_qmd_data_sync_baostock.py`                 | S05 CLI                        | ✅                          |
| `tests/test_sync_runners.py`                           | runner 回归                    | ✅                          |

**未改 forbidden：** `orchestrator.py` 共享锁面 · `fred_port.py`。

### 金路径 / 无 adapter bypass（独立代码读）

| 检查项                                             | 结果     | 证据                                                                                                                                     |
| -------------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| CLI 真跑经 `DataSourceService` + `run_incremental` | **PASS** | `data_commands.py:195-225`：`create_baostock_fetch_port` → `DataSourceService` → `orch.run_incremental(..., datasource_service=service)` |
| 无 `adapter=` CLI bypass                           | **PASS** | `rg 'adapter=' backend/app/cli` → 0 命中                                                                                                 |
| Orchestrator 生产 guard                            | **PASS** | `orchestrator.py:187-194` `guard_production_datasource_service_required`                                                                 |
| Runner adapter bypass guard                        | **PASS** | `runners.py:422-426` `guard_runner_direct_adapter_bypass`                                                                                |
| E2E 与 CLI smoke 走同一 service 路径               | **PASS** | `test_baostock_incremental_e2e.py` · `test_qmd_data_sync_baostock.py` 均 `datasource_service`                                            |

### 逻辑正确性 vs AC（`prd.md` §5）

| AC / 检查项                          | 结果     | 证据                                                |
| ------------------------------------ | -------- | --------------------------------------------------- |
| watermark 空/有/边界日               | **PASS** | 4 个 watermark 单测绿；`date_start = max+1` 断言    |
| incremental E2E 写 `security_bar_1d` | **PASS** | `test_baostockIncremental_e2e_writesSecurityBar1d`  |
| 重复跑幂等                           | **PASS** | `test_baostockIncremental_repeatRun_noRowGrowth`    |
| caught-up（watermark==end）语义      | **FAIL** | 见 A4-P1-001                                        |
| CLI dry-run 可审计且无误导副作用     | **FAIL** | 窗字段有；但 dry-run 仍建库+migration，见 A4-P2-001 |
| CLI 输入错误可观测                   | **FAIL** | 非法 `end` 抛 `ValueError`，见 A4-P2-002            |

### 错误处理与 API 契约（DOUBT 对抗搜索）

| 范围                                   | 结论                                                                      |
| -------------------------------------- | ------------------------------------------------------------------------- |
| `compute_incremental_window` 全仓调用  | CLI `data_commands.py:152`、E2E、单测；**无** caught-up 守卫              |
| `IncrementalJobRunner.run` date 注入段 | **无** `date_start > date_end` 早退或 `ValueError`                        |
| `sync_baostock_incremental` 入参       | `end`/`since` `fromisoformat` 无 try/except → 非 `CliFailure`             |
| dry-run 分支                           | L139-145 在 L178 `if dry_run` **之前** 已 `writer()` + `apply_migrations` |
| `baostock_port._filter_bars_by_window` | 倒置 start/end 静默 `min/max` 归一化，无日志                              |
| `BaostockAdapter.fetch` 新增           | JSON/空 bars 静默退回；与 incremental 金路径分叉                          |

独立复验（2026-06-30）：

```text
compute_incremental_window(date(2026,6,30), end=date(2026,6,30))
→ date_start=2026-07-01, date_end=2026-06-30

sync_baostock_incremental(dry_run=True, end='not-a-date') → ValueError (非 CliFailure)

sync_baostock_incremental(dry_run=True, end='2024-06-30') → 创建 quant_monitor.duckdb
```

### 独立 pytest

```text
uv run pytest tests/test_baostock_incremental_watermark.py \
  tests/test_baostock_incremental_e2e.py \
  tests/test_qmd_data_sync_baostock.py \
  tests/test_sync_runners.py::test_incrementalRunner_injectsDateWindowIntoFetchRequest -q
→ 11 passed (2026-06-30)
```

靶向绿 **不** 抵消逻辑/契约缺口（对抗权威：验证只信代码+跑测，不信文档自述）。

### GitNexus

| 动作                                                                         | 结果                                                                                   |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `query("run_incremental datasource_service baostock incremental watermark")` | 命中 `DataSyncOrchestrator.run_incremental` · `DataSourceService.fetch` · batch_d 先例 |
| `watermark.py` / `sync_baostock_incremental`                                 | 索引未收录新符号（worktree 未 analyze，预期）                                          |

### A4 checklist（模板）

- [x] 无 P0 逻辑阻塞 merge 级（caught-up 为 P1 语义/契约）
- [ ] 错误处理可观测 — **FAIL**（非法日期、dry-run 副作用）
- [x] 风格与邻近模块大体一致（`live_fetch` 同构 guard 模式）
- [x] 测试五字段 docstring 齐全（靶向测已读）
- [x] 判定基于代码读 + pytest，非覆盖率 KPI

### 与 A1/A2/A3 交叉（本维独立 ID）

| 同源问题              | 他维 ID   | A4 视角                       |
| --------------------- | --------- | ----------------------------- |
| caught-up 倒置窗      | A1-P2-001 | 逻辑正确性 + runner 缺早退    |
| dry-run migration     | A3-P1-02  | API 契约与 payload 文案一致性 |
| CLI `--instrument-id` | A2-P2-003 | 公共 API 表面不完整           |
| canonical denylist    | A3-P1-01  | 本维不重复（归 A3 安全边界）  |

---

## §维度裁决

**FAIL**

（§计划内 4 行 + §计划外 2 行非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                            | 锚点                                                                   | 根因                                                                                                                                        | 修复方案                                                                                                                                                                                           | 验证                                                                                                                                                        |
| --------- | --- | ----------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A4-P1-001 | P1  | caught-up 时增量窗倒置且链路无 no-op 早退       | `watermark.py:64-65` · `runners.py:436-439` · `baostock_port.py:58-62` | `watermark >= end` 时 `date_start > date_end`；runner 仍注入 FetchRequest 并 fetch；port `min/max` 把窗扩回含 watermark 日                  | `compute_incremental_window` 在 `watermark is not None and watermark >= date_end` 返回空窗或 CLI/runner 检测 `date_start > date_end` 早退 COMPLETED no-op；port 对倒置窗返回空 bars 而非静默归一化 | 新增 watermark/runner caught-up 单测；`uv run pytest tests/test_baostock_incremental_watermark.py tests/test_baostock_incremental_e2e.py -q`                |
| A4-P2-001 | P2  | dry-run 声称无写库但实际 migration 副作用       | `data_commands.py:139-145,178-179` · `prd.md` AC「dry-run 可审计」     | DB 连接与 `apply_migrations` 在 `if dry_run` 之前执行；payload 写「no fetch or DB writes」与 DDL 矛盾                                       | dry-run 路径只读：DB 不存在时 `watermark=None` 纯计算窗；migration 移至 `dry_run=False` 或显式 `--init`                                                                                            | `test_qmdData_syncBaostock_dryRun_noDbFileCreated`：dry-run 前后 `tmp_path` 无 `.duckdb`；`uv run pytest tests/test_qmd_data_sync_baostock.py -k dryRun -q` |
| A4-P2-002 | P2  | CLI 非法日期/lookback 抛未处理 ValueError       | `data_commands.py:146-151,121`                                         | `date.fromisoformat(end[:10])` 与 `compute_incremental_window(..., empty_table_lookback_days=...)` 无边界包装为 `CliFailure(INVALID_INPUT)` | 用 try/except 捕获 `ValueError`，抛 `CliFailure(error_code="INVALID_INPUT", ...)` 与 `health_check` 先例一致                                                                                       | `pytest.raises(CliFailure)` 对 `end='not-a-date'`；`uv run pytest tests/test_qmd_data_sync_baostock.py -k invalidInput -q`                                  |
| A4-P2-003 | P2  | `main.py` sync 子命令未暴露 `instrument_id` API | `main.py:23-35` · `:128-136` · `data_commands.sync_plan`               | `sync_plan`/`sync_baostock_incremental` 支持 `instrument_id`，但 argparse 未注册、`_run_data` 未传入；公共 CLI 契约与库 API 不一致          | 增加 `--instrument-id` 并传入 `sync_plan`；help 补充 cn_equity watermark 语义                                                                                                                      | `uv run pytest tests/test_qmd_data_sync_baostock.py -q` 经 main/argparse 覆盖 `--instrument-id`                                                             |

金路径（`datasource_service` + 无 `adapter=`）、watermark 核心 happy-path、port 窗过滤、幂等 E2E 已 PASS，未列入表。

---

## 计划外发现

| ID        | P   | 标题                                           | 锚点                         | 根因                                                                                                                                           | 修复方案                                                                                               | 验证                                                                                                             |
| --------- | --- | ---------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| A4-P2-004 | P2  | `BaostockAdapter` staging 与 DCP-01 金路径分叉 | `adapters/baostock.py:17-61` | 增量 CLI/E2E 均走 `fetch_port`→`DataSourceService`；adapter 新增 `stg_foundation_smoke` 手写 DELETE/INSERT 未被本轨测覆盖，形成第二 staging 轨 | 删除本轨 adapter 变更（ponytail：incremental 不需要）或补 adapter 路径测并文档化何时用 adapter vs port | `rg 'BaostockAdapter' tests/test_*baostock*` 有意覆盖；`uv run pytest tests/test_baostock_incremental_e2e.py -q` |
| A4-P3-001 | P3  | `since` 被当作 `end_date` 回退语义含混         | `data_commands.py:148-149`   | `since` 与 `end` 互斥优先级未文档化；`since` 命名暗示下界却被用于上界                                                                          | 仅 `end` 驱动 `end_date`；`since` 映射 `date_start` 覆盖或弃用并更新 help                              | CLI 测断言 `since`/`end` 组合窗；`uv run pytest tests/test_qmd_data_sync_baostock.py -q`                         |

已对抗搜索：`watermark.py` · `runners.py` IncrementalJobRunner date 段 · `baostock_port.py` 窗过滤 · `data_commands.sync_baostock_incremental` 全函数 · `main.py` sync 参数表 · `adapters/baostock.py` diff · `rg adapter= backend/app/cli` · GitNexus query · 独立 Python 复验 caught-up / invalid date / dry-run 建库 · 靶向 pytest 11/11。
