# G1-01 正式入口接线清单与配置核实

> **切片：** Gate 1 · G1-01  
> **日期：** 2026-07-11  
> **方法：** GitNexus `query`/`context`（repo `quant-monitor-desk`）+ 源码/契约/registry 对照  
> **索引：** `context(SourceRegistry.sync_to_db)` 与 `context(DataSyncOrchestrator.bootstrap)` 已核对调用方；若 MCP 提示 index 滞后，结论仍以当前仓库文件为准。  
> **状态：** Plan r6（`completion-check-plan-g1-01-r6.md`）= **`PLAN-READY`**（独立重审；消 r5 CC-3/CC-5）。**不等于**实现 / R4 / G1-08 完成。

---

## 0. 同参探针定义（跨入口横测用）

下列输入用于「同参 → 同 source/status/reason」验收（G1-02～G1-05）。**档位**列见 §3。

| 探针 ID | platform（隐式） | data_domain | operation（默认） | 产品默认期望（未授权、无 overlay） | 证据锚点 |
|--------|------------------|-------------|-------------------|--------------------------------------|----------|
| P-DAILY | 本机 matrix | `cn_equity_daily_bar` | `fetch_daily_bar` | `READY` / `baostock` / Primary | `source_registry.yaml` `domain_roles.cn_equity_daily_bar`；audit CC-1 复现 |
| P-MINUTE | 本机 matrix | `cn_equity_minute_bar` | （域默认） | `DISABLED_SOURCE` + 授权类 reason（`user_authorization_required` / domain disabled） | YAML `domain_enabled_by_default: false` + primary `qmt_xtdata`；audit CC-1 |
| P-MACRO | 本机 matrix | `macro_series` | （域默认） | `DISABLED_SOURCE`（fred 默认关 + 域默认关） | YAML `macro_series`；`enabled_by_default: false` on fred |
| P-SUPP | 本机 matrix | `macro_supplementary` | （域默认） | `VALIDATION_ONLY_BLOCKED`（域默认开但 primary=akshare validation_only） | YAML L431–438；findings T01-F02 |

**禁止：** 用 override 路径的绿灯冒充上表「产品默认」期望。

---

## 1. 正式入口总表

图例 — **策略路径**：

| 代号 | 含义 |
|------|------|
| **SSOT-DEFAULT** | 未打补丁的 `SourceRegistry` + `SourceCapabilityRegistry` + platform matrix |
| **OVERRIDE-MEM** | `enabled_source_registry` / `enabled_fred_source_registry`：`object.__setattr__(is_enabled)` + 改写 `get_domain_roles`；常伴 `planner._platform_allows = lambda: (True,None)` |
| **PRODUCT-LIVE** | `build_product_live_service`（默认 registry，另挂 live fetch_port） |
| **N/A-POLICY** | 不选源（仅同步登记表 / 健康检查等） |

图例 — **目标档位**（证据允许范围）：

| 档位 | 允许证据 | 禁止升格为 |
|------|----------|------------|
| `dry_run` | CLI 默认 dry-run 计划/预览 | R4 / G1-08 发布 |
| `product_default` | 未覆盖 registry 的预览/拒绝 | — |
| `override_runtime` | 仅作「绕过仍存在」反证 | 产品启用证明 |
| `gate_live` | `QMD_DATA_ROOT` 含 `.audit-sandbox/source-route-db` 且非 dry-run | fixture/replay PASS |
| `staged_fixture` | `staged_fixture_mode=True` 宏增量 | 产品默认 |
| `danger_skip_isolation` | **仅**登记暗门存在；**禁止**作任何完成/发布证据 | 一切正式档位 |

**overlay revision：** 当前仓库**尚无**持久化 `source_activation_overlay` 实现；列填 `none（ADR-017/018 待 G1-02）`。目标态两层接缝见 ADR-018：开关本层 → 安检层；禁止内存 OVERRIDE 长期兼容。

### 1.1 Registry 同步（task-01 直属 · 含 `sync_to_db` 全量生产/运维入口）

GitNexus `context(sync_to_db)` 生产侧调用方：`init_basic`、`scripts/init_db.py:main`、`DataSyncOrchestrator.bootstrap`、`acceptance_isolation._ensure_isolated_db_cached`（另：测试与 `scripts/sync_registry.py`）。

| ID | 入口命令 / 函数 | 调用链（精简） | Owner 切片 | 同参输入 | 策略路径 | overlay | 档位 | 预期可观察结果 | 持久化 / 事件 | 反证 |
|----|-----------------|----------------|------------|----------|----------|---------|------|----------------|---------------|------|
| E-REG-01 | `qmd-sync-registry` → `scripts.sync_registry:main` | `SourceRegistry.load` → `sync_to_db`（`tombstone_missing=True`） | G1-02 / 工作包 5 | `--yaml` 可选；DB=`$QMD_DATA_ROOT/duckdb/quant_monitor.duckdb` | N/A-POLICY | none | `product_default`（默认根）或显式隔离根 | stdout `sync_registry: ok rows=N`；DuckDB `source_registry` 行与 YAML 一致 | DuckDB 表行 | 改 YAML 后不同步则 DB 陈旧 |
| E-REG-02 | `qmd-data data init-basic` → `data_commands.init_basic` | dry-run：只声明 steps；确认写：migrate + `sync_to_db` | G1-04 | `--db` 可选；默认 dry-run | N/A-POLICY | none | `dry_run` 默认；`dry_run=false`→`product_default`（或 `--db` 指向的根） | dry-run 无写，文案指向 `qmd-init-db --sync-registry`；确认后 `registry_rows` 有值 | schema + registry | 未确认 dry-run 却写入；与 E-REG-03 写入同库后行数不一致 |
| E-REG-03 | `qmd-init-db --sync-registry` → `scripts.init_db:main` | migrate →（仅 flag 时）`SourceRegistry.load` → `sync_to_db(tombstone_missing=True)` | G1-02 / 工作包 5 | `--sync-registry` **必选才写 registry**；`--db` 覆盖路径，否则 `DATA_ROOT`（=`QMD_DATA_ROOT`）`/duckdb/quant_monitor.duckdb`；**无 dry-run** | N/A-POLICY | none | **实际写入**：默认 `product_default`；`--db` 指隔离路径时仍是真实写，须按路径降档登记，不得当 dry-run | stdout `init_db: sync_registry rows=N` + `database at <path>`；表行=YAML | 迁移 + registry 行 | 无 `--sync-registry` 时不写 registry（仅 migrate）；与 E-REG-01 同 DB 根应对齐行数 |
| E-REG-04 | `DataSyncOrchestrator.bootstrap(sync_registry=True)` | `registry.load` → `self._cm.writer` → `sync_to_db(tombstone_missing=True)` | G1-02（策略 SSOT）/ 调用方属 task-10 编排面 | 程序化；DB=构造 orchestrator 时的 `ConnectionManager` 路径；`sync_registry=False`（默认）**不**同步 | N/A-POLICY | none | **实际写入**（取决于 CM 根：产品根=`product_default`；隔离根须显式标注） | 调用后该 CM 库 `source_registry` 与 YAML 一致 | DuckDB 表行 | `sync_registry=False` 仍声称已同步；当前生产 CLI **未**调用本 API（GitNexus 仅见测试调用），但仍是可写正式方法，禁止漏登 |

### 1.2 默认服务路径（SSOT 基准）

| ID | 入口命令 / 函数 | 调用链 | Owner | 同参输入 | 策略路径 | overlay | 档位 | 预期 | 持久化 / 事件 | 反证 |
|----|-----------------|--------|-------|----------|----------|---------|------|------|---------------|------|
| E-SVC-01 | `DataSourceService.preview_route` / `fetch`（`_service()`） | `DataSourceService` → `SourceRoutePlanner.plan` → registry/capability/matrix | G1-02 | P-DAILY / P-MINUTE / P-MACRO / P-SUPP | **SSOT-DEFAULT** | none | `product_default` | 见 §0 | `_emit_route_plan` / job_events（若注入） | monkeypatch registry 后结果变化 |
| E-CLI-01 | `qmd-data data route-preview` → `route_preview` | `_service()` → `preview_route` | G1-04 | `--domain` + optional `--operation` / `--use-fallback` | **SSOT-DEFAULT** | none | `dry_run` + `product_default` | 与 E-SVC-01 同参同 status/source/reason | payload `route_plan` | 同参与 OVERRIDE 入口不一致 |
| E-CLI-02 | `qmd-data data live-fetch`（dry-run） | `_service().preview_route`；live 才 `build_product_live_service` | G1-04 | `--source-id` `--domain` | preview=**SSOT-DEFAULT**；fetch=**PRODUCT-LIVE** | none | dry-run=`dry_run`；live 另受 ProductLiveGate | preview 与 E-CLI-01 同域同结果 | dry-run 无 fetch | gate 拒绝时仍强制 fetch |

### 1.3 四类 Gate 命令（task-17）

| ID | 入口命令 / 函数 | 调用链 | Owner | 同参输入 | 策略路径 | overlay | 档位 | 预期 | 持久化 / 事件 | 反证 |
|----|-----------------|--------|-------|----------|----------|---------|------|------|---------------|------|
| E-CLI-10 | `qmd-data data sync`（无 `--source-id`，非 baostock 捷径） | `sync_plan` → dry-run 时 `route_preview` | G1-04 | `--domain` | **SSOT-DEFAULT** | none | `dry_run` | READY 才出计划；否则 `error_for_route_status` | dry-run 无写 | 未 READY 仍声称可 sync |
| E-CLI-11 | `qmd-data data sync --domain cn_equity_daily_bar`（无 source-id） | `sync_baostock_incremental` → `route_preview` | G1-04 | P-DAILY | **SSOT-DEFAULT** | none | `dry_run` / `gate_live` | 预览 READY/baostock | watermark 窗；live 写 audit root | 用 OVERRIDE 假装 baostock 启用 |
| E-CLI-12 | `qmd-data data sync --source-id <gold>` | `incremental_sync_router.sync_incremental_by_source_id` → `_incremental_route_preview`（**默认** `SourceRegistry`）或各源 `*_incremental_run` | G1-04→G1-02 | gold 源 + 规范域（见 §2.1） | 预览：**SSOT-DEFAULT**；执行侧多数宏源见 §1.4 **OVERRIDE-MEM** | none | dry-run 要求 `QMD_DATA_ROOT`∈`.audit-sandbox`；live→`gate_live` | 预览应反映 YAML 禁用；不得静默变 READY | acceptance envelope / watermark | `_incremental_route_preview` 绿但 `load_incremental_route_bundle` 强制启用 |
| E-CLI-13 | `qmd-data data sync --source-id mootdx` | `sync_mootdx_incremental` → **`enabled_source_registry(mootdx)`** | G1-02 / 4b | P-DAILY 域但强制 mootdx | **OVERRIDE-MEM** | none | `override_runtime` | 可 READY/mootdx（绕过 YAML 若 mootdx 默认关） | watermark 计划 | 移除 override 后应回默认策略 |
| E-CLI-20 | `qmd-data data backfill` | `backfill_plan` → `_gold_path_backfill_route_preview`（`data_commands.py` L304–331） | G1-04 / 4b → **G1-02 清 OVERRIDE** | `--domain --source-id --start --end`（金路径源见 §2.1） | **OVERRIDE-MEM（全金路径）**：`source_id==fred` 且域=`macro_series` → `build_fred_incremental_preview_service`（编排壳，内部仍 `load_incremental_route_bundle`/ESR）；**else 任意非 fred 金路径** → 直接 `enabled_source_registry` + `_platform_allows=True`。**不是**「仅 fred 专用」 | none | `dry_run` / `gate_live` / `override_runtime` | 覆盖后可能 READY；**不等于**产品默认；与 ADR-018 开关本目标冲突属已知债 | shard plan + acceptance | 与 E-CLI-01 同域不同 status；只清 fred 分支而漏清 else → 非 fred backfill 仍 OVERRIDE |
| E-CLI-30 | `qmd-data data full-load` | `full_load_plan` → **`route_preview`（SSOT）**；baostock live 走 phase1 | G1-04 | 同 backfill 形参 | 预览 **SSOT-DEFAULT** | none | `dry_run` / `gate_live` | 预览服从 YAML；未 READY 拒绝 | shard + envelope | backfill override 绿而 full-load 红（同参）即入口分裂 |

### 1.4 增量 / 宏源执行（OVERRIDE 消费者 — 须进 G1-02 闭环）

共享根因：`macro_incremental_common.enabled_source_registry` + `load_incremental_route_bundle`（强制 `_platform_allows`）。

| ID | 入口 / 包装函数 | 文件锚点 | Owner | 规范域 | 策略路径 | 档位 | 预期（当前事实） | 反证 |
|----|-----------------|----------|-------|--------|----------|------|------------------|------|
| E-INC-FRED | `enabled_fred_source_registry` / `build_fred_incremental_*` | `fred_incremental_watermark.py`（含**重复** enable 拷贝）；`fred_incremental_run.py` | G1-02 / 4a；编排合并见 **ADR-018** / `T01-ENABLE-FRED-MERGE-001` | `macro_series` | **OVERRIDE-MEM**（与 E-INC-BUNDLE **同模式**；builder=编排壳≠第二套启用权威） | `override_runtime` / `staged_fixture` | 强制启用 fred+域；watermark/proxy 为编排 | 默认 E-CLI-01 P-MACRO 仍 DISABLED；G1-08 前须按 ADR-018 合并或废止 |
| E-INC-AV | `enabled_alpha_vantage_source_registry` | `alpha_vantage_incremental_run.py` | G1-02 | `us_equity_daily_bar` | OVERRIDE-MEM | 同上 | 强制启用 | YAML 默认域 disabled |
| E-INC-UST | `enabled_us_treasury_source_registry` | `us_treasury_incremental_run.py` | G1-02 | `us_treasury_yield_curve` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-BIS | `enabled_bis_source_registry` | `bis_incremental_run.py` | G1-02 | `central_bank_policy` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-WB | `enabled_world_bank_source_registry` | `world_bank_incremental_run.py` | G1-02 | `development_indicator` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-CFTC | `enabled_cftc_source_registry` | `cftc_incremental_run.py` | G1-02 | `cot_positioning` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-CNINFO | `enabled_cninfo_source_registry` | `cninfo_incremental_watermark.py` | G1-02 | `cn_announcements` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-SEC | `enabled_sec_edgar_source_registry` | `sec_edgar_incremental_watermark.py` | G1-02 | `us_filings` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-DER | `enabled_deribit_source_registry` | `deribit_incremental_watermark.py` | G1-02 | `crypto_options_surface` | OVERRIDE-MEM | 同上 | 强制启用 | — |
| E-INC-BUNDLE | `load_incremental_route_bundle` / `build_macro_incremental_service` | `macro_incremental_common.py` L428–467 | G1-02 | 各宏域 | OVERRIDE-MEM + `staged_fixture_mode=True` | `staged_fixture` | 路由可 READY | 与 SSOT 预览不一致 |

GitNexus `context(enabled_source_registry)` 已列出上表生产调用方（另含 `tests/test_mootdx_adapter_staging.py` — **测试**，G1-02 测试治理）。

### 1.5 Scheduler（task-18）

| ID | 入口命令 / 函数 | 调用链 | Owner | 同参输入 | 策略路径 | overlay | 档位 | 预期 | 持久化 / 事件 | 反证 |
|----|-----------------|--------|-------|----------|----------|---------|------|------|---------------|------|
| E-SCH-01 | `qmd-data data scheduler run --profile <name>` | `scheduler_run` → `sync.scheduler.run_profile` → `execute_binding`；live 时 `resolve_binding_datasource_service` → `_build_datasource_service` | G1-05 | profile=`daily_close` / `weekly_backfill` | binding：**PRODUCT-LIVE** 或 baostock builder（**非** enabled_source_registry）；与 matrix spine OVERRIDE **双轨** | none | `dry_run` 默认；live=`gate_live` | dry-run 出 child envelope；live 须与 RoutePlan 同 source；**当前** fred binding 用默认 registry（常 DISABLED），matrix live 用 override — 已知分裂 | parent/child report JSON | 同 profile 与 CLI sync 不同 source |
| E-SCH-02 | `qmd-data data incremental --profile` | `incremental_profile_plan` → `scheduler_run`（仅 incremental jobs） | G1-05 | 同上 | 同 E-SCH-01 | none | 同 E-SCH-01 | 同 E-SCH-01 | 同 E-SCH-01 | — |

Profile 权威：`specs/layer1_axes/sync_scheduler_profiles.yaml`（`daily_close`：baostock + fred incremental；`weekly_backfill`：固定 2024-01-08..12 窗）。

### 1.5b Sibling CLI（不经 RoutePlan 选源 · 须降档登记，防「散文漏表」）

下列命令在 `main.py` `_run_data` 注册，**不**调用 `SourceRoutePlanner` / `enabled_source_registry` 做启用决策；不得用其结果证明策略同路。Gate 1A 选源验收以 §1.2–1.5 为准。

| ID | 入口命令 / 函数 | 调用链（精简） | Owner | 同参输入 | 策略路径 | 档位 | 预期 | 反证 / 降档边界 |
|----|-----------------|----------------|-------|----------|----------|------|------|-----------------|
| E-CLI-40 | `qmd-data data health` → `health_check` | `run_data_health_profile`；禁止 `--allow-network` / clean-write 等 | task-17 邻域；**非** G1-02 选源闭环 | `--domain --profile` | **N/A-POLICY**（只读健康） | 默认只读；契约禁止 live fetch 旗标 | DataHealth 信封；无 `selected_source_id` 策略决定 | 不得当作 RoutePlan / 启用策略证据；带禁旗应失败 |
| E-CLI-41 | `qmd-data data revision-audit` → `revision_audit_plan` | ResourceGuard → orchestrator `run_revision_audit`（默认 dry-run） | task-15/17；非选源 | `--domain --market` · `--lookback-days` | **N/A-POLICY**（修订审计 job，不选 Primary） | `dry_run` 默认 | job 计划/结果；无 registry override | 不得证明 P-* 同路；live 写须另绑存储根档位 |
| E-CLI-42 | `qmd-data data reconcile` → `reconcile_plan` | orchestrator reconcile（常需人工确认） | task-14/17；非选源 | `--conflict-id` | **N/A-POLICY** | `dry_run` 默认 | 冲突处理计划 | 同上 |
| E-CLI-43 | `qmd-data data quality-check` → `quality_check_plan` | orchestrator `run_data_quality`（默认 dry-run） | task-16/17；非选源 | `--domain --date` | **N/A-POLICY** | `dry_run` 默认 | 质量 job 计划 | 同上 |

### 1.6 验收 / 矩阵 spine / ops packaging（非正式产品策略入口 · 降档登记）

| ID | 入口 | 调用链 / 锚点 | 策略路径 | Owner | 档位 | DB / 存储根 | 可观察写入 | 反证 / 降档边界 |
|----|------|---------------|----------|-------|------|-------------|------------|-----------------|
| E-OPS-01 | `qmd-ops db-inspect` → `scripts.qmd_ops:main` | `DbInspector` 只读 | N/A-POLICY | 运维只读 | 只读检查 | 默认 `DATA_ROOT`；可 `--db` / `--data-root` | 无 registry sync | 不得作策略/发布证据 |
| E-OPS-02 | `qmd-ops data -- …` | 转发 `backend.app.cli.main` `["data", *rest]` | **与被转发的 E-CLI-* 相同** | 同对应 data 子命令 | 同被转发命令 | 同被转发命令 | 同被转发命令 | 必须按实际 rest 子命令套用 §1.2–1.5b；禁止因走 `qmd-ops` 包装而换档 |
| E-OPS-03a / E-ACC-02 | `qmd-ops accept-source-route-db --target …` | `_resolve_acceptance_data_root`（assert）→ `spine.execute(..., skip_data_root_validation=False` 默认）→ 内部再 `resolve_matrix_data_root` | 验收 spine；宏源侧常 OVERRIDE | G1-02 知情；**不得**作 G1-08 唯一证据 | `gate_live`（CLI **已** assert；execute **未** skip） | `.audit-sandbox/source-route-db` | report JSON + 可能 sync registry | 不得升格 `product_default`；与危险 skip（E-ACC-SKIP-01）区分 |
| E-OPS-03b | `qmd-ops accept-source-route-db --all-documented-sources` | `_resolve_acceptance_data_root`（assert）→ `execute_documented_matrix`：先 `resolve_matrix_data_root`，再 `_bootstrap_acceptance_db`，再对每行 `spine.execute(..., skip_data_root_validation=True)`（`matrix.py` L761–774） | 同上 | 同上 | `gate_live`（隔离依赖**先验** assert/resolve，**不是** skip 参数本身） | 同上 | matrix report + 共享 cm 上可能已 sync registry | **诚实：** CLI **会**传 skip=True，但是在根已 resolve 之后跳过**重复**校验。skip 行不得单独证明「已隔离」；先验失败则整条不得当 `gate_live`。不得因「传了 skip」误标 `danger_skip_isolation`，也不得升格 `product_default` |
| E-ACC-01 | `phase1_acceptance` / matrix live handlers | **预览：** matrix `preview_route_payload`→`load_incremental_route_bundle`（**含 baostock 在内全部** matrix 目标 = OVERRIDE-MEM）；**live：** 宏源常 OVERRIDE；baostock live 另走专用 builder / PRODUCT-LIVE。`_prepare_phase1_connection`→`ensure_isolated_db` | preview=OVERRIDE-MEM；live=OVERRIDE 或 PRODUCT-LIVE | 登记供 G1-02 清债 | `gate_live` / `override_runtime` | 调用方常先 `require_phase1_data_root_for_live`；**非** `ensure_isolated_db` 内置保证 | acceptance envelope | 不得升格为 `product_default`；勿把「baostock 专用」误读为 preview 也非 OVERRIDE |
| E-ACC-BRIDGE-01 | `source_route_matrix_bridge.run_matrix_spine_for_source` / `try_delegate_tier_acceptance` | `source_route_matrix_bridge.py`：`spine.execute`（默认 skip=False→`resolve_matrix_data_root`）；无 cm 时 `_bootstrap_acceptance_db`→`ensure_isolated_db`→`sync_to_db`；宏源执行侧常 OVERRIDE | 验收 bridge；可写 registry | G1-02 知情；静态 **零外部调用方**（仅文件内自调用） | `gate_live`（若调用方已隔离）或未调用=**dead 可调用面** | 调用方传入的 `data_root`（须隔离约定，API 不保证） | 可能 sync registry + spine report | **须登记：** 零调用≠可省略。删除/迁入正式入口条件：G1-02 后无生产引用则删除模块，或并入 E-OPS-03 文档化调用链；**禁止**口头「没人用」永久漏登 |
| E-ACC-ISO-01 | `ensure_isolated_db` → `_ensure_isolated_db_cached` | `acceptance_isolation.py` L61–88：对传入 `data_root` **无条件** migrate + `sync_to_db(tombstone_missing=True)`；**API 自身不调用** `assert_isolated_live_data_root` | N/A-POLICY（只同步登记） | G1-02 清债知情 | 调用方若已隔离 → 证据可标 `gate_live`；**API 单独调用无档位保证** | DB=`<data_root>/duckdb/quant_monitor.duckdb`（**任意**传入根，含 canonical `data/`） | 该库 registry 行 | **诚实边界：**「调用方应先 assert」只是约定，不是本函数保证。对 canonical 根调用 = 真实写主库风险。禁止把本 helper 单独当作「已隔离」证明 |
| E-ACC-SKIP-01 | `SourceRouteDbAcceptanceSpine.execute(..., skip_data_root_validation=True)` **且调用前未**经 `resolve_matrix_data_root` / `assert_isolated_live_data_root`（或等价） | `source_route_db_acceptance.py` L277–283：直接 `Path(data_root).resolve()`；无 cm 时仍 `_bootstrap_acceptance_db`→`ensure_isolated_db`→`sync_to_db` | 程序化/内部暗门（**非** E-OPS-03b） | 盘点必登；**禁止**发布证据 | **`danger_skip_isolation`** | 可指向非 audit-sandbox / canonical 根仍写库 | 可能写入任意根的 registry | **永久禁止**升格为 `gate_live` / `product_default` / R4 / G1-08。**对照：** E-OPS-03b 虽传 skip=True，但先验已 resolve → 归 E-OPS-03b，不归本行。单目标 CLI（E-OPS-03a）默认 skip=False |

### 1.7 测试专属注入（非生产入口 — 必须处置，不可当发布证据）

| ID | 位置 | 行为 | Owner |
|----|------|------|-------|
| E-TEST-01 | `tests/service_path_support.py` | monkeypatch 启用 source/domain/capability；另有 helper **`sync_to_db(..., tombstone_missing=False)`**（vendor E2E bootstrap） | G1-02 工作包 3：删除/改写/迁到受控配置构造 |
| E-TEST-02 | `tests/test_*_adapters.py` 等 `_enable_*_route` | `object.__setattr__(is_enabled)` | G1-02 测试改写 |
| E-TEST-03 | `tests/support/orchestration_flow_fixtures.py:orch_stack_from_cm` | 直接 `sync_to_db`（常 `tombstone_missing=False`） | 测试夹具；不得作发布证据 |
| E-TEST-04 | `tests/test_sync_orchestrator.py` → `orch.bootstrap(sync_registry=True)` | 覆盖 E-REG-04 | 单元证据 only |
| E-TEST-05 | `tests/test_audit_remediation.py`（如 `test_allowedDomains_dbLoaderRoundTrip`） | 直接 `sync_to_db(..., tombstone_missing=False)` | 测试 only；不得作发布证据 |
| E-TEST-06 | `tests/test_source_registry.py` 多条 `test_syncToDb_*` | 直接测 `sync_to_db` 契约 | 模块单测；证明 API 行为，不证明产品入口同路 |

---

## 2. 候选顺序与回补窗口（配置核实）

### 2.1 增量金路径源 ↔ 规范域（已核实，无歧义）

来源：`backend/app/sync/incremental_source_registry.py`（与 `INCREMENTAL_GOLD_PATH_SOURCE_IDS` 对齐校验）。

| source_id | canonical_domain |
|-----------|------------------|
| baostock | cn_equity_daily_bar |
| mootdx | cn_equity_daily_bar |
| fred | macro_series |
| us_treasury | us_treasury_yield_curve |
| bis | central_bank_policy |
| world_bank | development_indicator |
| cftc_cot | cot_positioning |
| cninfo | cn_announcements |
| sec_edgar | us_filings |
| alpha_vantage | us_equity_daily_bar |
| deribit | crypto_options_surface |

### 2.2 领域候选顺序（registry SSOT）

权威：`specs/datasource_registry/source_registry.yaml` → `domain_roles`。  
运行时解析：`SourceRegistry._parse_domain_role_binding` + `SourceRoutePlanner._ordered_candidates`。

**已核实的解析规则（非猜测）：**

1. 候选链 = `Primary` →（至多一个）`Validation` →（仅当 `use_fallback=True`）`fallback_source_ids` 各为 `FallbackPolicy`。  
2. YAML `validation:` **列表只取第一项**（`_normalize_validation_source`）；其余 validation 源**当前不会**进入 RoutePlan 候选。  
3. `fallback_policy` 为**字符串策略名**时 → `fallback_source_ids=()`；为**源 ID 列表**时 → 填入 `fallback_source_ids`。

**代表域（完整顺序以 YAML 为准）：**

| data_domain | YAML primary | YAML validation 列表 | 运行时 Validation | fallback_policy / ids | domain_enabled_by_default |
|-------------|--------------|----------------------|-------------------|------------------------|---------------------------|
| cn_equity_daily_bar | baostock | [akshare, mootdx] | **仅 akshare** | [qmt_xtdata]（需 use_fallback） | true |
| cn_equity_minute_bar | qmt_xtdata | [] | none | [] | false |
| macro_series | fred | [] | none | [] | false |
| macro_supplementary | akshare | [] | none | use_last_good_cache（无源 ID） | true |
| us_equity_daily_bar | alpha_vantage | [] | none | [] | false |

**与 ADR-017 差距（事实，非 VERIFY）：** ADR 要求「按领域固定次源优先级尝试**所有**合格 Validation」。当前实现只保留 validation 列表首项，且 FallbackPolicy 源默认不进链（除非 `use_fallback`）。**归属 G1-03 / task-02**，不阻塞本清单闭合。

### 2.3 回补 / 恢复窗口

| 问题 | 核实结论 | 证据 | 后续归属 |
|------|----------|------|----------|
| 是否存在「每领域唯一回补缓冲天数」配置表？ | **不存在** | 全库 specs 无 per-domain recovery buffer 表；ADR-017 只规定「按领域频率 + 前后缓冲」，未给数字 | G1-07 实现时按 ADR 规则派生；**禁止**全项目固定天数 |
| scheduler 窗口从哪来？ | profile 内显式日期或 `lookback_days` | `sync_scheduler_profiles.yaml`：`weekly_backfill` 固定 2024-01-08..12；`revision_audit` lookback_days=90 | G1-05 执行 profile，不自造窗 |
| CLI backfill 窗口 | 调用方 `--start/--end` + bounded cap | `data_cli_contract.yaml` / ADR-011 | G1-04 |
| 增量空表 lookback | 代码默认 `empty_table_lookback_days=30`（baostock/mootdx sync） | `data_commands.py` 签名 | 非 ADR-017 恢复窗；勿混用 |

**无用户裁决缺口：** 不存在「两个冲突的唯一数字」需现场拍板；规则已由 ADR-017 给定，数值表尚待 G1-07 落配置（可届时新增 design 字段，经评审）。

---

## 3. 责任矩阵（Gate 1A）

| 任务 | 必须吃进的本清单行 | 验收同参 |
|------|-------------------|----------|
| **task-01 / G1-02** | OVERRIDE-MEM（§1.3–1.4 含 E-CLI-20 全金路径）、E-TEST-*、E-REG-01～04、E-ACC-ISO-01、E-ACC-SKIP-01、E-ACC-BRIDGE-01、E-SVC-01、E-OPS-01～03b；ADR-018 两层接缝 | P-*：允许 / 未授权 / capability 缺失；同 DB 根下 E-REG 行对齐；无先验隔离的 skip 不得当证据；bridge 零调用仍须处置 |
| **task-02 / G1-03** | E-SVC-01 契约；§2.2 多 Validation 全链 | 主源失败只选合格次源 |
| **task-17 / G1-04** | E-CLI-01～30、E-REG-02；E-CLI-40～43 仅降档知情 | 选源命令 ↔ E-SVC-01 同 source/status/reason |
| **task-18 / G1-05** | E-SCH-* | 不自选源；按 profile 窗触发恢复 |

---

## 4. 包装入口登记（pyproject）

| Console script | 目标 | 清单锚点 |
|----------------|------|----------|
| `qmd-data` | `backend.app.cli.main:main` | §1.2–1.5b |
| `qmd-ops` | `scripts.qmd_ops:main` | E-OPS-01～03b（`db-inspect` / `data` 转发 / `accept-source-route-db` 单目标与 matrix） |
| `qmd-init-db` | `scripts.init_db:main` | E-REG-03 |
| `qmd-sync-registry` | `scripts.sync_registry:main` | E-REG-01 |

`qmd-data` 子命令分发：`backend/app/cli/main.py` `_run_data`  
→ 选源相关：route-preview / sync / backfill / full-load / live-fetch / scheduler / incremental（§1.2–1.5）  
→ 非选源降档：init-basic（E-REG-02）/ health / revision-audit / reconcile / quality-check（§1.5b）

程序化 registry 同步：`DataSyncOrchestrator.bootstrap(sync_registry=True)`（E-REG-04）；`ensure_isolated_db`（E-ACC-ISO-01）；无先验隔离的 `skip_data_root_validation`（E-ACC-SKIP-01）；矩阵路径的 skip 复用见 E-OPS-03b；可调用 bridge 见 E-ACC-BRIDGE-01。

契约：`specs/contracts/data_cli_contract.yaml`。权威接缝：ADR-017 + **ADR-018**。

---

## 5. G1-01 闭合声明（相对 r5 + ADR-018）

- [x] 上一轮遗漏的 `qmd-init-db` / `bootstrap` / `ensure_isolated_db` / `qmd-ops` / skip 二分 / sibling CLI / 测试 sync 已有行  
- [x] **r5 CC-5：** E-CLI-20 改为**全金路径 OVERRIDE**（fred 编排壳 vs else ESR；非「fred 专用」）  
- [x] **r5 CC-3：** 登记 `source_route_matrix_bridge`（E-ACC-BRIDGE-01，含零调用仍须处置 / 删除条件）  
- [x] **r5 次要：** E-ACC-01 区分 matrix preview=OVERRIDE（含 baostock）vs live baostock builder  
- [x] **ADR-018：** overlay=`none` 诚实；OVERRIDE→G1-02；E-INC-FRED 标明编排≠启用权威；合并台账 `T01-ENABLE-FRED-MERGE-001`  
- [x] 候选顺序与回补规则已核实  
- [x] 无 `VERIFY_REQUIRED` 单元格  

**下一步：** 开 G1-02 RED（ADR-018 两层接缝 + 清 OVERRIDE，含 E-CLI-20 全金路径；处置 E-ACC-BRIDGE-01）。实现关账须独立 Execute/Audit，pytest/勾选不得单独证明。
