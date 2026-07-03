# Audit A5 — AC 追溯 · 独立复验 · 执行偏差

> **维：** A5 (audit-completion)  
> **任务：** `07-02-wave4-r3-dcp-08-layer4` · `plan_protocol_version: 4.1`  
> **分支：** `feature/wave4-r3-dcp-08-layer4`  
> **工作目录：** `quant-monitor-desk-wt-dcp08`  
> **日期：** 2026-07-02  
> **模板：** `agents/audit-a5-completion.md`

---

## 维度证据

### 1. Boot / diff

| 项                               | 证据                                                                                                                                                              |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff master...HEAD`         | 空（本分支相对 master 无已提交 DCP-08 提交）                                                                                                                      |
| `git diff --stat HEAD`（未提交） | 7 tracked files + untracked 新文件（`clean_read.py`、e2e 测、ADR-033、活卡、任务包）                                                                              |
| 已跟踪核心变更                   | `market_structure.py` (+137) · `data_commands.py` (+3 行 dry-run 覆盖) · `test_qmd_data_sync_tier_a_router.py` (+16) · `data_sync_quick_reference.md`             |
| 未跟踪实现                       | `backend/app/layer4_markets/clean_read.py` · `tests/layer4_clean_e2e_support.py` · `tests/test_layer4_clean_read.py` · `tests/test_layer4_us_equity_clean_e2e.py` |
| frozen §5 / 活卡 §5              | 8 条 AC；ENTRY §1 完成条件与 `to-issues-slices.md` 切片表对齐                                                                                                     |
| AUDIT.plan §3 台账               | 关：ACC-MOOTDX · ACC-EASTMONEY(部分) · ACC-LAYER L4；不关：REQ2-EM                                                                                                |

### 2. GitNexus

| 调用                                                                                         | 结果                                                                 |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `query("Layer4 US_EQ clean market structure breadth tier_a_clean", repo=quant-monitor-desk)` | 返回 cross-community 流程；索引未直接命中本票新符号                  |
| `query("sync_mootdx_incremental selected_source_id dry-run", repo=quant-monitor-desk)`       | 未命中 `sync_mootdx_incremental`（索引偏 orchestrator/staged_pilot） |
| `context(USEquityCleanMarketAdapter)`                                                        | **Symbol not found** — `clean_read.py` 为未提交新文件，索引滞后      |

审计以 **代码 Read + pytest** 为主证据；GitNexus 已调用，新符号需 `node .gitnexus/run.cjs analyze` 刷新后方可 `context`/`impact`。

### 3. 独立 pytest（必跑）

| 命令                                                                   | exit code | 摘要                          |
| ---------------------------------------------------------------------- | --------- | ----------------------------- |
| `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q`            | **0**     | 1 passed                      |
| `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` | **0**     | 2 passed                      |
| `uv run pytest tests/test_layer4_market_structure.py -q`               | **0**     | 17 passed（022 无回归）       |
| `uv run pytest -q`                                                     | **0**     | 全绿（~7min；含既有 skipped） |

### 4. INDEX §2 最弱 2 行 — 独立复跑

> 本任务 `EXECUTION_INDEX.md` 无 §2.1；按 A5 规则取 **ENTRY §3 / INDEX §2** 中 tier 较弱、与 Red Flag 相关行。

| 原行（INDEX §2 / ENTRY §3） | 独立复跑命令                                                           | exit | 与代码一致                                                                                                                                                       |
| --------------------------- | ---------------------------------------------------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| US_EQ clean e2e             | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q`            | 0    | 是 — `MarketStructureBuilder.build(source_mode=tier_a_clean)` → `USEquityCleanMarketAdapter` → `security_bar_1d` 聚合；source 无 `staged_fixture`                |
| mootdx dry-run              | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` | 0    | 是 — `sync_mootdx_incremental` dry-run 在 `route_status==READY` 时强制 `selected_source_id=mootdx`（`data_commands.py:553-555`）；live path fail-closed @581-587 |

### 5. 活卡 §5 AC 评分（rubric 1–5）

| #   | 活卡 §5 AC（摘要）                                                     | 追溯链                                                                                                                                                                                                                                      | 分    |
| --- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| 1   | P0 `market_id` 从 clean/日历读入并产出可断言 snapshot                  | `clean_read.py` → `USEquityCleanMarketAdapter` → `MarketStructureBuilder._build_tier_a_clean` → `test_layer4_us_equity_clean_e2e.py` 绿                                                                                                     | **5** |
| 2   | `tests/test_layer4_*_clean_e2e.py` GREEN                               | `test_layer4_us_equity_clean_e2e.py` 独立复跑 exit 0                                                                                                                                                                                        | **5** |
| 3   | `ACC-MOOTDX-DRYRUN-ROUTE-001` dry-run 与 `--source-id mootdx` 路由一致 | `test_tierASyncRouter_dryRun_mootdx_selectedSourceId_aligned` 绿；runtime `validation_only` hack + dry-run 覆盖（`data_commands.py:540-555`）；**registry 仍为 `validation_only: true`**；`registry_proposed_delta.yaml` COORDINATOR-QUEUED | **3** |
| 4   | `ACC-EASTMONEY-TAXONOMY-001` notes 更新（不关 REQ2-EM）                | `docs/ops/data_sync_quick_reference.md` §ACC-EASTMONEY；`source_registry.yaml` eastmoney notes 含 ACC 指针；`registry_proposed_delta.yaml` EM 段 queued；REQ2-EM 仍 §3 open                                                                 | **4** |
| 5   | `ACC-LAYER-E2E-LIVE-001` L4 子集关账                                   | `l4-e2e-live-evidence.md` [x] + e2e pytest 绿；**`待修复清单.md` §4 行未记 L4 子集已关**                                                                                                                                                    | **4** |
| 6   | `reference-adoption-dcp08.md` 含 L1/L2/L3                              | `research/execute-reference-read-evidence-s08.md` 存在；非 A5 主判据                                                                                                                                                                        | **4** |
| 7   | Plan v4.1 包齐；`validate-plan-freeze`                                 | 任务包齐；Execute handoff 未在本维复跑                                                                                                                                                                                                      | **4** |
| 8   | `uv run pytest -q` exit 0                                              | 独立全量复跑 exit 0                                                                                                                                                                                                                         | **5** |

### 6. AUDIT.plan §2 A5 专项

| 要点                    | 结论                                                                                                                 |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **mootdx dry-run 对齐** | dry-run JSON `selected_source_id==mootdx` 测绿；依赖 runtime overlay，非 registry reconcile                          |
| **REQ2-EM 仍 open**     | `docs/quality/待修复清单.md` §3 `R3-B2.75-REQ2-EM` 仍在；ops/registry notes 均写「不关 REQ2-EM」；**未误关** ✓       |
| **diff silent scope**   | 变更限于 Layer4 clean + mootdx router + ops 文档 + catalog；无 CN_A full slice / migration / 参考项目 runtime import |

### 7. 台账关账证据核对（AUDIT.plan §3）

| 台账 ID                                | 代码/测证据                                                                                       | registry / 文档关账                                                                                                                                                   | 裁决                               |
| -------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| **ACC-MOOTDX-DRYRUN-ROUTE-001**        | `test_tierASyncRouter_dryRun_mootdx_selectedSourceId_aligned` 绿；dry-run 覆盖 + live fail-closed | `source_registry.yaml` mootdx 仍 `validation_only: true`（L298-299）；`registry_proposed_delta.yaml` merge gate [ ]；`待修复清单` §4 L91 仍 OPEN；runtime hack 未移除 | **行为已对齐，台账/registry 未关** |
| **ACC-EASTMONEY-TAXONOMY-001**（部分） | ops §ACC-EASTMONEY 新增；registry notes 已含 taxonomy 指针                                        | §4 L90 行内注明「部分 notes ✅；不关 REQ2-EM」；proposed delta queued                                                                                                 | **部分关账达标**（张力行保留合理） |
| **ACC-LAYER-E2E-LIVE-001** L4          | `l4-e2e-live-evidence.md` L4 [x]；e2e pytest 绿                                                   | §4 L92 仅记 L1 已关、L3–L5 open，**未记 L4 US_EQ 子集 @ DCP-08**                                                                                                      | **证据齐，台账行未更新**           |
| **R3-B2.75-REQ2-EM**                   | —                                                                                                 | §3 仍 open；活卡 §6 非目标                                                                                                                                            | **正确保持 open** ✓                |

---

## §维度裁决

**FAIL**

（§计划内 2 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                            | 锚点                                                                                                                                                                                                         | 根因                                                                                                                                                                                | 修复方案                                                                                                                                                                                                                                                   | 验证                                                                                                                                                                                                                                                    |
| --------- | --- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A5-P2-001 | P2  | `ACC-MOOTDX-DRYRUN-ROUTE-001` dry-run 已对齐、registry/台账未关 | `data_commands.py:540-555` · `specs/datasource_registry/source_registry.yaml` mootdx L288-302 · `registry_proposed_delta.yaml` merge gate · `待修复清单.md` §4 L91 · `to-issues-slices.md` S08-REG-MOOTDX AC | Execute 以 runtime `validation_only` 提升 + dry-run `selected_source_id` 覆盖达成测绿；registry delta 按 B3F-REG 仅 proposed、主会话未 apply；切片 AC 要求 registry 反映后去掉 hack | 主会话 coordinator：apply `registry_proposed_delta.yaml` mootdx 段（`validation_only: false` + notes）；移除 `object.__setattr__(validation_only, False)`；将 `ACC-MOOTDX-DRYRUN-ROUTE-001` 从 §4 移至 `RESOLVED_ISSUES_REGISTRY.md` 并附 router test 证据 | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` exit 0；`rg "validation_only: true" specs/datasource_registry/source_registry.yaml` mootdx 段为 false；`rg ACC-MOOTDX-DRYRUN-ROUTE-001 docs/quality/待修复清单.md` 无 §4 open 行 |
| A5-P2-002 | P2  | `ACC-LAYER-E2E-LIVE-001` L4 子集证据齐、§4 台账未记关账         | `research/l4-e2e-live-evidence.md` L27 · `tests/test_layer4_us_equity_clean_e2e.py` · `待修复清单.md` §4 L92 · AUDIT.plan §3                                                                                 | S08-L4-E2E-LEDGER 产出 evidence md + pytest，但未回写 §4 行关闭条件（L4 US_EQ clean→snapshot→lineage）                                                                              | 更新 `待修复清单.md` §4 `ACC-LAYER-E2E-LIVE-001` 行：追加「**L4 US_EQ 子集已关 @ R3-DCP-08**」+ 证据指针（e2e pytest + `l4-e2e-live-evidence.md`）；L3–L5 全链仍标 open；可选同步 `RESOLVED_ISSUES_REGISTRY.md` L4 子集行                                  | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q` exit 0；`rg "L4 US_EQ" docs/quality/待修复清单.md` 命中 DCP-08 关账注记                                                                                                                     |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/layer4_markets/` · `backend/app/cli/data_commands.py`（mootdx 段）· `specs/datasource_registry/` · `docs/ops/data_sync_quick_reference.md` · `docs/quality/待修复清单.md` §3-§4 · `tests/test_layer4_*` · `tests/test_qmd_data_sync_tier_a_router.py` · 对照 DCP-05 `audit-a5-report.md` 台账关账模式。除 §计划内 registry/台账脱节外，未发现活卡 Red Flag（staged 冒充、REQ2-EM 误关、参考项目 runtime import）或 scope creep。

---

## Verification Story

- **Tests reviewed:** yes — S08 切片五字段 docstring 与 AC 对齐；e2e 断言 breadth + 无 `staged_fixture`
- **Build verified:** yes — INDEX §2 最弱 2 行 + 全量 `uv run pytest -q` 独立 exit 0
- **Security checked:** yes — clean 路径只读 sandbox DuckDB；REQ2-EM 硬约束保持 open

### What's Done Well

- **US_EQ 竖切闭环**：`clean_read.py` → adapter → `tier_a_clean` builder 路径可独立 pytest 绿，022 staged 默认路径未破坏。
- **mootdx dry-run 可审计**：显式 `--source-id mootdx` 时 JSON `selected_source_id` 与 CLI 一致，live path fail-closed。
- **ACC-EASTMONEY 部分关账**：ops SSOT + registry notes + 明确不关 REQ2-EM，符合活卡 §3/§6。
- **L4 证据链可读**：`l4-e2e-live-evidence.md` 四步 seed→read→build→assert 与测试文件一一对应。
