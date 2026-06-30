# Audit A7 — ops/DB/CLI sandbox（R3-DCP-01 baostock incremental）

| 元信息   | 值                                                                 |
| -------- | ------------------------------------------------------------------ |
| 维度     | A7 ops/DB/CLI sandbox                                              |
| 任务     | `wave3-r3-dcp-01-baostock` · debt-lite                             |
| 活卡     | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`                                |
| 模板     | `agents/database-administrator.md` + `audit-skill-paths.yaml` A7   |
| 审计日期 | 2026-06-30                                                         |
| 模型     | composer-2.5                                                       |
| worktree | `quant-monitor-desk-wt-dcp01` · `feature/wave3-r3-dcp-01-baostock` |

---

## 维度证据 §3.7

### QMD_DATA_ROOT 隔离

| 步骤                          | 命令 / 动作                                                                                  | exit | 关键证据                                                                               |
| ----------------------------- | -------------------------------------------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------- |
| 配置解析                      | `backend/app/config.py` `DATA_ROOT = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")`      | —    | 未设 env 时回落 `data/`（canonical 风险，见 finding）                                  |
| CLI dry-run + sandbox         | `QMD_DATA_ROOT=<task>/.audit-sandbox/user-live` + `sync_baostock_incremental(dry_run=True)`  | 0    | `DATA_ROOT` 解析为 sandbox 绝对路径；`data/duckdb/quant_monitor.duckdb` mtime **不变** |
| 靶向 pytest                   | `uv run pytest tests/test_baostock_incremental_*.py tests/test_qmd_data_sync_baostock.py -q` | 0    | **10 passed**；CLI/E2E 测均 `monkeypatch.setenv("QMD_DATA_ROOT", tmp_path)`            |
| canonical 写保护（设 env 时） | dry-run 前后 canonical mtime 对比                                                            | —    | `canonical_before == canonical_after`（Audit 2026-06-30）                              |

### init/migrate 幂等（sandbox）

| 步骤           | 命令                                                                                                                        | exit | 关键证据                                                                    |
| -------------- | --------------------------------------------------------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------------- |
| init 第 1 次   | `QMD_DATA_ROOT=<sandbox/user-live> uv run python scripts/init_db.py --db <task>/.audit-sandbox/duckdb/quant_monitor.duckdb` | 0    | `applied ['001_foundation', …, '014_stg_bar_ohlcv']`（14 条）               |
| init 第 2 次   | 同上                                                                                                                        | 0    | `applied none (up to date)`                                                 |
| migration diff | `git diff master --name-only`                                                                                               | —    | **无** `backend/app/db/migrations/**` 变更（符合 `DEBT.plan.md` forbidden） |

### CLI dry-run / run sandbox 行为

| 步骤                 | 命令                                                                                                                     | exit | 关键证据                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `qmd data sync` 入口 | `python -m backend.app.cli.main data sync --domain cn_equity_daily_bar --end 2024-06-30`（`QMD_DATA_ROOT` 指向 sandbox） | 0    | JSON：`dry_run=true`，`window.date_start/end`，`watermark`，`clean_table=security_bar_1d`                                               |
| dry-run 副作用探测   | 空 sandbox + `sync_baostock_incremental(dry_run=True)`                                                                   | 0    | **before_exists=False → after_exists=True，size=2109440**；dry-run 经 `apply_migrations` 创建 DuckDB（见 finding A7-P1-01）             |
| non-dry-run replay   | `test_qmdData_syncBaostock_nonDryRun_replaySmoke`（pytest）                                                              | 0    | `job_status==COMPLETED`；写 sandbox `security_bar_1d`；`create_baostock_fetch_port(..., use_mock=True)` **硬编码 mock**，不经 live gate |
| 其他 domain 真跑挡板 | `sync_plan(data_domain=market_bar_1d, dry_run=False)`                                                                    | 抛错 | `CliFailure` / `USER_AUTH_REQUIRED`（既有 R3F-CLI 行为保留）                                                                            |

### GitNexus impact / detect_changes

| 目标                                   | 工具                                                                | 结果                                                                                                                                                                                |
| -------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DataSyncOrchestrator.run_incremental` | `impact(upstream, target_uid=…run_incremental#8)`                   | risk **LOW**；upstream 0 符号                                                                                                                                                       |
| `IncrementalJobRunner`                 | `impact(upstream, kind=Class)`                                      | risk **LOW**；d=1 `orchestrator.py` IMPORTS                                                                                                                                         |
| `compute_incremental_window`           | `impact(upstream)`                                                  | **未入索引**（`watermark.py` 为 worktree 未提交新文件；与 Execute 摘要一致）                                                                                                        |
| 分支变更                               | `detect_changes(scope=compare, base_ref=master, worktree=wt-dcp01)` | **7 changed symbols**，risk **medium**；命中 `IncrementalJobRunner.run`、`_PipelineMixin._finalize_staged`、`BaostockAdapter`；**未**命中 forbidden `orchestrator.py` / `fred_port` |

### detect_changes vs DEBT.plan allowed files

| 类别         | 结果             | 证据                                                                                                                              |
| ------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 已跟踪变更   | PASS             | `data_commands.py`、`runners.py`、`baostock_port.py`、`baostock.py` adapter、tests、`test_catalog.yaml`、generated docs ⊆ allowed |
| 未跟踪新文件 | PASS（scope 内） | `sync/watermark.py`、`test_baostock_incremental_*.py`、`test_qmd_data_sync_baostock.py` ∈ allowed                                 |
| forbidden    | PASS             | diff / status **无** `orchestrator.py`、`fred_port.py`、`db/migrations/**`、`data/duckdb/quant_monitor.duckdb`                    |

### 对抗搜索（计划外）

- 对照 `sandbox_clean_write` CLI：`assert_sandbox_db_allowed` + `--no-production-mutation` 门禁；**baostock `sync_baostock_incremental` 无等价路径守卫**（见 A7-P2-01）。
- dry-run 文案 vs 实际 writer+migrate（见 A7-P1-01）。
- `watermark.py` 新符号未入 GitNexus 索引：Execute 纪律项，**非**本维 DB 污染 finding。

---

## §维度裁决

**FAIL**

（§计划内问题 含 1 行非占位 finding；§计划外发现 含 1 行非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                                                       | 锚点                                                           | 根因                                                                                                                                                       | 修复方案                                                                                                                                           | 验证                                                                                                                                                               |
| -------- | --- | ---------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A7-P1-01 | P1  | dry-run 仍执行 migration 写 DuckDB，与「无副作用」文案矛盾 | `data_commands.py:139-145,178-179` `sync_baostock_incremental` | dry-run 路径在返回前调用 `ConnectionManager.writer()` + `apply_migrations(con)` 读 watermark；首次运行会创建 `quant_monitor.duckdb`（~2.1MB）并写入 schema | dry-run 分支：**不**开 writer/migrate；空库 watermark 视为 `None`（与空表 lookback 契约一致），或只读已存在库；同步修正 `message` 为准确副作用描述 | 空 sandbox：`dry_run=True` 后 `duckdb/quant_monitor.duckdb` **不存在**；设 env 后 canonical mtime 不变；`uv run pytest tests/test_qmd_data_sync_baostock.py -q` 绿 |

---

## 计划外发现

| ID       | P   | 标题                                          | 锚点                                                                                        | 根因                                                                                                                              | 修复方案                                                                                                                                                 | 验证                                                                                                           |
| -------- | --- | --------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| A7-P2-01 | P2  | baostock sync 缺少 canonical 路径 fail-closed | `data_commands.py:115-229` vs `sandbox_clean_write_rehearse` 的 `assert_sandbox_db_allowed` | `QMD_DATA_ROOT` 未设时 `DATA_ROOT` 回落 `PROJECT_ROOT/data`；运维误跑 `qmd data sync`（含 dry-run migrate）可 silent 写 canonical | 复用 `assert_sandbox_db_allowed` 或等价 guard：非 pytest 环境要求显式 sandbox root / `--db`；或默认拒绝 `data/duckdb` 写除非 `QMD_ALLOW_CANONICAL_WRITE` | 无 env 时 CLI exit 非 0 或强制 sandbox；设 `QMD_DATA_ROOT=.audit-sandbox/user-live` 时行为不变；靶向 pytest 绿 |

已对抗搜索：`backend/app/cli/**` 路径守卫模式、`DEBT.plan.md` production/data boundary、`docs/ops/backup_and_recovery.md` migration 契约、canonical duckdb mtime 对比、GitNexus `detect_changes` forbidden 文件集。

---
