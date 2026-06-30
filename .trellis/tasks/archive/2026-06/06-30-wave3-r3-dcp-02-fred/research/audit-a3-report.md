# Audit A3 — Security（静态威胁面）

> **维：** A3 (audit-security)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模型：** composer-2.5

---

## 维度证据

### 审计范围（AUDIT.plan §2 A3 + 派发 scope）

| 文件                                               | 角色                                         |
| -------------------------------------------------- | -------------------------------------------- |
| `backend/app/datasources/fetch_ports/fred_port.py` | live/mock port · API key 读取 · 白名单       |
| `backend/app/ops/fred_incremental_watermark.py`    | 参数化 SQL 水位读                            |
| `backend/app/ops/fred_incremental_run.py`          | 金路径编排 · staging 写                      |
| `backend/app/cli/data_commands.py`                 | `sync_plan` / `_sync_fred_macro_incremental` |
| `backend/app/cli/main.py`                          | CLI 注册（`--source-id` · 默认 `--dry-run`） |
| `tests/test_fred_macro_incremental_*.py`           | 负例 / 隔离 / env gate                       |

**注：** `tests/test_catalog.yaml` 已由协调员 revert，不在本次 diff（A1 已记录）。

### 静态命令（security-auditor 基线 + AUDIT §2 A3）

```bash
# AUDIT §2 A3 点名
rg -n "FRED_API_KEY|api_key|QMD_ALLOW_LIVE_FETCH" \
  backend/app/datasources/fetch_ports/fred_port.py \
  backend/app/ops/fred_incremental*.py \
  backend/app/cli/data_commands.py \
  tests/test_fred_macro_incremental*.py

# SQL 拼接
rg -n "execute\(f|f\".*SELECT|f'.*SELECT" \
  backend/app/ops/fred_incremental*.py \
  backend/app/ops/fred_incremental_watermark.py

# forbidden 触及
rg -n "baostock" backend/app/datasources/fetch_ports/fred_port.py \
  backend/app/ops/fred_incremental*.py backend/app/cli/data_commands.py
```

| 检查项                     | 结果       | 证据                                                                                                                   |
| -------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| 明文密钥 / token 落盘      | **PASS**   | scope + `.env.example` 仅 `FRED_API_KEY=` 占位；diff 无真实 key                                                        |
| `FRED_API_KEY` 仅 env 读取 | **PASS**   | `fred_port.py` L33–38 `_fred_api_key()` → `os.environ.get`                                                             |
| `QMD_ALLOW_LIVE_FETCH` 门  | **PASS**   | CLI L167 `assert_product_live_allowed`；port L208–210 `gate_live_fetch_port`                                           |
| fail-closed 负例           | **PASS**   | pytest：`test_fredIncrementalCli_execute_rejectsWithoutLiveEnv` · `test_fredPort_live_rejectsWithoutApiKey` 均绿       |
| dry-run 无副作用           | **PASS**   | `sync_plan` dry_run 分支 L71–123 仅 `preview_route` + `ResourceGuard`；`preview_route` 不触 DB（`service.py` L85–100） |
| baostock / forbidden 触及  | **PASS**   | scope `rg baostock` 0 命中；`sync/orchestrator.py` · `sync/runners.py` 磁盘无 diff                                     |
| watermark SQL 参数化       | **PASS**   | `fred_incremental_watermark.py` L19–26 `WHERE indicator_id = ?`                                                        |
| staging SQL 拼接           | **ACCEPT** | `fred_incremental_run.py` L122–128 f-string 表名来自常量 `STAGING_TABLE` / `AXIS_OBSERVATION_DDL_COLUMNS`，非用户输入  |
| canonical DB denylist      | **FAIL**   | 见计划内 A3-P1-001                                                                                                     |
| GitNexus                   | **PASS**   | `query` ×2（fred incremental / gate_live_fetch_port）；新符号未索引（worktree 未 analyze）                             |

### 威胁面核对表（§3.3）

| 威胁                              | 发现   | P   | 证据                                                                                                                  |
| --------------------------------- | ------ | --- | --------------------------------------------------------------------------------------------------------------------- |
| 密钥进 repo / 日志                | 无     | —   | `.env.example` L17 空占位；port 无 `print`/`logger`                                                                   |
| 未授权 live 默认开启              | 无     | —   | `create_fred_fetch_port` 默认 `use_mock=True`；CLI live 须 `QMD_ALLOW_LIVE_FETCH`                                     |
| 绕过 env gate 写库                | 无     | —   | `test_fredIncrementalCli_execute_rejectsWithoutLiveEnv` → `LIVE_FETCH_REJECTED`                                       |
| canonical 主库 silent write       | **有** | P1  | `data_commands.py` L195–198；对比 `rehearsal_runner.py` L83–94 `assert_sandbox_db_allowed`                            |
| SQL 注入（用户输入进 SQL）        | 无     | —   | 水位/计数均 `?` 绑定；series 经 `P0_SERIES_WHITELIST`                                                                 |
| dry-run 隐式 migrate/写           | 无     | —   | fred dry-run 不建 `ConnectionManager`                                                                                 |
| registry disabled-by-default 绕过 | 边缘   | P2  | `enabled_fred_source_registry` L55 `is_enabled=True`；`build_fred_incremental_service` L264 `platform_allows` 恒 True |
| NETWORK_ERROR 泄露 URL 中 api_key | 未证实 | —   | `fred_port.py` L145 `str(exc)`；urllib 默认 reason 通常不含 query；无 job event 落盘证据                              |

### GitNexus 追溯

- `query("fred incremental sync QMD_ALLOW_LIVE_FETCH canonical database write path")` → 邻近流程含 `DataSyncOrchestrator` · `test_batch25_production_data_gate`（生产库门禁测），印证 canonical 路径为项目级敏感面。
- `query("gate_live_fetch_port create_fred_fetch_port assert_product_live_allowed")` → `product_live_gate.py` 模式与 `live_pilot_phase3` 同族；新符号未入索引（Execute 新文件）。

### 独立验证（fail-closed）

```text
uv run pytest tests/test_fred_macro_incremental_cli.py::test_fredIncrementalCli_execute_rejectsWithoutLiveEnv \
  tests/test_fred_macro_incremental_port.py::test_fredPort_live_rejectsWithoutApiKey -q
..  [100%]
```

### DOUBT 对抗搜索（三类）

| 类                 | 范围                   | 结论                                                    |
| ------------------ | ---------------------- | ------------------------------------------------------- |
| 硬编码 URL 变体    | scope `https?://`      | 仅 `fred_port.py` L140 官方 FRED endpoint；无第三方旁路 |
| JWT / API key 模式 | scope + tests          | env-only；测试用 `'a'*32` 假 key，未写入 artifact       |
| SQL 拼接           | ops fred_incremental\* | 仅 compile-time 表/列名；indicator_id 参数绑定          |

---

## §维度裁决

**FAIL**

（§计划内 1 行非占位 finding：A3-P1-001）

---

## 计划内问题

| ID        | P   | 标题                             | 锚点                                                       | 根因                                                                                                                                                                                                                                                                                                                                                                          | 修复方案                                                                                                                                                                                          | 验证                                                                                                                                                                                        |
| --------- | --- | -------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P1-001 | P1  | CLI 真跑缺 canonical DB denylist | `data_commands.py` L193–198 `_sync_fred_macro_incremental` | `data_root = _path_env("QMD_DATA_ROOT", PROJECT_ROOT / "data")` 未调用 `assert_sandbox_db_allowed`（对比 `rehearsal_runner.py` L83–94）；操作员在 `QMD_ALLOW_LIVE_FETCH=1` + `--no-dry-run` 且未设 `QMD_DATA_ROOT` 时，`apply_migrations` + `run_fred_macro_incremental` 可写 `data/duckdb/quant_monitor.duckdb`，违反活卡 §3「禁止 canonical 主库写」与 AUDIT.plan §5 硬门槛 | 在打开 `ConnectionManager` 前对 `db` 调用 `assert_sandbox_db_allowed(db, no_production_mutation=True)`（或等价：未显式非 canonical `QMD_DATA_ROOT` 时 `CliFailure`）；生产入口改走 R3G promote 链 | 新增 pytest：无 `QMD_DATA_ROOT` 覆盖时 `sync_plan(..., dry_run=False)` 拒绝 canonical 路径；隔离 `QMD_DATA_ROOT=tmp_path` 仍绿；`uv run pytest tests/test_fred_macro_incremental_cli.py -q` |

---

## 计划外发现

| ID        | P   | 标题                                    | 锚点                                                                                                                             | 根因                                                                                                                                                                | 修复方案                                                                                                                                          | 验证                                                                               |
| --------- | --- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| A3-P2-001 | P2  | 运行时绕过 registry disabled-by-default | `fred_incremental_watermark.py` L48–71 `enabled_fred_source_registry`；`fred_incremental_run.py` L264 `planner._platform_allows` | fred 在 `source_registry.yaml` 为 disabled-by-default；增量路径在内存 patch `is_enabled=True` 且 `platform_allows` 恒 True，削弱第二层源启用防线（env gate 仍生效） | 文档化 ponytail 天花板；或改为：仅当 registry DB 行已 enable / 操作员 `--fred-authorization` 文件时才 patch；升级路径绑定 registry reconcile 任务 | 负例测：registry 未 enable 且无 env gate 时 route 非 READY；正例测：双 gate 下仍绿 |

已对抗搜索：scope 全文件 + `rehearsal_runner.assert_sandbox_db_allowed` 对照 + `specs/datasource_registry` fred 行 + fail-closed pytest 复跑 + GitNexus 生产库门禁邻域流程。

---

## 关账自检

- [x] Boot：已 Read `audit-boot-v4.1.md` · `audit-skill-paths.yaml` A3 · `security-auditor.md` · `sql-pro.md` · `audit-finding-schema.md` · `AUDIT.plan.md` §2 A3
- [x] §维度裁决 ∈ {PASS, FAIL}
- [x] findings 非占位 → FAIL
- [x] 每行 P0–P3 + 修复方案 + 验证
- [x] 未改代码（只读审计）
