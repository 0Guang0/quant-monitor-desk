# Audit A3 — Security（R3-DCP-09 Bounded Backfill + CI Nightly）

> **维：** A3 · **任务：** 07-02-wave4-r3-dcp-09-backfill-ci · **协议：** v4.1  
> **日期：** 2026-07-02 · **分支：** `feature/wave4-r3-dcp-09-backfill-ci`（未提交 diff）  
> **模板：** `agents/security-auditor.md` · **权威：** `agents/audit-adversarial-authority.md` · `AUDIT.plan.md` §0.1/§2 A3

---

## 维度证据 §3.3

### 范围

| 来源                   | 范围                                                                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AUDIT.plan §2 A3       | 无 `参考项目` runtime import                                                                                                                           |
| security-auditor 基线  | diff 变更面 + 信任边界 / SQL / 密钥 / 写路径 / live gate                                                                                               |
| 变更文件（`git diff`） | `data_commands.py` · `main.py` · `jobs.py` · `baostock_incremental_run.py` · `orchestrator.py` · `wave3_*_acceptance.py` · `nightly.yml` · 新测试/契约 |

### 静态命令与 rg 证据

| 动作                                                                                                                 | 证据                                                                        |
| -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `rg 参考项目 backend/ scripts/ --glob '!*test*'`                                                                     | **0 命中**                                                                  |
| `rg "import.*参考\|sys.path.*参考\|from 参考" backend/ scripts/`                                                     | **0 命中**                                                                  |
| `rg 参考项目 tests/test_qmd_data_backfill_cli.py tests/test_bounded_backfill_*.py tests/test_nightly_ci_manifest.py` | **0 命中**                                                                  |
| SQL f-string 扫描 `data_commands.py` · `jobs.py` · `baostock_incremental_run.py`                                     | **0 命中**；`jobs.py:125-143` INSERT 全 `?` 绑定                            |
| 密钥/URL 扫描变更面（`-i`）                                                                                          | 无硬编码 token；`data_commands.py:196` 仅 FRED 既有 `FRED_API_KEY` env 检查 |
| `subprocess` / `eval` / `exec` 于 `data_commands.py` · `baostock_incremental_run.py`                                 | **0 命中**                                                                  |
| `enable.qmt` / `enable.xqshare` / `--enable-qmt` 于变更面                                                            | **0 命中**                                                                  |

### GitNexus（必用）

| 调用                                                            | 结果                                                                                           |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `query` — `bounded backfill cap CLI write path live fetch gate` | 命中 live pilot / phase3 证据链；变更符号未全量索引                                            |
| `query` — `plan_backfill_shards run_backfill orchestrator`      | `plan_backfill_shards` → `BackfillShardRunner.run`；`DataSourceService.fetch` 金路径           |
| `impact` — `plan_backfill_shards` upstream                      | **LOW**；d=1：`BackfillShardRunner.run` · `production_equivalent_smoke._collect_scale_metrics` |
| `context` — `backfill_plan`                                     | 符号未索引（新代码）；静态读 `data_commands.py:505-687` 补证                                   |

### 信任边界核对（AUDIT.plan §2 · ENTRY §2 · ADR-030）

| 威胁面                               | 核对                                                                                                                                                                                                    | 结论                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| **参考项目 runtime import**（§2 A3） | `backend/**` · `scripts/**` 零 import/sys.path；`reference-adoption-dcp09.md` §0 铁律                                                                                                                   | **PASS**                                           |
| **有界 backfill cap**                | CLI `backfill_plan`：`max_shards` 1–12 · 默认 3 · 超 cap → `BACKFILL_CAP_EXCEEDED`；`truncate_to_cap` 记录 `window.effective_date_end`                                                                  | **PASS**（CLI 层；ADR-030 显式拒绝 runner 硬 cap） |
| **生产库写污染**                     | 非 dry-run：`_require_baostock_sync_operator_or_sandbox` + `assert_sandbox_db_allowed(..., allow_isolated_data_root=True)` 拒 prod/user-live；`test_qmd_data_backfill_without_dry_run_requires_sandbox` | **PASS**                                           |
| **dry-run 默认**                     | `main.py:61-65` `BooleanOptionalAction` default `True`；dry-run 须 `_require_audit_sandbox_data_root`                                                                                                   | **PASS**                                           |
| **Live fetch gate（ADR-027）**       | `resolve_baostock_incremental_use_mock()` → `is_product_live_fetch_allowed()`；无 env 则 mock replay                                                                                                    | **PASS**                                           |
| **金路径 / adapter bypass**          | `run_backfill` 保留 `guard_production_adapter_bypass` + `guard_production_datasource_service_required`；CLI 经 `DataSourceService`                                                                      | **PASS**                                           |
| **Route fail-closed**                | `route_status != READY` → `error_for_route_status`；`RESOURCE_GUARD_PAUSED` 提前拒绝                                                                                                                    | **PASS**                                           |
| **CI nightly 连网**                  | `nightly.yml`：`QMD_DATA_ROOT=.audit-sandbox/nightly-*` · `QMD_ALLOW_LIVE_FETCH=1` · `permissions: contents: read`；PR `ci.yml` 无 network                                                              | **PASS**                                           |
| **Live findings 门禁**               | `wave3_live_production_acceptance.py --fail-on-severity`；`EXPECTED_DEFER` 不计入；`LIVE-ACC-SEVERITY-GATE`                                                                                             | **PASS**                                           |
| **SQL 注入**                         | 变更面无 f-string SQL；e2e 测试参数化 `?` 查询                                                                                                                                                          | **PASS**                                           |

### 已核对架构取舍（**非 finding**）

| 项                                           | 说明                                                                                                                                                                   |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Runner 层无 `max_shards`                     | ADR-030 §Alternatives #1 明确拒绝；D2 RECONCILE「cap 在 planner + CLI；runner 吃已截断 `date_end`」。`backfill_plan` 传 `effective_end` 给 `run_baostock_bar_backfill` |
| `BackfillShardRunner.run:646` 无 cap 参数    | 与上同；直接调 `orchestrator.run_backfill` 为 operator/Python 级能力，非本任务新增旁路                                                                                 |
| `wave3_isolated` 设 `QMD_ALLOW_LIVE_FETCH=1` | diff 前已存在；步骤中 baostock 仅 `--dry-run`，fred 有 `QMD_FRED_INCREMENTAL_USE_MOCK=1`                                                                               |

### DOUBT 三类对抗搜索

| 类                 | 范围                                                                                                 | 结论                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 硬编码 URL 变体    | `data_commands.backfill_plan` · `baostock_incremental_run` · `nightly.yml` · `wave3_*_acceptance.py` | **无发现**；fetch 委托既有 baostock port                                          |
| JWT / API key 模式 | 同上 + 新测试文件                                                                                    | **无发现**；nightly 文档注明 `FRED_API_KEY` 为 GitHub secret（workflow 未硬编码） |
| SQL 拼接           | `jobs.py` · `data_commands.py` · e2e 测试                                                            | **无发现**；谓词参数化                                                            |

### §3.3 威胁摘要

| 威胁                            | 发现 | P   | 证据                                                                        |
| ------------------------------- | ---- | --- | --------------------------------------------------------------------------- |
| 参考项目 runtime 渗入           | 无   | —   | `rg` 0 命中 backend/scripts                                                 |
| 无界 backfill / cap 绕过（CLI） | 无   | —   | `BACKFILL_CAP_EXCEEDED` · `test_qmd_data_backfill_cap_exceeded_fail_closed` |
| 主库 silent 写入                | 无   | —   | sandbox gate · `test_qmd_data_backfill_without_dry_run_requires_sandbox`    |
| 未授权 live 源                  | 无   | —   | ADR-027 env gate · nightly 隔离 `QMD_DATA_ROOT`                             |
| SQL 注入                        | 无   | —   | 无 f-string SQL                                                             |
| 明文密钥                        | 无   | —   | rg 变更面 0 命中                                                            |

### 正向观察

- `backfill_plan` 域/源硬限制 `cn_equity_daily_bar` + `baostock`（`CAPABILITY_MISSING`），缩小 pilot 攻击面。
- 非 dry-run 顺序正确：route/guard → sandbox 授权 → `assert_sandbox_db_allowed` → `writer()` + migrate。
- `bounded_backfill_cli_e2e` 用 mock replay patch，不依赖真网即可验写路径。
- Nightly workflow `concurrency` 不 cancel-in-progress，避免半写证据状态（运维稳健性）。
- Live acceptance 新增 severity gate 强化 fail-closed（S05）。

---

## §维度裁决

**PASS**

（§计划内 + §计划外 findings 表均为占位行；checklist 满足）

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/cli/data_commands.py`（`backfill_plan`）· `backend/app/cli/main.py` · `backend/app/sync/jobs.py`（`plan_backfill_shards`）· `backend/app/ops/baostock_incremental_run.py` · `backend/app/sync/orchestrator.py` · `scripts/wave3_isolated_production_acceptance.py` · `scripts/wave3_live_production_acceptance.py` · `.github/workflows/nightly.yml` · `specs/contracts/bounded_backfill_cap.yaml` · 新测试模块 · GitNexus `query`×2 · `impact(plan_backfill_shards)` · DOUBT 三类 rg · AUDIT.plan §2 A3 参考项目铁律。
