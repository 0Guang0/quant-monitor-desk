# Repair/Debt Lite Plan — wave3-r3-dcp-02-fred

## Source of truth

- **audit / registry ID:** R3-DCP-02（活卡 `R3_DCP_02_FRED_INCREMENTAL.md` · INDEX §2）
- **base branch:** `master`
- **target branch:** `feature/wave3-r3-dcp-02-fred`
- **owner agent:** Execute（轨 B worktree `../quant-monitor-desk-wt-dcp02`）
- **调研 SSOT:** `research/reference-adoption-dcp02.md` · `research/architecture-dcp02.md`

## Boundary

### allowed files

```text
backend/app/datasources/fetch_ports/fred_port.py
backend/app/ops/fred_*.py
backend/app/ops/fred_incremental*.py（新建）
backend/app/cli/data_commands.py（fred macro_series sync 切片）
backend/app/cli/main.py（若需注册 sync --source-id 等参数）
tests/test_*fred*
tests/test_*macro*incremental*
.trellis/tasks/06-30-wave3-r3-dcp-02-fred/**
```

**sync 包（只读）：** 可 `import` 调用 `DataSyncOrchestrator.run_incremental` / `IncrementalJobRunner`；**禁止**改 `orchestrator.py` · `runners.py` 源码（协调手册 §4 · 轨 A 拥有写权限）。

### forbidden files

```text
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/adapters/baostock.py
backend/app/sync/orchestrator.py
backend/app/sync/runners.py
backend/app/sync/watermark*.py（写 — 轨 A 拥有；本轨仅 import 宏观专用 API）
tests/test_*baostock*
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
tests/test_catalog.yaml
data/duckdb/quant_monitor.duckdb
```

### production/data boundary

- 开发/CI：隔离 `QMD_DATA_ROOT`（tmp_path 或 `.audit-sandbox/user-live`）
- Live smoke：须 `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH=1`；**禁止** canonical 主库写
- 生产等价验证：仅 merge gate（主会话）

### explicit non-goals

- 宏观六源全量增量（Wave 4）
- 新 FRED series 目录 UI
- SEC/CFTC / 其它宏观源
- 新 migration / schema 变更
- 修改 baostock / CN equity clean 域

---

## Vertical slices

| Slice | Source ID | AC | Allowed files | Forbidden files | Verification | Evidence |
| ----- | --------- | --- | ------------- | --------------- | ------------ | -------- |
| **S02-01** watermark | R3-DCP-02 §5 | 空表 / 有观测 / 多 series 水位单测 | `ops/fred_incremental_watermark.py` · `tests/test_fred_macro_incremental_watermark.py` | `baostock_port` · `sync/watermark*`（写） | `uv run pytest tests/test_fred_macro_incremental_watermark.py -q` | 测绿 + 代码 |
| **S02-02** port window | R3-DCP-02 §5 | `FetchRequest.start_time` → FRED `observation_start`；冷启动 capped 窗 | `fred_port.py` · `tests/test_fred_macro_incremental_port.py` | 其它 port | `uv run pytest tests/test_fred_macro_incremental_port.py -q` | 测绿 |
| **S02-03** e2e replay | R3-DCP-02 §5 | mock/replay 经 `datasource_service` + `run_incremental` 写 `axis_observation`；调用方传 macro `primary_keys`/`required_fields` | `fred_port.py` · `ops/fred_incremental_run.py` · `tests/test_fred_macro_incremental_e2e.py` | `orchestrator.py` · `runners.py` · `baostock_port` | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q -k replay` | 测绿 + row count |
| **S02-04** live + idempotent | R3-DCP-02 §5 | env-gated live smoke；重复跑行数不增 | `fred_port.py` · `tests/test_fred_macro_incremental_e2e.py` | canonical DB | `pytest -k live_smoke`（skip 无 key）· `-k idempotent` | 测绿 |
| **S02-05** CLI | R3-DCP-02 §4 | `qmd data sync --domain macro_series --source-id fred` dry-run + 测中真跑（对齐 `live-fetch` 旗标；**非** `--source`） | `cli/data_commands.py` · `cli/main.py` · `tests/test_fred_macro_incremental_cli.py` | 非 fred CLI · baostock domain | `uv run pytest tests/test_fred_macro_incremental_cli.py -q` | 测绿 + help 快照 |

**切片数（Execute）：** **5**

**协调依赖：** S02-01 可独立于轨 A；若轨 A 已 merge `sync/watermark.py`，S02-01 **仅**可 import 宏观专用 API（`indicator_id` + `observation_date`/`publish_timestamp` 语义）；**禁止**调用 baostock `trade_date` reader（轨 A `read_bar_trade_date_watermark` 等 bar 域函数）。

---

## Merge gate

| 检查 | 命令 |
|------|------|
| 定向测 | `uv run pytest tests/test_fred_macro_incremental_watermark.py tests/test_fred_macro_incremental_port.py tests/test_fred_macro_incremental_e2e.py tests/test_fred_macro_incremental_cli.py -q` |
| 全库 | `uv run pytest -q` exit 0 |
| Loop | `uv run python scripts/loop_maintain.py`（新测模块时 `--fix`） |
| Registry | 主会话排队（本轨仅 proposed fred delta） |
| 生产等价 | merge 后主会话可选 live smoke（隔离库） |

---

## Execute Boot 必读（切片前）

1. `research/reference-adoption-dcp02.md`（L1/L2/L3）
2. `research/architecture-dcp02.md`
3. `DEBT.plan.md` 本表当前切片行
4. `/test-driven-development` · `/testing-guidelines` · `/karpathy-guidelines`
5. RED 前 Read 仓内：`fred_port.py` · `clean_write_targets.py` · `rehearsal_loader.py`（macro 映射）
6. **`_tmp-wave3-dcp-parallel/agent-prompts/EXECUTE-REFERENCE-READ-GATE.md`** — 主仓实读
7. **主仓绝对路径**（worktree 内无 `参考项目/`）：
   - `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\OpenBB\openbb_platform\core\openbb_core\provider\abstract\fetcher.py`（architecture_only）
   - `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\EasyXT\data_manager\unified_data_interface.py` L172-237（forbidden）
8. **RED 前产出** `research/execute-reference-read-evidence.md`

**禁止：** 未 Read 调研 + 主仓参考项目 + 仓内源码即写 port/CLI 实现。
