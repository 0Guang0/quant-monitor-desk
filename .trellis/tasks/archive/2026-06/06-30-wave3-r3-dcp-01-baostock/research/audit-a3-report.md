# Audit A3 — 安全（R3-DCP-01 baostock incremental）

| 元信息   | 值                                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------------- |
| 维度     | A3 安全                                                                                                    |
| 任务     | `wave3-r3-dcp-01-baostock` · debt-lite                                                                     |
| 活卡     | `R3_DCP_01_BAOSTOCK_INCREMENTAL.md`                                                                        |
| 模板     | `agents/security-auditor.md` + `agents/audit-finding-schema.md` + 本任务 `AUDIT.plan.md` §A4（安全核对项） |
| 审计日期 | 2026-06-30                                                                                                 |
| 模型     | composer-2.5                                                                                               |
| worktree | `quant-monitor-desk-wt-dcp01`                                                                              |
| 分支     | `feature/wave3-r3-dcp-01-baostock`                                                                         |

---

## 维度证据 §3.3

### 变更范围（diff + DEBT.plan allowed）

| 文件                                                   | 安全相关变更                                                                |
| ------------------------------------------------------ | --------------------------------------------------------------------------- |
| `backend/app/cli/data_commands.py`                     | 新增 `sync_baostock_incremental`；`sync_plan` 对 `cn_equity_daily_bar` 路由 |
| `backend/app/sync/watermark.py`                        | 新建 watermark 读库 SQL                                                     |
| `backend/app/datasources/fetch_ports/baostock_port.py` | 窗过滤 + symbol whitelist                                                   |
| `backend/app/sync/runners.py`                          | `spec.date_start/end` → `FetchRequest`（无 adapter bypass 新增）            |
| `tests/test_qmd_data_sync_baostock.py` 等              | `QMD_DATA_ROOT` + `tmp_path` 隔离                                           |

**未改：** `fred_port`、orchestrator 共享锁面；无 requirements 变更。

### AUDIT.plan 安全核对项（任务卡 §A4 映射）

| 检查项                                          | 结果     | 证据                                                                                                                                                                                                                                                                                     |
| ----------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `QMD_DATA_ROOT` 隔离（测试/证据）               | **PASS** | `test_qmd_data_sync_baostock.py` / `test_baostock_incremental_e2e.py` 均 `monkeypatch.setenv("QMD_DATA_ROOT", tmp_path)` + `DATA_ROOT` patch；grep `tests/test_*baostock*` 无 `PROJECT_ROOT/data/duckdb` 引用                                                                            |
| 禁止 canonical 主库 silent 写                   | **FAIL** | `sync_baostock_incremental` L139–145、L195–225：`db = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"`；`DATA_ROOT` 默认 `PROJECT_ROOT/data`（`config.py:37`）；无 `_assert_production_db_allowed` / `assert_sandbox_db_allowed` 类 denylist（对照 `limited_production_entry.py:126-142`） |
| live env gate                                   | **PASS** | CLI 真跑 L195：`create_baostock_fetch_port(..., use_mock=True)` 硬编码；`use_mock=False` 才调 `gate_live_fetch_port`（`baostock_port.py:161-163`）+ `QMD_ALLOW_LIVE_FETCH`（`product_live_gate.py:24-27`）                                                                               |
| `ResourceGuard` 在 CLI 真跑路径                 | **PASS** | L137–138 取 guard；`dry_run=False` 时 L182–187：`guard_decision != OK` → `CliFailure(RESOURCE_GUARD_PAUSED)`                                                                                                                                                                             |
| dry-run 默认无 side effect                      | **FAIL** | `dry_run=True` 仍 L140–145：`mkdir` + `ConnectionManager.writer()` + `apply_migrations(con)`；payload 自述「no fetch or DB writes」与 DDL migration 矛盾                                                                                                                                 |
| 测试/证据无 canonical `quant_monitor.duckdb` 写 | **PASS** | 靶向 pytest 10/10 绿（Audit 独立复跑 2026-06-30）；日志路径均在 `tmp_path` 下                                                                                                                                                                                                            |

### 静态基线扫描（security-auditor §quant-monitor-desk）

| 扫描                           | 范围                                                           | 结果                                                               |
| ------------------------------ | -------------------------------------------------------------- | ------------------------------------------------------------------ |
| 密钥 / token / URL             | `watermark.py`, `baostock_port.py`, `data_commands.py` diff 区 | 0 命中                                                             |
| `subprocess` / `eval` / `exec` | `data_commands.py` diff 区                                     | 0 命中                                                             |
| SQL 拼接                       | `watermark.py:45`                                              | `f"SELECT ... FROM {clean_table} WHERE ..."` — 见 finding A3-P3-01 |
| `adapter=` 生产 bypass         | `data_commands.py` `run_incremental` 调用                      | 仅 `datasource_service=service`，无 `adapter=`                     |
| symbol 白名单                  | `baostock_port.py:32,67-69`                                    | `SYMBOL_WHITELIST` + `PortError`                                   |

### 信任边界（STRIDE 摘要）

| 边界                    | 威胁                      | 控制                                        | 残余                                   |
| ----------------------- | ------------------------- | ------------------------------------------- | -------------------------------------- |
| CLI → DuckDB            | 误写 canonical 主库 (E/T) | R3G promote 有 denylist；**本 CLI 路径无**  | **高** — 默认 `DATA_ROOT` 即 canonical |
| CLI dry-run             | 运维误判零副作用 (I)      | 消息声称无写；实际 migration                | **中**                                 |
| CLI → live fetch        | 未授权外网拉数 (T)        | `use_mock=True` + env gate 链               | **低**                                 |
| `instrument_id` 输入    | 非白名单 symbol (T)       | port `_reject_unknown_symbol`               | **低**                                 |
| watermark `clean_table` | SQL 注入 (T)              | 当前仅硬编码调用方                          | **低**（纵深缺口）                     |
| `cn_equity` 真跑        | 绕过 operator 确认 (E)    | 其它 domain 有 `USER_AUTH_REQUIRED`；本域无 | **中**                                 |

### GitNexus

| 动作                                                                   | 结果                                              |
| ---------------------------------------------------------------------- | ------------------------------------------------- |
| `query("sync_baostock_incremental QMD_DATA_ROOT production database")` | 命中 staged_pilot / vendor E2E 先例；无新符号专条 |
| `context("sync_baostock_incremental")`                                 | symbol not found（worktree 新符号，索引滞后）     |

### 独立 pytest 复验

```text
uv run pytest tests/test_qmd_data_sync_baostock.py \
  tests/test_baostock_incremental_watermark.py \
  tests/test_baostock_incremental_e2e.py -q
→ 10 passed (2026-06-30)
```

### DOUBT 对抗搜索

| 类别                | 范围                                       | 结论                                            |
| ------------------- | ------------------------------------------ | ----------------------------------------------- |
| 硬编码 URL 变体     | diff 区 + baostock port                    | 无发现                                          |
| JWT / API key 模式  | diff 区 backend                            | 无发现                                          |
| SQL 拼接            | `watermark.py`, CLI, port                  | 发现 `clean_table` f-string（A3-P3-01）         |
| 计划外 bypass       | `sync_plan` 早返回 vs `USER_AUTH_REQUIRED` | 发现 cn_equity 真跑无 operator gate（A3-P1-03） |
| 计划外 canonical 写 | CLI 默认 `DATA_ROOT` 路径                  | 发现无 denylist（A3-P1-01）                     |

---

## §维度裁决

**FAIL**

（§计划内问题 含 3 行非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                                         | 锚点                                                                                                             | 根因                                                                                                                                                                                                                      | 修复方案                                                                                                                                                           | 验证                                                                                                                                                    |
| -------- | --- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P1-01 | P1  | CLI 真跑无 canonical 主库 denylist           | `data_commands.py:139-145,195-225`；活卡 §3「禁止 silent 写 canonical」；`DEBT.plan.md` production/data boundary | `sync_baostock_incremental` 固定 `DATA_ROOT/duckdb/quant_monitor.duckdb`，未复用 `_assert_production_db_allowed`（`limited_production_entry.py:126-142`）fail-closed 模式；`QMD_DATA_ROOT` 未设时默认 `PROJECT_ROOT/data` | 真跑前调用共享 guard（拒绝 `canonical_prod` / `default_prod` 三路径集合）；或要求显式 `--db` + sandbox 路径；补 `test_qmdData_syncBaostock_refusesCanonicalDbPath` | `uv run pytest tests/test_qmd_data_sync_baostock.py -k canonical -q`；手工 `QMD_DATA_ROOT` 未设 + `--no-dry-run` 应 `CliFailure`                        |
| A3-P1-02 | P1  | dry-run 仍执行 migration 写库                | `data_commands.py:140-145,178-179`；`AUDIT.plan.md` §A4「dry-run 默认无 side effect」                            | `dry_run=True` 分支在返回 payload 前已 `mkdir` + `apply_migrations`；与 dry-run 契约及 payload 文案矛盾                                                                                                                   | dry-run 仅只读：若 DB 不存在则 watermark=None + 计算窗，不 `writer()`/不 migration；或文档化「schema bootstrap」为显式 `--init` 子命令                             | 新增测：`dry_run=True` 前后 `tmp_path` 下 duckdb 文件不存在或 mtime 不变；`uv run pytest tests/test_qmd_data_sync_baostock.py -k dryRunNoSideEffect -q` |
| A3-P1-03 | P1  | `cn_equity_daily_bar` 真跑绕过 operator 确认 | `data_commands.py:69-75` vs `76-85`；`sync_plan` 路由                                                            | `cn_equity_daily_bar` 早返回 `sync_baostock_incremental`，跳过其它 domain 的 `USER_AUTH_REQUIRED`（`dry_run=False` 门禁）                                                                                                 | 真跑前统一要求 operator 确认旗标（与 R3F-CLI-01 一致），或绑定 `QMD_DATA_ROOT` 必须在 `.audit-sandbox` 下                                                          | `uv run pytest tests/test_qmd_data_sync_baostock.py -k operatorAuth -q`；非 cn domain 现有测保持绿                                                      |

## 计划外发现

| ID       | P   | 标题                                     | 锚点                      | 根因                                                                   | 修复方案                                                                           | 验证                                                                                                          |
| -------- | --- | ---------------------------------------- | ------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| A3-P3-01 | P3  | watermark `clean_table` 未 `quote_ident` | `sync/watermark.py:44-46` | 表名 f-string 拼接；当前调用方仅传默认 `security_bar_1d`，无 allowlist | 引入 `quote_ident` + 表名 allowlist（`security_bar_1d`）或删除可配置参数仅保留常量 | 对抗测传入恶意 `clean_table` 应 `ValueError`；`uv run pytest tests/test_baostock_incremental_watermark.py -q` |

已对抗搜索：`data_commands.py` · `watermark.py` · `baostock_port.py` · `runners.py` diff 区；`tests/test_*baostock*`；`limited_production_entry` denylist 先例对照；GitNexus query。

---

## 已通过控制（不计 finding）

- **Live fetch fail-closed：** CLI 硬编码 `use_mock=True`；product live 须经 `QMD_ALLOW_LIVE_FETCH` + `gate_live_fetch_port`。
- **金路径无 adapter bypass：** `orch.run_incremental(..., datasource_service=service)`，无 `adapter=`。
- **ResourceGuard 真跑阻断：** `dry_run=False` 且 guard 非 OK 时抛 `RESOURCE_GUARD_PAUSED`。
- **Port 资源 cap：** `MAX_SYMBOLS=5` / `MAX_ROWS=500` / `MAX_WINDOW_DAYS=120` + symbol whitelist。
- **测试隔离：** 靶向测均在 `tmp_path` + `QMD_DATA_ROOT` 下，未写仓库 canonical DB。
