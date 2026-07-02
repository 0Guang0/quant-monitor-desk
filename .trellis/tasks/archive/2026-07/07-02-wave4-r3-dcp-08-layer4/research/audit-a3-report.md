# Audit A3 — Security（R3-DCP-08 Layer4）

> **维：** A3 · **任务：** `07-02-wave4-r3-dcp-08-layer4` · **协议：** v4.1  
> **日期：** 2026-07-02 · **分支：** `feature/wave4-r3-dcp-08-layer4`（未提交变更面）  
> **模板：** `agents/security-auditor.md` · **权威：** `agents/audit-adversarial-authority.md`  
> **工作目录：** `quant-monitor-desk-wt-dcp08`

---

## 维度证据 §3.3

### 范围与 diff

| 类别 | 路径 | 角色 |
|------|------|------|
| 新增 | `backend/app/layer4_markets/clean_read.py` | US_EQ clean read（只读 SQL） |
| 修改 | `backend/app/layer4_markets/market_structure.py` | `source_mode=tier_a_clean` 分支 |
| 修改 | `backend/app/cli/data_commands.py` | `sync_mootdx_incremental` dry-run JSON + `validation_only` mutation |
| 新增/改 | `tests/test_layer4_clean_read.py` · `test_layer4_us_equity_clean_e2e.py` · `layer4_clean_e2e_support.py` | 测试 bootstrap |
| 修改 | `tests/test_qmd_data_sync_tier_a_router.py` | ACC-MOOTDX dry-run 断言 |
| 文档 | `docs/decisions/ADR-033-*.md` · `docs/ops/data_sync_quick_reference.md` | 双轨 primary 语义 |

**diff 基线：** `git diff`（相对 `master` 无已提交分叉；审计面 = 上述未提交变更 + AUDIT Trace Authority）。

### 静态命令（A3 基线 + 任务面）

| 动作 | 范围 | 证据 |
|------|------|------|
| `rg 参考项目 backend/app/layer4_markets/` | runtime import | **0 命中** |
| `rg 参考项目 backend/app/cli/data_commands.py` | runtime import | **0 命中** |
| `rg "import.*参考\|sys\.path.*参考" backend/app/layer4_markets/` | 旁路 import | **0 命中** |
| SQL f-string 扫描 `backend/app/layer4_markets/` | 注入面 | **0 命中**；`clean_read.py:33-43` · `107-118` 使用 `?` 绑定 |
| 密钥/URL 扫描 layer4 变更面 | 泄露 | **0 命中** |
| `subprocess` / `eval` / `exec` · layer4 | 命令执行 | **0 命中** |
| `writer(` / `INSERT` / `apply_migrations` · `clean_read.py` | 未授权写 | **0 命中**（只读聚合） |
| `enable.qmt` / `xqshare` · 变更面 | live 源旁路 | **0 命中** |
| `object.__setattr__` · `data_commands.py` | registry mutation | **1 命中** L543（`validation_only`） |
| `enabled_source_registry` · `sync_mootdx_incremental` | 禁用源覆写 | L539–546 全路径调用 |

### GitNexus（索引 stale · 新符号未收录）

| 调用 | 结果 | 用途 |
|------|------|------|
| `query` — layer4 US equity clean read | 命中 validation_gate / write_manager 流；**未**索引 `USEquityCleanMarketAdapter` | 写路径旁路上下文 |
| `query` — sync_mootdx route preview | 命中 `DataSourceService.preview_route` | mootdx 路由链 |
| `context(USEquityCleanMarketAdapter)` | Symbol not found | 新文件未 analyze |
| `context(sync_mootdx_incremental)` | Symbol not found | 同上 |

> 静态结论以 **rg + 源码 Read** 为准；GitNexus 作调用图补位，不以索引缺失为 PASS。

### 信任边界核对（AUDIT.plan §2 · ENTRY §2 · ADR-033）

| 威胁面 | 核对 | 结论 |
|--------|------|------|
| **AUDIT A3：无 `参考项目` runtime import** | `backend/**` 变更面 0 import；`execute-reference-read-evidence-s08.md` L3 greenfield | **PASS** |
| Layer4 `tier_a_clean` 写库 | `_build_tier_a_clean` 仅读 `clean_con`；无 `writer`/`INSERT` | **PASS** |
| SQL 注入 | 谓词参数化；`market_id`/`trade_date` 绑定 | **PASS** |
| mootdx registry SSOT | 生产 YAML 仍 `validation_only: true`；runtime `enabled_source_registry` + L543 `__setattr__` | **FAIL**（见 P1） |
| dry-run 审计 JSON | L554–555 覆写 `selected_source_id`；对比 bis `DISABLED_SOURCE` 负向测 | **FAIL**（见 P2） |
| 非 dry-run 写 clean | `assert_sandbox_db_allowed` + `_require_baostock_sync_operator_or_sandbox` + `user-live` 拒绝 | **PASS**（sandbox 链完整） |
| mootdx live fetch | `resolve_mootdx_incremental_use_mock()` → `is_product_live_fetch_allowed()` | **PASS**（ADR-027 gate 保留） |
| fixtures 密钥 | 测试 bootstrap 无真实 API key | **PASS** |

### DOUBT 三类对抗搜索

| 类 | 范围 | 结论 |
|----|------|------|
| 硬编码 URL 变体 | `clean_read.py` · `market_structure.py` · `data_commands.py`（mootdx 段） | **无发现** — 无新增 outbound URL |
| JWT / API key 模式 | 同上 + `layer4_clean_e2e_support.py` | **无发现** |
| SQL 拼接 | `clean_read.py` 全文件 | **无发现** — 仅 `?` 绑定 |

### §3.3 威胁摘要

| 威胁 | 发现 | P | 证据 |
|------|------|---|------|
| 参考项目 runtime 渗入 | 无 | — | `rg` backend 变更面 0 命中 |
| registry 禁用/validation_only 旁路 | 有 | P1 | `data_commands.py:539-543` · `source_registry.yaml:288-299` |
| dry-run 审计 JSON 覆写 organic route | 有 | P2 | `data_commands.py:553-555` |
| SQL 注入 · 密钥落盘 · live 源默认开 | 无 | — | rg 扫描 |
| tier_a_clean 未授权写库 | 无 | — | `clean_read.py` 只读 |

### 正向观察

- `USEquityCleanMarketAdapter` / `aggregate_breadth_from_bars` 仅 `SELECT`，空 bar 集 `Layer4MarketError` fail-closed（`clean_read.py:44-47`）。
- `MarketStructureBuilder.build(source_mode=tier_a_clean)` 限制 `market_id=="US_EQ"`，拒绝未知 `source_mode`（`market_structure.py:199-212`）。
- `_reject_future_observation` 在 clean 路径保留（calendar + breadth）。
- mootdx 非 dry-run 仍经 `assert_sandbox_db_allowed` + sandbox/operator 双门禁；`user-live` 路径拒绝（`tier_a_sync_router.py:37-42`）。
- `test_tierASyncRouter_dryRun_disabledRegistry_failClosed` 对 **bis** 证明生产 registry fail-closed 模式存在，可复用到 mootdx 负向。

---

## §维度裁决

**FAIL**

（§计划外 2 行非占位 finding；§计划内 AUDIT 点名项 PASS）

---

## 计划内问题

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| — | — | 无 | — | — | — | — |

**AUDIT.plan §2 A3 核对：** `backend/**` 变更面无 `参考项目` runtime import / `sys.path` 耦合 — 满足活卡 `reference-adoption-dcp08.md` §0 铁律。

---

## 计划外发现

| ID | P | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| A3-P1-001 | P1 | mootdx 增量路径 runtime 覆写 registry SSOT（`validation_only` / `is_enabled`），与生产 YAML 漂移 | `data_commands.py:539-543` · `macro_incremental_common.py:87-110` · `specs/datasource_registry/source_registry.yaml:288-299` · `research/registry_proposed_delta.yaml`（COORDINATOR-QUEUED） | `sync_mootdx_incremental` 入口固定调用 `enabled_source_registry`（强制 `is_enabled=True` + domain primary=mootdx）并 `object.__setattr__(..., "validation_only", False)`；生产 registry 仍标 mootdx 默认禁用且 validation-only；proposed delta 未 merge。dry-run 无对比 bis 的 `DISABLED_SOURCE` 负向测（`test_qmd_data_sync_tier_a_router.py:124-135` 仅覆盖 bis） | 主会话按 `registry_proposed_delta.yaml` apply registry 三件套后 **删除** L543 `__setattr__` 与重复 enable hack；`enabled_source_registry` 仅用于测试或显式 opt-in 路径；新增负向：`sync_tier_a_by_source_id(source_id="mootdx", dry_run=True)` **无** monkeypatch 时须 `DISABLED_SOURCE` 或文档化 ADR-033 显式例外并在 ops SSOT 标明 | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k "mootdx or disabledRegistry" -q`；`rg "object\.__setattr__.*validation_only" backend/app/cli/data_commands.py` → 0 命中（registry apply 后） |
| A3-P2-001 | P2 | dry-run JSON 在 `preview_route` 之后强制 `selected_source_id=mootdx`，审计轨迹不反映 organic 路由决策 | `data_commands.py:549-555` · ADR-033 §Decision-5 | `route_status==READY` 时将 `preview["selected_source_id"]` 覆写为 `"mootdx"`，即使 `DataSourceService.preview_route` 返回 domain default primary（baostock）；运维 JSON 无法区分「路由自然选中」与「事后覆写」 | 在 registry apply 后让 mootdx-scoped registry 使 `preview_route` **原生** 返回 `selected_source_id=mootdx`（见 `registry_proposed_delta.yaml` §Runtime）；删除 L554-555 覆写；payload 增加 `route_primary_source_id`（organic）与 `effective_source_id`（CLI）双字段若仍需双轨语义 | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py::test_tierASyncRouter_dryRun_mootdx_selectedSourceId_aligned -q`；静态：`preview["selected_source_id"]` 赋值仅来自 `plan.selected_source_id`（无 post-override） |

已对抗搜索：`backend/app/layer4_markets/**` · `backend/app/cli/data_commands.py`（`sync_mootdx_incremental` 全函数）· `backend/app/ops/macro_incremental_common.py` · `tests/test_layer4_clean_read.py` · `tests/test_layer4_us_equity_clean_e2e.py` · `tests/test_qmd_data_sync_tier_a_router.py` · `specs/datasource_registry/source_registry.yaml` · `docs/decisions/ADR-033-dcp08-layer4-us-eq-clean-read.md` · GitNexus `query`×2 · DOUBT 三类 rg。
