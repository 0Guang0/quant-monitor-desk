# Audit A5 — AC 追溯 · 独立复验 · 执行偏差

> **维：** A5 (audit-completion)  
> **任务：** `wave4-r3-dcp-05-tier-a` · `plan_protocol_version: 4.1`  
> **分支：** `feature/wave4-r3-dcp-05-tier-a`  
> **日期：** 2026-07-02  
> **模板：** `agents/audit-a5-completion.md`

---

## 维度证据

### 1. git diff（`master...HEAD` + uncommitted）

**已提交（相对 master）：** 93 files，+7062 / -105 行。核心：`migration 015`、11 源 incremental ops/ports、`incremental_source_registry.py`、`clean_write_targets`、11 个 `test_*_incremental_e2e.py`、`test_qmd_data_sync_baostock.py`、`test_tierA_incremental_registry.py` 等。

**未提交（工作区）：**

| 文件                                                                                        | 关联切片 |
| ------------------------------------------------------------------------------------------- | -------- |
| `backend/app/cli/tier_a_sync_router.py`（新）                                               | S12      |
| `backend/app/cli/data_commands.py`、`main.py`                                               | S12 接线 |
| `tests/test_qmd_data_sync_tier_a_router.py`（新）                                           | S12      |
| `specs/datasource_registry/source_{registry,capabilities}.yaml`                             | S13      |
| `docs/ops/data_sync_quick_reference.md`、`docs/architecture/06_deployment_and_local_ops.md` | S13      |
| `tests/test_catalog.yaml`                                                                   | S13      |

审计复验包含未提交文件（mandated pytest 已覆盖 `tier_a_router` 测）。

### 2. 独立 pytest（必跑）

| 命令                                                                                                                             | exit code | 摘要                                          |
| -------------------------------------------------------------------------------------------------------------------------------- | --------- | --------------------------------------------- |
| `uv run pytest tests/test_schema_migration.py tests/test_qmd_data_sync_baostock.py tests/test_qmd_data_sync_tier_a_router.py -q` | **0**     | 40 passed                                     |
| `uv run pytest tests/test_baostock_incremental_e2e.py tests/test_fred_macro_incremental_e2e.py -q`（ENTRY §3 最弱 2）            | **0**     | 12 passed                                     |
| `uv run pytest -q`（活卡 §5 全量）                                                                                               | **0**     | 全绿（3 skipped，与既有 network/opt-in 一致） |
| `uv run pytest tests/test_fred_staged_semantics.py -q`（B2.5-O-05 守门）                                                         | **0**     | 4 passed                                      |
| `uv run python scripts/loop_maintain.py`                                                                                         | **0**     | OK                                            |

### 3. INDEX §2.1 最弱 2 行 — 独立复跑

| 原 §2.1 / ENTRY 行 | 独立复跑命令                                                | exit | 与代码一致                                        |
| ------------------ | ----------------------------------------------------------- | ---- | ------------------------------------------------- |
| baostock clean e2e | `uv run pytest tests/test_baostock_incremental_e2e.py -q`   | 0    | 是 — `run_incremental` → `security_bar_1d` upsert |
| fred macro e2e     | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q` | 0    | 是 — replay `use_mock=True` → `axis_observation`  |

### 4. 活卡 §5 AC 1–5 评分（rubric 1–5）

| #   | 活卡 §5 AC（摘要）                                                               | 追溯链                                                                                                                | 分    |
| --- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ----- |
| 1   | migration 015 应用；`test_schema_migration` / `test_migration_coverage` 绿       | `015_dcp05_tier_a_clean.sql` + 测绿                                                                                   | **5** |
| 2   | `clean_write_targets` 覆盖 11 源 canonical domain                                | `incremental_source_registry.py` ↔ `TIER_A_SOURCES`；`test_tierA_incremental_registry.py` 绿                          | **5** |
| 3   | baostock：`QMD_ALLOW_LIVE_FETCH=1` → `use_mock=False`；关 `ACC-BAOSTOCK-NO-LIVE` | `resolve_baostock_incremental_use_mock()` + `test_qmdData_syncBaostock_liveOptIn_*` 绿；**台账仍 OPEN**（见 finding） | **4** |
| 4   | 11 源各有 watermark 单测 + replay 增量 e2e **写 clean**                          | 11× `test_*_incremental_e2e.py` 存在；弱 2 + 全量 pytest 绿                                                           | **5** |
| 5   | 11 源 `qmd data sync` dry-run 可审计                                             | `tier_a_sync_router.py` + `test_tierASyncRouter_dryRun_allSources_*`（11 源 parametrize）绿                           | **5** |

### 5. AUDIT.plan §2 专项

| 要点                          | 结论                                                                                                                                                                                             |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **baostock live gate**        | `backend/app/ops/baostock_incremental_run.py`：`is_product_live_fetch_allowed()` → `use_mock`；`data_commands.sync_baostock_incremental` 暴露 `product_live`；测覆盖 default false / opt-in true |
| **fred live primary 仍 open** | `docs/UNRESOLVED_ISSUES_REGISTRY.md` `B2.5-O-05` = DEFERRED；`test_fred_staged_semantics.py` 绿；活卡 §6 非目标；**未误关**                                                                      |
| **execution vs slices**       | S00–S11 实现与 `to-issues-slices.md` 对齐；S12 路由器未提交但测绿；**S13 台账关账未完成**（`ACC-BAOSTOCK-NO-LIVE`）                                                                              |

### 6. ACC-BAOSTOCK-NO-LIVE 闭合证据核对

| 证据类型                                                                                                          | 状态                                        |
| ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 代码：`QMD_ALLOW_LIVE_FETCH=1` → `use_mock=False`                                                                 | **满足**                                    |
| 测试：`test_qmdData_syncBaostock_liveOptIn_setsProductLive` / `test_baostockIncremental_resolveUseMock_liveOptIn` | **绿**                                      |
| registry `source_registry.yaml` baostock notes（DCP-05 CLI）                                                      | **已提交**                                  |
| `docs/quality/待修复清单.md` §4 `ACC-BAOSTOCK-NO-LIVE`                                                            | **仍 OPEN**（描述仍写「仍 use_mock=True」） |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                                                                | **无** `ACC-BAOSTOCK-NO-LIVE` 闭合行        |
| AUDIT.plan §3「关：ACC-BAOSTOCK-NO-LIVE」                                                                         | **未文档关账**                              |

### 7. B2.5-O-05（fred live primary）— 必须保持 open

- `待修复清单.md` §6：`B2.5-O-05` 刻意未关闭 → Batch 6 / `R3F-SH-06`
- 独立复验 `test_fred_staged_semantics.py` exit 0
- fred 增量路径默认 replay/mock；registry 仍注「not live FRED primary」

---

## §维度裁决

**FAIL**

（findings 表 1 行非占位）

---

## 计划内问题

| ID        | P   | 标题                                      | 锚点                                                              | 根因                                                        | 修复方案                                                                                                                                                                                                                                       | 验证                                                                                                                    |
| --------- | --- | ----------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| A5-P2-001 | P2  | `ACC-BAOSTOCK-NO-LIVE` 代码已关、台账未关 | `docs/quality/待修复清单.md` §4 L85 · AUDIT.plan §3 · 活卡 §5 AC3 | S13 主会话 registry/docs 关账未执行；实现与 OPEN 行描述脱节 | 主会话 S13：将 `ACC-BAOSTOCK-NO-LIVE` / `LIVE-BAOSTOCK-SYNC-001` 从 §4 移至 `RESOLVED_ISSUES_REGISTRY.md`；更新关闭条件证据（`test_qmd_data_sync_baostock.py` live opt-in + replay smoke）；registry notes 可选补「live gate closed @ DCP-05」 | `rg ACC-BAOSTOCK-NO-LIVE docs/quality` 仅 RESOLVED/历史；`uv run pytest tests/test_qmd_data_sync_baostock.py -q` exit 0 |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`tier_a_sync_router.py` 非 dry-run 仅 baostock/mootdx/fred 接线（其余 `USER_AUTH_REQUIRED`，与 slices S12 dry-run 范围一致）；`B2.5-O-05` 误关路径；baostock `product_live` 默认/ opt-in 分支；11 源 e2e 文件完整性；未提交 diff silent scope 扩大。

---

## 关账摘要

| 项                               | 值                                                                  |
| -------------------------------- | ------------------------------------------------------------------- |
| **findings 数（计划内）**        | 1                                                                   |
| **findings 数（计划外）**        | 0                                                                   |
| **pytest（mandated 子集）**      | exit **0**                                                          |
| **pytest（baostock+fred 弱 2）** | exit **0**                                                          |
| **pytest（全量）**               | exit **0**                                                          |
| **报告路径**                     | `.trellis/tasks/wave4-r3-dcp-05-tier-a/research/audit-a5-report.md` |
