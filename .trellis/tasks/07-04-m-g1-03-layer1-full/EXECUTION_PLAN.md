# EXECUTION_PLAN — M-G1-03（Plan · 唯一执行 SSOT）

> **协议：** Trellis Plan v4.2 · Phase **5e** 产物  
> **票结构：** **B** — 单票 `M-G1-03` · **P1-GATE** 未绿 **禁止** Phase 2 Execute  
> **状态：** **Plan frozen** @ 2026-07-04 · Open Questions **已关闭**（OQ-1A · OQ-2A）  
> **索引：** `EXECUTION_INDEX.md` §0.1 L0–L4 · §1 步骤量化 Done · §2 五列卡 · §3 manifest（Execute 必读 [1]–[8]）  
> **Trellis 任务根：** `.trellis/tasks/07-04-m-g1-03-layer1-full/`  
> **活卡（薄指针）：** `docs/implementation_tasks/M_G1_03_LAYER1_FULL/M_G1_03_LAYER1_FULL.md`  
> **禁止：** 任务拆解、竖切 AC、门禁条件写入其他文件；仅本文件 + 引用的设计权威

---

## Spec: M-G1-03 Layer1 + Sync 架构解耦

### Objective

在 **M-DATA-03 已闭合**前提下，于 **同一 complex 票** 内完成：

1. **Phase 1（阻塞）：** 按 `data_sync_orchestrator.md` **完整**落地同步子系统（Incremental / Backfill / **FullLoad**、§13.6 **调度**、§13.7 CLI、五 job 行为）+ `module_boundary_matrix.md` 边界；建立 **62×指标绑定**机制；消除 Layer 直连抓数与 ops 厚脚本重复。
2. **Phase 2：** 62 个 `indicator_id` 各走 **真 sync → clean → 特征（诚实 NULL）→ 模板解读**，同库可追溯；**G1→R4**。

**用户/验收方：** 运营（CLI/隔离库可查）、Audit（pytest + 边界）、Round4 读模型（字段形状，无 HTTP）。

**不做：** Round4 API/前端、Agent 润色、每轴 1 代表竖切、seed 冒充真 sync。

### Assumptions（显式 — 错请现在纠正）

1. Python 3.x + `uv`；测试 `uv run pytest -q`；隔离库 `.audit-sandbox` + `QMD_DATA_ROOT`。
2. Sync 金路径：`DataSyncOrchestrator` + `DataSourceService`（ADR-025）；生产禁止 `adapter=` 旁路。
3. **FullLoad** 本票 **必须实现**（非 Batch6 defer）；**§13.6 全表调度** 本票 **必须可执行**。
4. 指标绑定矩阵 SSOT：**`specs/layer1_axes/indicator_binding_registry.yaml`**（用户 OQ-2A @ 2026-07-04）。
5. §13.6 调度：**内置** `backend/app/sync/scheduler.py` + profile YAML；宿主 cron **仅**调 `qmd data scheduler run`（用户 OQ-1A @ 2026-07-04）。
6. Trellis 冻结后：`research/to-issues-slices.md` 从本文件 §7 **摘录**，不另写 AC。

### Tech Stack

- Backend: DuckDB · FastAPI（本票不实现路由）· `backend/app/sync/*` · `backend/app/layer1_axes/*`
- Contracts: `specs/contracts/sync_job_contract.yaml` · `module_boundary_contract.yaml` · `bounded_backfill_cap.yaml` · **`data_cli_contract.yaml`**（CLI 扩展须登记）· `layer1_axis_contract.yaml`（P2 读模型/quality_flags）
- 设计权威: `docs/modules/data_sync_orchestrator.md` · `docs/architecture/module_boundary_matrix.md` · `specs/layer1_axes/restructured_axes_v1_1/`

### Commands

> **Source-driven：** 可执行入口以 `pyproject.toml` `[project.scripts]`（`qmd-data`）与 `specs/contracts/data_cli_contract.yaml` 为准；`data_sync_orchestrator.md` §13.7 为语义设计，**不**另起 `python -m quant_monitor.sync` 平行 CLI（One-Version Rule）。

```bash
# 全量验证（关账）
uv run pytest -q
uv run python scripts/check_module_boundaries.py
uv run python scripts/loop_maintain.py

# 矩阵（Plan 冻结时创建）
uv run python scripts/check_indicator_binding_matrix.py
uv run python scripts/check_indicator_binding_matrix.py --strict   # P2-GATE

# Sync CLI — 金路径：qmd-data（= backend.app.cli.main）
uv run qmd-data data sync --source-id fred --dry-run
uv run qmd-data data backfill --domain cn_equity_daily_bar --source-id baostock --start YYYY-MM-DD --end YYYY-MM-DD --dry-run
# Phase 1 新增（须同步 data_cli_contract.yaml）：
# uv run qmd-data data full-load --domain macro_series --start YYYY-MM-DD --dry-run
# uv run qmd-data data scheduler run --profile daily_close --dry-run

# 隔离库 live（env-gated，非默认 CI）
# QMD_ALLOW_LIVE_FETCH=1 QMD_DATA_ROOT=.audit-sandbox/... uv run qmd-data data sync --source-id fred ...
```

### Project Structure（本票触及）

```text
.trellis/tasks/07-04-m-g1-03-layer1-full/
  EXECUTION_PLAN.md          ← 本文件（唯一执行 SSOT）
docs/implementation_tasks/M_G1_03_LAYER1_FULL/
  M_G1_03_LAYER1_FULL.md     ← 薄活卡指针
specs/layer1_axes/
  indicator_binding_registry.yaml   ← 62×矩阵 SSOT（OQ-2A）
  sync_scheduler_profiles.yaml      ← §13.6 profile 配置（OQ-1A）
  restructured_axes_v1_1/           ← 设计权威（只读）
backend/app/sync/
  orchestrator.py · runners.py · watermark.py · scheduler.py（新）
  indicator_binding.py · binding_executor.py · mappers/ · layer1_sync_facade.py（新）
backend/app/layer1_axes/     ← Phase 2 特征/解读；Phase 1 去除 fetch
backend/app/ops/*_incremental_run.py  ← 薄化为 binding 调用方
scripts/check_indicator_binding_matrix.py（新）
specs/contracts/data_cli_contract.yaml   ← full-load / scheduler 扩展登记处
tests/test_sync_* · test_layer1_* · test_indicator_binding_* · test_data_cli_contract.py
```

### Code Style & Patterns

- **解耦：** 三 job 只差 `SyncJobSpec` 时间窗/触发原因；**禁止**在 runner 内写 `indicator_id` 业务分支。
- **绑定：** Layer 用 `sync_indicator`；ops/scheduler 用 `execute_binding`（§9.2 · §10）
- **边界：** `layer*` **不得** `import backend.app.datasources.service`。
- **ponytail:** 先抽 mapper/ watermark 再删 ops 重复；有意简化须注释天花板。
- **改符号前** GitNexus `impact()`；触达 `specs/`/`docs/` 跑 `loop_maintain.py --fix`。

### Testing Strategy

| 层级 | 用途                                            | 位置                                                           |
| ---- | ----------------------------------------------- | -------------------------------------------------------------- |
| 契约 | boundary · sync_job_contract · 矩阵行数         | `tests/test_module_boundaries.py` · `scripts/check_*`          |
| 单元 | watermark · mapper · binding loader · scheduler | `tests/test_sync_*.py`                                         |
| 集成 | orchestrator 五 job · CLI dry-run               | `tests/test_qmd_data_*.py` · `tests/test_sync_orchestrator.py` |
| e2e  | 隔离库 macro→axis_observation；62 指标真链      | `tests/test_layer1_*` · `test_layer1_indicator_binding_*`      |

**五字段：** 每个新 `test_*` 须 docstring 含覆盖范围、对象、目的、验证点、失败含义。

**TDD：** 正式代码先 RED 再 GREEN；Phase 1 gate 前 `uv run pytest -q` exit 0。

### Boundaries

| tier          | 规则                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------- |
| **Always**    | P1-GATE 前不做 Phase 2；不 seed 冒充 sync；不改测试目的换绿；矩阵改一指标不动 orchestrator 核心   |
| **Ask first** | 新第三方依赖；`data_sync_job` 表 DDL 变更；单条 ADR 升格为设计变更                                |
| **Never**     | Layer 直连 vendor；跳过 P1 做 62 指标；每轴 1 代表关账；未登记 ADR 批量 honest-fail；API/前端本票 |

### Success Criteria（关账）

**P1-GATE**

- [ ] `full_load` implemented；`sync_job_contract` 无 reserved full_load
- [ ] Backfill ≥ Tier A 全 canonical domain（含 `macro_series`）
- [ ] §13.7 CLI + §13.6 scheduler 可执行
- [ ] `module_boundary` 绿；layer1 无 datasources fetch（**P1-14 后**）
- [ ] `BindingSyncExecutor` 为 ops/facade/scheduler 唯一编排路径（抽查 `fred_incremental_run` 无内联 orchestration）
- [ ] 62 行矩阵骨架 + `check_indicator_binding_matrix.py` 绿
- [ ] macro_series→axis_observation 隔离库 e2e（非 seed）
- [ ] `uv run pytest -q` exit 0

**P2-GATE**

- [ ] 矩阵 `--strict`；62 指标同库真链
- [ ] G1 **MCR ≥ R4**；`tests/test_layer1_*` 绿

---

## Architecture Decisions（已冻结）

| ID          | 决策                                                                                                                                                                                                           |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AD-MG103-01 | 单票双阶段；P1 阻塞 P2                                                                                                                                                                                         |
| AD-MG103-02 | Incremental / Backfill / FullLoad 共用管道；指标绑定薄层                                                                                                                                                       |
| AD-MG103-03 | FullLoad 本票实现（用户 @ 2026-07-04）                                                                                                                                                                         |
| AD-MG103-04 | §13.6 全表调度本票可执行（用户 @ 2026-07-04）                                                                                                                                                                  |
| AD-MG103-05 | 62 指标全链路；禁止每轴 1 代表                                                                                                                                                                                 |
| AD-MG103-06 | BlindSpot/Forbidden/SHADOW 同管道；不当 primary；诚实降级                                                                                                                                                      |
| AD-MG103-07 | **OQ-1A：** 内置 `sync/scheduler.py` + `specs/layer1_axes/sync_scheduler_profiles.yaml`；host cron 只调 `qmd data scheduler run --profile …`                                                                   |
| AD-MG103-08 | **OQ-2A：** 矩阵 SSOT = `specs/layer1_axes/indicator_binding_registry.yaml`                                                                                                                                    |
| AD-MG103-09 | **契约优先：** 新公开面先 YAML/contract → frozen dataclass → 测试；CLI **只**扩展 `qmd-data` + `data_cli_contract.yaml`；错误统一 `CliFailure`（`docs/ops/ERROR_CODE_GUIDE.md`）                               |
| AD-MG103-10 | **深度模块：** `BindingSyncExecutor`（`sync/binding_executor.py`）为 **唯一** binding→orchestrator 实现；`sync_indicator` / ops / scheduler **只**调 executor，禁止三处复制 watermark+mapper+orchestrator 编排 |
| AD-MG103-11 | **接缝顺序：** P1-04 仅收紧契约+RED 测试；Layer fetch **物理迁出**仅在 P1-14（依赖 facade+executor）                                                                                                           |

---

## Dependency Graph

```text
P1-01..03  矩阵 + boundary 契约
    ↓
P1-04      boundary RED（测试先失败；ingestion 仍可有 fetch 直至 P1-14）
    ↓
P1-05..06  watermark + mappers
    ↓
P1-06′     BindingSyncExecutor（binding→SyncJobSpec→orchestrator）
    ↓
P1-07..09  FullLoad
    ↓
P1-10..12  Backfill 扩域 + ops → executor
    ↓
P1-13      sync_indicator 薄包装（Layer 对外接缝）
    ↓
P1-14      Layer1 去 fetch（boundary GREEN）
    ↓
P1-15..17  CLI + scheduler（经 executor）+ 五 job
    ↓
★ P1-GATE ★
    ↓
P2-01      矩阵 strict
    ↓
P2-02..07  按源批次真链（S08–S12）
    ↓
P2-08..10  特征/解读/读模型
    ↓
★ P2-GATE ★
```

---

## Phase 1 Tasks（Sync 解耦）

### P1-01: 62×矩阵 SSOT 与校验器

- **Acceptance:** 62 `indicator_id` 与 YAML 一一对应；`adr_id` 可 `PENDING`；行 schema 符合 §9.1
- **Verify:** `uv run python scripts/check_indicator_binding_matrix.py`
- **Files:** `specs/layer1_axes/indicator_binding_registry.yaml` · `scripts/check_indicator_binding_matrix.py`
- **Scope:** S · **Deps:** None

### P1-02: Indicator binding registry loader

- **Acceptance:** `@dataclass(frozen=True) IndicatorBinding` 与 §9.1 列一一对应；YAML 在 **loader 边界**校验；未知 `indicator_id` → `UnknownIndicatorError`（含 `error_code=CAPABILITY_MISSING` + `docs_anchor`），禁止裸 `ValueError`
- **Verify:** `uv run pytest tests/test_indicator_binding_registry.py -q`
- **Files:** `backend/app/sync/indicator_binding.py`
- **Scope:** S · **Deps:** P1-01

### P1-03: Module boundary 契约收紧

- **Acceptance:** `layer*` must_not_import `datasources.service`
- **Verify:** `uv run python scripts/check_module_boundaries.py`
- **Files:** `specs/contracts/module_boundary_contract.yaml`
- **Scope:** S · **Deps:** None

### P1-04: Module boundary RED（契约先行）

- **Acceptance:** `module_boundary_contract` 收紧；`check_module_boundaries` / pytest **能检出** layer1 对 `datasources.service` 的 import；**本任务不宣称** ingestion 已迁出（迁出在 P1-14）
- **Verify:** `uv run python scripts/check_module_boundaries.py`（可先 xfail/RED，P1-14 转绿）
- **Files:** `specs/contracts/module_boundary_contract.yaml` · `tests/test_module_boundaries.py`
- **Scope:** S · **Deps:** P1-03

### P1-05: 统一 watermark

- **Acceptance:** `read_watermark(domain, key)` 单一入口；macro+bar
- **Verify:** `uv run pytest tests/test_sync_watermark.py -q`
- **Files:** `backend/app/sync/watermark.py` · ops watermark 改 re-export
- **Scope:** M · **Deps:** None

### P1-06: Domain row mapper 包

- **Acceptance:** `sync/mappers/`；macro_series→axis_observation 单测；mapper **无** orchestrator/watermark 调用（纯函数边界）
- **Verify:** `uv run pytest tests/test_sync_macro_mapper.py -q`
- **Files:** `backend/app/sync/mappers/` · 瘦身 `ops/fred_incremental_run.py`
- **Scope:** M · **Deps:** P1-02

### P1-06′: BindingSyncExecutor（深度模块）

- **Acceptance:** `execute_binding(binding, job_type, *, dry_run, date_start, date_end) -> SyncJobResult` 为 **唯一**「读 binding → 组 SyncJobSpec → watermark → mapper → orchestrator」实现；**删除测试：** 若删 executor 则逻辑散落 ops+facade+scheduler（应集中于此）
- **Verify:** `uv run pytest tests/test_sync_binding_executor.py -q`
- **Files:** `backend/app/sync/binding_executor.py`
- **Scope:** M · **Deps:** P1-02, P1-05, P1-06

### P1-07: FullLoadJobRunner

- **Acceptance:** §13.4.1；断点续跑；无 DeferredJobTypeError
- **Verify:** `uv run pytest tests/test_sync_full_load.py -q`
- **Files:** `backend/app/sync/runners.py` · `orchestrator.py`
- **Scope:** L（可拆 07a/07b）· **Deps:** P1-05, P1-06

### P1-08: sync_job_contract 更新

- **Acceptance:** `full_load` ∈ implemented_job_types
- **Verify:** `uv run pytest tests/test_sync_job_contract.py -q`
- **Files:** `specs/contracts/sync_job_contract.yaml`
- **Scope:** XS · **Deps:** P1-07

### P1-09: FullLoad CLI

- **Acceptance:** `qmd-data data full-load` → `run_full_load`；**登记** `data_cli_contract.yaml`；失败走 `CliFailure`（`error_code` + `docs_anchor` + `retryable`）；语义对齐 `data_sync_orchestrator.md` §13.7 / §13.4.1
- **Verify:** `uv run pytest tests/test_qmd_data_full_load_cli.py tests/test_data_cli_contract.py -q`
- **Files:** `backend/app/cli/data_commands.py` · `specs/contracts/data_cli_contract.yaml`
- **Scope:** M · **Deps:** P1-07, P1-08

### P1-10: Backfill 扩域 Tier A

- **Acceptance:** 全 incremental_source_registry domain；macro 可 backfill；ADR-030 cap 保留
- **Verify:** `uv run pytest tests/test_qmd_data_backfill_cli.py tests/test_bounded_backfill_cap.py -q`
- **Files:** `backend/app/cli/data_commands.py`
- **Scope:** M · **Deps:** P1-06

### P1-11..12: Ops runner 薄绑定（按源分批）

- **Acceptance:** fred/cot/bis/baostock/… **只**解析 source→`IndicatorBinding` 列表或 domain 批次 → 调 `BindingSyncExecutor`；**禁止**内联 orchestration/DDL；`fred_incremental_run.py` LOC 显著下降
- **Verify:** `tests/test_tier_a_live_dispatch.py` · `tests/test_sync_binding_executor.py` · 相关 e2e
- **Files:** `backend/app/ops/*_incremental_run.py`
- **Scope:** M/批 · **Deps:** P1-06′, P1-10

### P1-13: Sync facade（Layer 对外接缝）

- **Acceptance:** `sync_indicator(...)` = `load_binding` + `execute_binding`（§9.2）；**本身不得膨胀**为新 orchestrator；返回 `SyncJobResult`
- **Verify:** `uv run pytest tests/test_layer1_sync_facade.py tests/test_sync_binding_executor.py -q`
- **Files:** `backend/app/sync/layer1_sync_facade.py`
- **Scope:** S · **Deps:** P1-06′, P1-07, P1-10

### P1-14: Layer1 ingestion 迁出 fetch（boundary GREEN）

- **Acceptance:** `ingestion.py` · `ingestion_evidence.py` 无 `datasources.service`；改调 `sync_indicator`；I1–I7 + phase evidence 绿；P1-04 boundary 测试转绿
- **Verify:** `uv run pytest tests/test_module_boundaries.py tests/test_layer1_observation_ingestion.py -q`
- **Files:** `backend/app/layer1_axes/ingestion*.py`
- **Scope:** M · **Deps:** P1-04, P1-13

### P1-15: §13.7 CLI 余量

- **Acceptance:** revision-audit · reconcile · quality-check · incremental --profile
- **Verify:** 各 `tests/test_qmd_data_*.py`
- **Files:** `backend/app/cli/data_commands.py`
- **Scope:** M · **Deps:** P1-07

### P1-16: §13.6 调度器（OQ-1A）

- **Acceptance:** profile 中 `macro_series`/Layer1 项经 **binding registry 展开**为 executor 调用（非硬编码 series 列表）；`scheduler run --profile daily_close` 登记 `data_cli_contract.yaml`；ResourceGuard 跳过非核心
- **Verify:** `uv run pytest tests/test_sync_scheduler.py tests/test_data_cli_contract.py -q`
- **Files:** `backend/app/sync/scheduler.py` · `specs/layer1_axes/sync_scheduler_profiles.yaml` · `backend/app/cli/data_commands.py` · `specs/contracts/data_cli_contract.yaml`
- **Scope:** L · **Deps:** P1-06′, P1-09, P1-15

### P1-17: 五 job 行为对齐 §13.4.4–6

- **Acceptance:** revision_audit/data_quality 非空壳；reconcile datasource_service 金路径或 ADR
- **Verify:** `uv run pytest tests/test_sync_orchestrator.py tests/test_r3f_br_backfill_reconcile_closure.py -q`
- **Scope:** M · **Deps:** P1-15

---

## Phase 2 Tasks（62 指标真链）

**前置：** P1-GATE 全勾。

| ID        | 摘要                           | Verify                                       |
| --------- | ------------------------------ | -------------------------------------------- |
| P2-01     | 矩阵 strict 填满；ADR 逐条     | `check_indicator_binding_matrix.py --strict` |
| P2-02..07 | 按**源域**批次（下表 S08–S12） | 批内 `test_layer1_indicator_binding_*`       |

### Phase 2 源批次清单（Plan 冻结 · 派发 ready-for-agent）

| Slice   | 批次          | `source_id`（Tier A）                 | `canonical_domain`                           | 绑定指标范围                             |
| ------- | ------------- | ------------------------------------- | -------------------------------------------- | ---------------------------------------- |
| **S08** | macro/policy  | fred · us_treasury · bis · world_bank | macro_series 等                              | 矩阵中 `primary_source` 属此四源的全部行 |
| **S09** | positioning   | cftc_cot                              | cot_positioning                              | 同上                                     |
| **S10** | CN bar        | baostock · mootdx                     | cn_equity_daily_bar                          | 同上                                     |
| **S11** | US/crypto bar | alpha_vantage · deribit               | us_equity_daily_bar · crypto_options_surface | 同上                                     |
| **S12** | filings       | cninfo · sec_edgar                    | cn_announcements · us_filings                | 同上                                     |

权威：`backend/app/sync/incremental_source_registry.py`（11 源 SSOT）。每批 AC：批内指标真链 + 同库 lineage；禁止 seed。
| P2-08 | 特征：publish 日 delta · z/分位/state_bucket | `test_layer1_feature_engine.py` |
| P2-09 | 解读：profile + boundary | `test_layer1_interpretation.py` |
| P2-10 | Round4 读模型字段形状（§9.4；无 HTTP） | `test_layer1_round4_read_model_shape.py` |

---

## §7 `/to-issues` 竖切（Issue 发布用）

> Plan 冻结后同步到 `research/to-issues-slices.md` · GitHub/local issue 用 **`ready-for-agent`**（`docs/agents/triage-labels.md`）

| Slice   | Phase       | Blocked by | Triage            | What to build（端到端）                             |
| ------- | ----------- | ---------- | ----------------- | --------------------------------------------------- |
| **S01** | P1          | None       | `ready-for-agent` | 62 行矩阵骨架 + boundary 契约 RED                   |
| **S02** | P1          | S01        | `ready-for-agent` | watermark + mappers + **BindingSyncExecutor**       |
| **S03** | P1          | S02        | `ready-for-agent` | FullLoad runner + contract + CLI                    |
| **S04** | P1          | S02        | `ready-for-agent` | Backfill 扩 Tier A；ops → executor                  |
| **S05** | P1          | S03,S04    | `ready-for-agent` | facade + Layer1 ingestion 迁出 fetch                |
| **S06** | P1          | S05        | `ready-for-agent` | CLI 余量 + scheduler（经 executor）+ 五 job         |
| **—**   | **P1-GATE** | S06        | `ready-for-human` | pytest 全绿 · boundaries · macro e2e · **人工确认** |
| **S07** | P2          | P1-GATE    | `ready-for-agent` | 矩阵 strict + ADR 关账                              |
| **S08** | P2          | S07        | `ready-for-agent` | macro/policy 源批次真链                             |
| **S09** | P2          | S07        | `ready-for-agent` | COT 批次                                            |
| **S10** | P2          | S07        | `ready-for-agent` | CN bar 批次                                         |
| **S11** | P2          | S07        | `ready-for-agent` | US/crypto bar 批次                                  |
| **S12** | P2          | S07        | `ready-for-agent` | filings 批次                                        |
| **S13** | P2          | S08+       | `ready-for-agent` | 特征/解读/读模型 + P2-GATE                          |

### Issue 正文模板（派发 S0x 时）

```markdown
## Parent

M-G1-03 · .trellis/tasks/07-04-m-g1-03-layer1-full/EXECUTION_PLAN.md §7 S0x

## What to build

[从本文件对应 Task 的 Acceptance 改写为端到端行为，不写易腐路径]

## Acceptance criteria

- [ ] 引用 EXECUTION_PLAN P1-xx / P2-xx 全部 AC
- [ ] `uv run pytest -q` 不回归

## Blocked by

- [issue # 或 None]
```

---

## §8 Context Engineering（Execute 按切片加载）

| 切片    | Always load                                                                                     | Task-specific                                                                   |
| ------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 全局    | `EXECUTION_PLAN.md` §Boundaries · `data_sync_orchestrator.md` §13 · `module_boundary_matrix.md` | —                                                                               |
| S01–S04 | 上 + `sync_job_contract.yaml` · `bounded_backfill_cap.yaml`                                     | `indicator_binding_registry.yaml` · `binding_executor.py` · 目标 `ops/*_run.py` |
| S05–S06 | 上 + `data_commands.py` · `data_cli_contract.yaml` · `cli/errors.py`                            | `sync_scheduler_profiles.yaml` · `data_sync_orchestrator.md` §13.6–13.7         |
| S07–S13 | 上 + `restructured_axes_v1_1/README.md` §指标全链路                                             | 批内 YAML spec · `layer1_axes/feature_engine.py`                                |

**禁止：** 一次加载全部 62 指标 YAML；**禁止** Execute 读 `docs/ideas/` 已废弃路径。

---

## §9 Public Interface Contracts（api-and-interface-design · source-driven）

> Execute **先**定契约再写实现。权威来源见下表；与仓库冲突时 **以仓库契约为准** 并回写设计文档（不静默分叉）。

### 9.0 权威来源（source-driven）

| 主题                      | 权威（按优先级）                                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Sync job 类型/状态机      | `specs/contracts/sync_job_contract.yaml` · `backend/app/sync/jobs.py` `SyncJobSpec`                                  |
| CLI 行为与失败信封        | `specs/contracts/data_cli_contract.yaml` · `backend/app/cli/errors.py` `CliFailure` · `docs/ops/ERROR_CODE_GUIDE.md` |
| CLI 可执行入口            | `pyproject.toml` → `qmd-data`（**非** `quant_monitor.sync` 平行命名空间）                                            |
| Orchestrator 语义         | `docs/modules/data_sync_orchestrator.md` §13.4–13.9                                                                  |
| Layer1 指标/quality_flags | `specs/contracts/layer1_axis_contract.yaml` · `layer1_global_regime_panel.md` §6.4–6.5                               |
| 模块 import 边界          | `specs/contracts/module_boundary_contract.yaml`                                                                      |
| 第三方 fetch 载荷         | **不可信** — 仅在 `sync/mappers/*` 边界校验/归一化后再入 staging                                                     |

### 9.1 `indicator_binding_registry.yaml` 行契约（P1-01/02）

每行 **必填**（additive 扩展须改校验器，不得改已有列语义）：

| 列                         | 类型           | 说明                                                                      |
| -------------------------- | -------------- | ------------------------------------------------------------------------- |
| `indicator_id`             | string         | 与五轴 YAML 一致；主键                                                    |
| `axis_id`                  | string         | 所属轴                                                                    |
| `primary_source`           | string         | `source_id`；非 adapter 旁路                                              |
| `data_domain`              | string         | orchestrator domain                                                       |
| `adapter_entry`            | string         | mapper 键                                                                 |
| `cold_start_policy`        | enum           | `full_load` \| `bounded_backfill` \| `incremental_only` \| `adr_deferred` |
| `incremental_watermark`    | string         | watermark 键                                                              |
| `backfill_available`       | bool           | ADR-030 cap 下是否允许 backfill                                           |
| `formula`                  | string \| null | 合成指标引用                                                              |
| `cabin`                    | enum           | `PRIMARY` \| `VALIDATION` \| `BLINDSPOT` \| `FORBIDDEN` \| `SHADOW`       |
| `adr_id`                   | string         | `PENDING` 仅 Phase 1；Phase 2 strict 禁止                                 |
| `feature_outputs_expected` | list[string]   | 预期特征列子集                                                            |

Loader 产出 `IndicatorBinding`（frozen dataclass），字段与上表 1:1。

### 9.2 Layer 同步接缝（P1-06′/13/14 · design-it-twice 结论）

**已评估的接口形状（未采纳原因）：**

| 设计                 | 接口                                       | 结论                                                               |
| -------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| A · 指标接缝（采纳） | `sync_indicator(id, job_type)`             | Layer 只需学 1 个接缝；深度在 executor                             |
| B · 域接缝           | `sync_domain(domain, source_id, job_type)` | ops/scheduler 友好但 Layer 仍须懂 domain；**浅**                   |
| C · 裸 orchestrator  | 各处直接 `run_incremental(SyncJobSpec)`    | 删除测试失败：编排散落 N 处（当前 `fred_incremental_run.py` 痛点） |

**对外（Layer）：**

```python
def sync_indicator(
    indicator_id: str,
    job_type: Literal["incremental", "backfill", "full_load"],
    *,
    dry_run: bool = True,
    date_start: date | None = None,
    date_end: date | None = None,
) -> SyncJobResult: ...
```

**对内（深度模块 · 唯一编排实现）：**

```python
def execute_binding(
    binding: IndicatorBinding,
    job_type: Literal["incremental", "backfill", "full_load"],
    *,
    dry_run: bool = True,
    date_start: date | None = None,
    date_end: date | None = None,
) -> SyncJobResult: ...
```

- `sync_indicator` = `load_binding` + `execute_binding`（**禁止**在 facade 内写源专属逻辑）
- ops runner / scheduler **只**调 `execute_binding` 或批量 helper `execute_bindings_for_source(source_id, …)`
- 未知 `indicator_id` → fail-closed（`CAPABILITY_MISSING`）；禁止 ad-hoc dict 返回
- Layer **仅** import `layer1_sync_facade`；禁止 `DataSourceService`

### 9.3 `sync_scheduler_profiles.yaml`（P1-16）

```yaml
# 最小 profile 形状（可 additive 扩展 optional 字段）
profiles:
  daily_close:
    description: "CN_A + US_EQ bars + Layer1 日频增量"
    jobs:
      - job_type: incremental
        domain: cn_equity_daily_bar
        source_id: baostock
      - job_type: incremental
        domain: macro_series
        source_id: fred
        # Layer1：scheduler 经 registry 展开为 execute_binding 列表，非手写 series
```

- `scheduler run --profile NAME` → 展开 profile → **registry 查 binding** → `execute_binding` 序列
- 单 job 失败不吞异常（CLI → `CliFailure`）

### 9.4 Round4 读模型（P2-10 · 本票无 HTTP）

- **表形状 SSOT：** `layer1_global_regime_panel.md` §6.4 `axis_feature_snapshot` · §6.5 `axis_indicator_profile`
- **quality_flags 枚举：** `layer1_axis_contract.yaml`（含 `INSUFFICIENT_HISTORY` · `BLINDSPOT_NOT_OBSERVABLE` 等）
- 测试断言 **列名+类型** 子集，不实现 REST；Round4 API 另票

### 9.5 CLI 扩展清单（登记 `data_cli_contract.yaml`）

| 命令                          | Phase | 必须                                                                   |
| ----------------------------- | ----- | ---------------------------------------------------------------------- |
| `qmd-data data full-load`     | P1-09 | `--dry-run` 默认；`required_args` 含 `domain`；`must_use` orchestrator |
| `qmd-data data scheduler run` | P1-16 | `--profile` required；`side_effects_allowed` 受 dry-run 控制           |
| 既有 `sync` / `backfill`      | —     | **不改**失败信封；仅扩 domain                                          |

每新增命令须在 `data_cli_contract.yaml` 增加 `required_tests` 行指向对应 pytest。

---

## §10 Module Depth & Seam Map（codebase-design）

> 词汇：**module** · **interface** · **depth** · **seam** · **adapter** · **leverage** · **locality**

### 10.1 目标深度（Phase 1 关账后）

```text
Callers                    Seam (small interface)              Deep implementation
─────────────────────────────────────────────────────────────────────────────────
layer1_axes/*        →     sync_indicator()            →     BindingSyncExecutor
ops/*_run.py         →     execute_binding(s)          →     watermark + mapper + Orchestrator
qmd-data CLI         →     data_commands handlers      →     Orchestrator / scheduler
scheduler            →     run_profile(name)           →     registry expand + executor
```

### 10.2 删除测试（当前浅层 → 目标）

| 若删除…                          | 现况                            | 目标                                              |
| -------------------------------- | ------------------------------- | ------------------------------------------------- |
| `fred_incremental_run.py` 内编排 | 复杂度散落回 ops                | 逻辑已在 `binding_executor`；ops 剩 &lt;50 行绑定 |
| `layer1_sync_facade`             | Layer 须直接懂 SyncJobSpec      | 禁止；Layer 只保留 `sync_indicator`               |
| `binding_executor`               | 编排复制到 facade+ops+scheduler | 禁止；**一处**修 bug                              |

### 10.3 禁止的浅层形状

- facade 内复制 `fred_incremental_run` 的 watermark/staging 逻辑（**pass-through 膨胀**）
- scheduler profile 手写 `indicator_id` 列表与 registry 漂移
- 为通过 boundary 在 layer1 保留 `datasources` import「仅测试用」（迁出统一走 P1-14）

### 10.4 Phase 1 微提交顺序（request-refactor-plan · S02/S05 参考）

1. 矩阵骨架 + checker 绿
2. mapper 纯函数抽出（行为不变）
3. `binding_executor` + 单测（fred 单 series 金路径）
4. `fred_incremental_run` 改调 executor（Tier A 子集仍绿）
5. `sync_indicator` 薄包装
6. layer1 ingestion 删 `DataSourceService` import
7. FullLoad / scheduler 接 executor（非平行编排）

---

## Risks and Mitigations

| Risk                            | Impact | Mitigation                                  |
| ------------------------------- | ------ | ------------------------------------------- |
| FullLoad+Scheduler 体量         | 高     | S03/S06 可再拆；不砍 P1-GATE AC             |
| **浅层 facade**（三处复制编排） | 高     | AD-MG103-10 · §10 · P1-06′ 先于 P1-11/13/16 |
| P1-04/P1-14 顺序误读            | 中     | P1-04 仅 RED；GREEN 仅在 P1-14              |
| 付费墙源                        | 中     | 矩阵 ADR 逐条（`must_wire_all`）            |
| FRED 120d vs 500d 窗            | 中     | FullLoad+backfill；`cold_start_policy` 列   |
| 单票 Audit 过大                 | 中     | Audit 分 P1/P2 证据节                       |

---

## Resolved Decisions（原 Open Questions · 已关闭 @ 2026-07-04）

| ID        | 裁决                                                                         | 落点                                                                               |
| --------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **OQ-1A** | 内置 scheduler + YAML profile；host cron **仅**触发 `qmd data scheduler run` | `backend/app/sync/scheduler.py` · `specs/layer1_axes/sync_scheduler_profiles.yaml` |
| **OQ-2A** | 62×指标绑定矩阵与五轴 spec 同目录                                            | `specs/layer1_axes/indicator_binding_registry.yaml`                                |

未采纳：OQ-1B（纯 crontab 分散调度）· OQ-1C（Dagster/Airflow）· OQ-2B（`specs/contracts/` 矩阵路径）。

---

## Changelog

| 日期       | 变更                                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------------------- |
| 2026-07-04 | §10 深度模块/接缝图；P1-06′ BindingSyncExecutor；依赖图与 P1-04/14 顺序修正；P2 五批次 + triage 列        |
| 2026-07-04 | §9 接口契约 + source-driven 权威表；Commands 改 `qmd-data`；AD-MG103-09                                   |
| 2026-07-04 | OQ-1A · OQ-2A 用户拍板；写入 AD-MG103-07/08                                                               |
| 2026-07-04 | 自 `docs/ideas/m-g1-03-scope-clarification.md` 迁入；加固 SDD/to-issues/context/triage；定为唯一执行 SSOT |
