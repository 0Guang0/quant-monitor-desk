# Audit A3 — Security（R3-DCP-05 Tier A）

> **维：** A3 · **任务：** wave4-r3-dcp-05-tier-a · **协议：** v4.1  
> **日期：** 2026-07-02 · **分支：** `feature/wave4-r3-dcp-05-tier-a`  
> **模板：** `agents/security-auditor.md` · **权威：** `agents/audit-adversarial-authority.md`

---

## 维度证据 §3.3

### 范围与命令

| 动作                                                                                                 | 证据                                                                                                                 |
| ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `rg 参考项目 backend/`                                                                               | **0 命中**（无 runtime import）                                                                                      |
| `rg 参考项目 tests/`                                                                                 | 仅 guardrail/契约测试字符串；无 `import`/`sys.path` 耦合                                                             |
| `rg import.*参考\|sys.path.*参考 backend/`                                                           | **0 命中**                                                                                                           |
| SQL f-string 扫描 `backend/app/cli/tier_a_sync_router.py` · `data_commands.py` · `ops/*incremental*` | 表名来自常量/`resolve_clean_write_target`；用户输入（`instrument_id`/`since`）走 `?` 绑定（如 `watermark.py:55-62`） |
| 密钥扫描 tier-a 变更面                                                                               | 无硬编码 token；`tests/test_fred_macro_incremental_port.py` 用 `"a"*32` 占位                                         |
| GitNexus `query`（repo=quant-monitor-desk）                                                          | 命中 live pilot / validation_gate 流；索引 stale（`gitnexus-audit-summary.md`）                                      |
| GitNexus `impact`/`context` on `assert_product_live_allowed`                                         | 符号未索引；改读 `product_live_gate.py` 静态链                                                                       |

### 信任边界核对（AUDIT.plan §2 · ENTRY §2）

| 威胁面                  | 核对                                                                                        | 结论                            |
| ----------------------- | ------------------------------------------------------------------------------------------- | ------------------------------- |
| 参考项目 runtime import | `backend/**` 零 import；`reference-adoption-dcp05.md` §0 铁律                               | **PASS**                        |
| ADR-027 live gate       | `product_live_gate.py` · port `gate_live_fetch_port`；baostock/mootdx `resolve_*_use_mock`  | **部分 PASS**（见 P1/P2）       |
| fail-closed sync        | tier_a 8/11 源 `--no-dry-run` → `USER_AUTH_REQUIRED`；sandbox + `assert_sandbox_db_allowed` | **FAIL**（mootdx 路由门控缺口） |
| SQL 注入                | watermark/macro 查询参数化；DDL 表名非用户输入                                              | **PASS**                        |
| fixtures 密钥           | 无真实 API key 落盘                                                                         | **PASS**                        |

### DOUBT 三类对抗搜索

| 类                 | 范围                                                               | 结论                                     |
| ------------------ | ------------------------------------------------------------------ | ---------------------------------------- |
| 硬编码 URL 变体    | `tier_a_sync_router.py` · `data_commands.py` · `ops/*incremental*` | 无新增 outbound URL；fetch 委托既有 port |
| JWT / API key 模式 | 同上 + 新增 `tests/test_qmd_data_sync_tier_a_router.py`            | 无硬编码 secret；FRED 占位 key 仅测试    |
| SQL 拼接           | incremental ops + router                                           | 仅标识符常量插值；谓词参数化             |

### §3.3 威胁摘要

| 威胁                                | 发现               | P   | 证据                                                |
| ----------------------------------- | ------------------ | --- | --------------------------------------------------- |
| 参考项目 runtime 渗入               | 无                 | —   | `rg` 0 命中 backend                                 |
| registry 禁用态绕过（dry-run 审计） | 有                 | P2  | `enabled_source_registry` · `_tier_a_route_preview` |
| validation_only 源写 clean 绕过     | 有                 | P1  | `sync_mootdx_incremental` route gate                |
| dry-run route 非 READY 仍 exit 0    | 有                 | P2  | `_dry_run_shell` vs fred 分支                       |
| live fetch 无 ADR-027 opt-in        | 无（port 层 gate） | —   | `baostock_port.py:157-159`                          |
| SQL 注入                            | 无                 | —   | `watermark.py` 参数绑定                             |

### 正向观察

- `tier_a_sync_router.sync_tier_a_by_source_id` 对未知 `source_id`、domain mismatch **fail-closed**（`INVALID_INPUT`）。
- S12 对 bis/us_treasury 等 8 源 `--no-dry-run` 统一 `USER_AUTH_REQUIRED`，无 staging-only 旁路。
- `sync/runners.guard_reconcile_product_live_service` 保留 ADR-027 对注入 fetch_port 的 fail-closed。
- baostock live：`QMD_ALLOW_LIVE_FETCH` → `use_mock=False` 有专门测试（`test_qmd_data_sync_baostock.py`）。
- fred live：`assert_product_live_allowed` + `FRED_API_KEY` 缺失 → `USER_AUTH_REQUIRED`（禁止 silent mock）。

---

## §维度裁决

**FAIL**

（§计划内 1 行 + §计划外 2 行非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                                        | 锚点                                                                   | 根因                                                                                                                                                                      | 修复方案                                                                                                                                                                                                               | 验证                                                                                                                                                                                        |
| --------- | --- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P1-001 | P1  | mootdx 增量 sync 用 domain 主源路由门控，绕过 registry 禁用/validation_only | `backend/app/cli/data_commands.py:533-624` · `sync_mootdx_incremental` | `route_preview(cn_equity_daily_bar)` 只验证 **baostock primary** READY；未校验 `mootdx` `is_enabled`/`validation_only` 即调用 `build_mootdx_incremental_service` 写 clean | 在 `sync_mootdx_incremental` 非 dry-run 前：`preview_route(..., source_id="mootdx")` 或 `registry.get("mootdx")` 断言 enabled 且拒绝 validation_only 写路径；与 `route_planner.validation_only_cannot_be_primary` 对齐 | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py tests/test_mootdx_incremental_e2e.py -q`；新增负向：`mootdx` registry disabled 时 `--source-id mootdx --no-dry-run` → `CliFailure` |

---

## 计划外发现

| ID        | P   | 标题                                                                    | 锚点                                                                                           | 根因                                                                                                                                                           | 修复方案                                                                                                                                          | 验证                                                                                                                                                       |
| --------- | --- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3-P2-001 | P2  | Tier A dry-run 预览强制 enable 禁用源，审计 JSON 误导 READY             | `tier_a_sync_router.py:41-47` · `macro_incremental_common.py:87-110` `enabled_source_registry` | `_tier_a_route_preview` 对 bis/fred/us_treasury 等 **enabled_by_default:false** 源 runtime patch `is_enabled=True`，dry-run 显示生产 registry 不会允许的 READY | dry-run 改用生产 `SourceRegistry`（与 baostock `route_preview` 一致）；若源 disabled 则 `route_status!=READY` 或 `CliFailure`，禁止 silent enable | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -q`；新增：registry 默认态下 `bis` dry-run 不得 `route_status=READY` 除非显式 test fixture enable |
| A3-P2-002 | P2  | `_dry_run_shell` 在 route 非 READY 时仍返回成功形 JSON（fred 路径除外） | `tier_a_sync_router.py:72-96` `_dry_run_shell`；对比 `274-278` fred 分支                       | 10/11 源 dry-run 对 `route_status!=READY` 仅改 message 不 raise；自动化可误判 exit 0=可执行                                                                    | 统一 fail-closed：`route_status!=READY` → `error_for_route_status`（与 fred · `data_commands.sync_plan` 一致）                                    | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -q`；负向：DISABLED 源 dry-run 须非 0 exit 或明确 `error_code`                                    |

已对抗搜索：`backend/app/cli/tier_a_sync_router.py` · `data_commands.py` · `backend/app/ops/*incremental*` · `backend/app/datasources/product_live_gate.py` · `tests/test_qmd_data_sync_tier_a_router.py` · `specs/datasource_registry/source_registry.yaml` · GitNexus live-gate 查询 · DOUBT 三类 rg。
