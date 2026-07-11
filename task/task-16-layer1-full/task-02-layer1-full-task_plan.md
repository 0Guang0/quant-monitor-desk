# Implementation Plan: task-02-layer1-full · Phase 1 P1-GATE

> **活文档 SSOT：** 本文件 = 可执行切片 + 验收标准 + Issue 草稿  
> **产品权威：** `PHASE1_PRD.md`  
> **契约权威：** `specs/contracts/data_cli_contract.yaml` · `MIGRATION_MAP.md` 索引设计图  
> **状态台账：** `findings.md` · `progress.md`  
> **历史背景：** `EXECUTION_PLAN.md`（含 Phase 2 · 勿混用）  
> **更新：** 2026-07-09 · **Slice 0 = A（成品纳入 P1）** @ 用户确认  
> **P1-GATE：** **未绿** — 阻塞项 F-07 · F-08 · F-09 · **F-14** · **F-15** · **F-16**（路由/启用轨见 **findings.md §6**）  
> **硬前置：** [`task-01.5-task-02phase1前置阻塞/task_plan.md`](task-01.5-task-02phase1前置阻塞/task_plan.md) 须先关账，方可开工 Slice 0-N

---

## Overview

在 M-DATA-03 已闭合前提下，把四条正式 `qmd-data data` 命令（`sync` / `backfill` / `full-load` / `scheduler`）收敛到 **task-01 生产等价验收库** + **`SourceRouteDbAcceptanceSpine`**，用**同一套** `AcceptanceReport` 证明八步金路径（选路 → 抓数 → raw/staging → 质检 → 冲突 → 写 clean → 下游读）在隔离库上真实可走、失败诚实、不可被 replay/mock/dry-run 冒充 live PASS。

**已完成约 70%：** 正式 CLI 接线、四命令信封统一、baostock 本机真网、`weekly_backfill` live、live/replay 双轨政策均已关账（`findings.md` F-01–F-06、F-10–F-12）。

**剩余工作（Slice 0 已决：A）：** **先** Slice 0-N → **1-E ∥ 1-P ∥ 2a-0** → **Slice 1** → 2a-R1→R2→R3→**R4** + 2a-Q → Slice 3–4。产品形态：**收盘 = A 股 + 宏观**（AD-11 A）；修订链含 **步骤 6 标记**（2a-R4）。

---

## Stack Detected（Source-Driven）

> 框架无关逻辑不引外部文档；**产品/契约决策以仓库权威为准**。

| 项              | 版本/来源                                                                        | 用途                  |
| --------------- | -------------------------------------------------------------------------------- | --------------------- |
| Python          | `>=3.11`（`pyproject.toml`）                                                     | 运行时                |
| pytest          | `>=8.3.0` dev                                                                    | 验收测                |
| DuckDB          | `>=1.1.0`                                                                        | 隔离验收库            |
| 正式 CLI        | `qmd-data` → `backend.app.cli.main:main`（`pyproject.toml` `[project.scripts]`） | One-Version Rule 入口 |
| live-pilot 可选 | `baostock>=0.8.8` 等                                                             | 真网验收              |

**权威引用（实现前必读）：**

| 优先级 | 文档                                                           | 锚点                                                               |
| ------ | -------------------------------------------------------------- | ------------------------------------------------------------------ |
| 1      | `task/task-02-layer1-full/PHASE1_PRD.md`                       | 统一验收接缝 · §162 quality jobs · 用户故事 1–70                   |
| 1      | `specs/contracts/data_cli_contract.yaml`                       | `phase1_gate` · `official_commands_must_expose` · `required_tests` |
| 1      | `docs/decisions/ADR-015-tier-a-live-acceptance-sandbox.md`     | 双轨测试 · `QMD_ALLOW_LIVE_FETCH`                                  |
| 1      | `docs/decisions/ADR-016-source-route-matrix-honest-closure.md` | 诚实关账 · 防假绿                                                  |
| 2      | `docs/modules/data_sync_orchestrator.md`                       | §13.6 调度语义（设计权威）                                         |
| 2      | `specs/contracts/data_quality_rules.yaml`                      | `data_quality` 规则集 · domain 绑定                                |
| 2      | `docs/modules/design/data_validation_and_conflict.md`          | `DataQualityReport` · `data_quality_log`（MIGRATION_MAP 设计权威） |
| 2      | `specs/layer1_axes/sync_scheduler_profiles.yaml`               | `daily_close` / `weekly_backfill` profile                          |

**UNVERIFIED（外部 API）：** baostock / FRED HTTP 行为以各厂商文档为准；本票只约束**产品接缝**如何诚实报告 `BLOCKED` / `FAIL_EXTERNAL`。

---

## Architecture Decisions

### AD-1 · 最高验收接缝（Contract First）

正式命令 **不得** 各自发明验收形状。唯一公开产品接缝：

```text
qmd-data data <sync|backfill|full-load|scheduler>
  → SourceRouteDbAcceptanceSpine / source_route_db_cli_acceptance
  → production-equivalent acceptance DB（QMD_DATA_ROOT 含 source-route-db）
  → AcceptanceReport（+ scheduler 的 parent/child 聚合）
```

**来源：** `PHASE1_PRD.md` §统一验收接口；`data_cli_contract.yaml` `phase1_gate.acceptance_authority`。

### AD-2 · One-Version Rule（CLI）

可执行入口以 `pyproject.toml` `qmd-data` 与 `data_cli_contract.yaml` 为准；禁止平行 `python -m quant_monitor.sync` 类入口作为完成依据。

**来源：** `EXECUTION_PLAN.md` Commands 节；`data_cli_contract.yaml` `rules`。

### AD-3 · 统一错误与状态语义（API / Interface Design）

- **单一信封：** 四条命令均暴露 `acceptance_report`、`gate_eligible`、`observability_evidence`、`failure_class`（`official_commands_must_expose`）。
- **discriminated status：** `PASS` / `FAIL` / `BLOCKED` / `FAIL_EXTERNAL` / `CONTRACT_VIOLATION`；`dry_run` / `replay` / `mock` **不得** 计为 live PASS（`non_gate_evidence`）。
- **scheduler 聚合：** parent `PASS` = 所有 **required** child 均 PASS 或 honest skipped；任一 required child 非 PASS → parent 非 PASS（`PHASE1_PRD.md` §Scheduler）。
- **边界校验：** CLI 参数、env gate、`source_registry` 能力在**系统边缘**校验；内部 orchestrator/runner 信任已验证契约。
- **扩展优先于修改：** 新增可选 profile 字段 / report 字段；不删改已有契约字段类型。

### AD-4 · Live / Replay 双轨（Testing + ADR-015）

- **默认 pytest：** replay/mock · 快、稳、无 key。
- **P1-GATE live：** `QMD_ALLOW_LIVE_FETCH=1` + `source-route-db` 根 + `--no-dry-run`。
- **真网专项：** `@pytest.mark.network` + `--run-network`。
- **禁止：** monkeypatch `_build_datasource_service` 冒充正式路径已接线（F-02 已关闭）。

### AD-5 · Quality Jobs 范围（**已关闭 · 2026-07-09**）

**决策：A · 成品纳入 P1** — `revision_audit` 与 `data_quality` 均为 Phase 1 关账**必做**功能，不得长期 stub，不得 ADR defer。

**用户原话：** Phase 1 关账时二者算必须做完；本阶段做成真能力——能跑、有小票、行为说得清，不是 placeholder。

**来源：** `PHASE1_PRD.md` §162 · 用户确认 @ 2026-07-09。

**Slice 2b（ADR defer）不适用。**

### AD-6 · Quality Job 成品契约（Contract First · **用户确认 @ 2026-07-09**）

> 接口设计原则：与 incremental 相同 **AcceptanceReport** 语义；profile/CLI **边界**校验参数；runner 内信任 `SyncJobSpec`（api-and-interface-design §Validate at Boundaries）。

**`daily_close` 目标形态（两条 quality job 均在本 profile、均 P1 完成，不留给后续 phase）：**

| job_type         | domain                | source     | P1 金路径理由                                                        | core  |
| ---------------- | --------------------- | ---------- | -------------------------------------------------------------------- | ----- |
| `incremental`    | `cn_equity_daily_bar` | `baostock` | 股线抓数                                                             | true  |
| `incremental`    | `macro_series`        | `fred`     | 宏观抓数                                                             | true  |
| `revision_audit` | `macro_series`        | `fred`     | 与宏观增量同域；**P1 必做修订 diff**（非仅 validation）              | false |
| `data_quality`   | `cn_equity_daily_bar` | `baostock` | **用户指定**：本机真网最顺、少 fred key 干扰；规则集 OHLC/缺日更直观 | false |

**来源：** `specs/layer1_axes/sync_scheduler_profiles.yaml`（须扩展）· 用户确认 @ 2026-07-09。

| 能力               | P1 成品定义（可测）                                                                                                      | 权威来源                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| **scheduler 子单** | orchestrator 类 job child 须带 `acceptance_report` + `observability_evidence`（今日缺口：`scheduler.py` L426–435）       | `PHASE1_PRD.md` · `official_commands_must_expose`                              |
| **profile 入参**   | `instrument_id`、`lookback_days`（audit）、检查日/窗口（quality）；`_run_orchestrator_job` 不得写死 `instrument_id=None` | `scheduler.py` L128                                                            |
| **data_quality**   | `DataQualityValidator` + `data_quality_rules.yaml`；`validation_run_ids` 可回填；**daily_close 必含此 job**              | `data_sync_orchestrator.md` §13.4.6 · `data_cli_contract.yaml` `quality-check` |
| **revision_audit** | **修订 diff 成品**（见 AD-7）；非 row-count / 非仅 validation                                                            | `data_sync_orchestrator.md` §13.4.4                                            |
| **CLI 辅路径**     | `revision-audit` / `quality-check` live 与 scheduler 同语义、同 `instrument_id`                                          | `data_commands.py`                                                             |

**非目标（仍属 P1 外）：** 22 源每条都挂进 `daily_close`（`PHASE1_PRD.md` 非目标 §200）；**Phase 2 62-indicator feature engine 实际重算**（≠ 设计 §13.4.3/§13.4.4 步骤 6「标记」；标记见 **2a-R4**）。

### AD-8 · 验收接缝模块正名（**用户确认 @ 2026-07-09**）

**问题：** `backend/app/cli/phase1_acceptance.py` 名含 `phase1`，易被误读为阶段性临时代码；与 `AGENTS.md`「阶段性代码放 `phase-scripts/`」规则冲突感强。该模块实为 **四条正式 `qmd-data data` 命令的生产等价验收接缝**（正式实现，非 `phase-scripts/`）。

**决策：**

| 项                           | 新名称                                                                                                                                                                                                | 依据                                                                                                                                  |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **模块文件**                 | `backend/app/cli/source_route_db_cli_acceptance.py`                                                                                                                                                   | 与 `source_route_db_acceptance.py`（Spine 模型）/ `source_route_db_acceptance_matrix.py` 同族；职责 = CLI 层 source-route-db 验收信封 |
| **信封版本**                 | `REPORT_VERSION = "source_route_db_cli_acceptance_v1"`                                                                                                                                                | 可观测契约字段；与旧 `phase1_acceptance_v1` 一次性迁移（本切片内全量改引用）                                                          |
| **公开函数（同切片一并改）** | `require_source_route_db_data_root_for_live` · `try_resolve_source_route_db_data_root` · `run_source_route_db_sync_live` · `run_source_route_db_backfill_live` · `run_source_route_db_full_load_live` | api-and-interface-design：边界 API 名反映职责，不含里程碑代号                                                                         |
| **不放 `phase-scripts/`**    | —                                                                                                                                                                                                     | 本模块是正式 runtime 接缝；`phase-scripts/` 仅放真·阶段性脚本（须中文退役注释）                                                       |

**来源：** `data_cli_contract.yaml` `phase1_gate.acceptance_authority: SourceRouteDbAcceptanceSpine`（契约里程碑名可保留；**实现模块名**须反映功能）。

### AD-9 · revision 持久化双写（**用户确认 @ 2026-07-09 · OQ-P1-Q5 已关闭**）

**决策：** P1 **必做、不得延后** 的两层存储（缺一即 2a-R2 未关账）：

1. **DuckDB `revision_log` 表**（新 migration）— 主查询/关联面（2a-R3 backfill 关联、行为测断言）
2. **`data/audit/revision_log.ndjson`** — 与表**同步 append** 双写；满足 `specs/contracts/design/log_audit_contract.yaml` `required_logs`

**禁止：** 以「不阻塞 gate」「后续再做」「ponytail 只写表」为由跳过 ndjson；历史多次后置导致遗漏。

**字段权威（设计对齐）：** `docs/modules/design/data_sync_orchestrator.md` §12.5 / §13.4.4 — `content_hash` · `schema_hash` · `revision_id` · `fetch_time` · 标的/观测日 · `instrument_id` · `data_domain` · `source_id`（migration 须覆盖行为测可查列）。

**非主存储：** `manual_review_queue`（`source_object_type='revision'`）仅作需人工介入时的 escalation，**不替代** `revision_log`。

### AD-10 · 多源路由与启用策略（**findings.md §6 · 2026-07-09**）

**权威：** `docs/modules/design/source_route_plan.md` · `data_sources.md` §5.9.1/§573 · `source_route_contract.yaml` · **F-17 按设计**

| 原则                     | 产品含义                                                                                                                     |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **路由已落地**           | `SourceRoutePlanner` + `DataSourceService.fetch` 先 plan 后 fetch；`job_event_log` ROUTE_PLAN；**不等于**「应全开 registry」 |
| **禁止 mass-enable**     | **不得**批量改 `source_registry.yaml` `enabled_by_default: true`；打穿 `test_r3h01_*` 与 `data_sources.md`                   |
| **按源启用**             | READY_WITH_EVIDENCE + DCP-05（Tier A）等：adapter/capability/replay/clean ✓ 后 **逐源** flip；见 **Slice 1-E**               |
| **One-Version 启用接缝** | binding / matrix spine / scheduler **同一** `enabled_source_registry` 语义（**Slice 1** · F-07/F-14）                        |
| **诚实不可用**           | 缺 key / 未授权 / validation-only 当 Primary → `DISABLED_SOURCE` / `USER_AUTH_REQUIRED`（ADR-015/016）                       |

**非目标：** validation-only 源（akshare、yahoo 等）升格为生产 Primary。

### AD-11 · macro_series production-live（**已关闭 · 2026-07-09 · OQ-P1-Q6**）

**用户决议：A** — `macro_series` **纳入** P1 `daily_close` **production-live**，与 `sync_scheduler_profiles.yaml` profile 对齐。

| 项                   | 产品含义                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **生产面**           | `daily_close` = A 股 incremental + **宏观 incremental（core）** + **宏观 revision_audit**                                                                                              |
| **前置满足就应能跑** | `FRED_API_KEY` + `QMD_ALLOW_LIVE_FETCH` + **Slice 1** 统一启用接缝 + **Slice 1-P** registry 域策略落地后，fred child **不得**因域级 `not production-live` / 双轨误报 `DISABLED_SOURCE` |
| **前置缺失仍诚实**   | 缺 key / 无 live 授权 → `BLOCKED` / `USER_AUTH_REQUIRED`（**合法**，非 P1 缺口）                                                                                                       |
| **禁止**             | mass-enable 全 registry；validation-only 源升格 Primary                                                                                                                                |

**实现（Slice 1-P）：** 更新 `source_registry.yaml` · `domain_roles.macro_series`（`domain_enabled_by_default` / `disabled_until_configured` / notes 去 sandbox-only）；fred 源仍 `enabled_by_default: false`，按 **Slice 1-E** 台账逐源 flip。**不**改 `sync_scheduler_profiles.yaml`（已与 A 一致）。

### AD-7 · revision_audit P1 = 修订 diff（可拆小票）

**用户决策：** P1 **必做修订 diff**；可与接缝/触发 backfill 拆成多张 **S–M** 小票。

**设计权威（§13.4.4 RevisionAuditJob）：**

```text
1. 选取 data_domain
2. 重抓小范围历史样本或官方修订窗口
3. 比较 content_hash / schema_hash / revision_id
4. 若变化 → 写 revision_log
5. 创建 BackfillJob
6. 标记受影响 feature / snapshot 需重算
```

**P1 切片映射（纵向、每片可独立验收）：**

| 切片      | 覆盖设计步骤                                                                                                  | P1 必做 |
| --------- | ------------------------------------------------------------------------------------------------------------- | ------- |
| **2a-0**  | scheduler quality child → `AcceptanceReport` 接线（audit + quality 共用）                                     | ✅      |
| **2a-R1** | 步骤 1 + profile/`instrument_id`/lookback + runner 状态机                                                     | ✅      |
| **2a-R2** | 步骤 2–4：修订 diff + **DuckDB `revision_log` 表 + ndjson 双写**（AD-9）                                      | ✅      |
| **2a-R3** | 步骤 5：`revision_detected` → 创建 **BackfillJob**（可观测 job_id，非口头 message）                           | ✅      |
| **2a-R4** | 步骤 6：**标记**受影响 feature / snapshot 需重算（可观测结构化字段；**非** Phase 2 全量 feature engine 执行） | ✅      |

**来源：** `docs/modules/design/data_sync_orchestrator.md` §13.4.4（MIGRATION_MAP 设计权威）。

---

## Dependency Graph

```text
[已完成] CLI 接缝 · 信封 · observability · baostock live
    │
    ├── [已关闭] Slice 0: A · 两条 quality job 均 P1 成品
    │
    ├── Slice 0-N: source_route_db_cli_acceptance 正名（阻塞一切实现切片）
    │
    ├── Slice 1: fred binding 路径（F-07 · F-14）
    ├── Slice 1-E: Tier A 运营启用清单 SSOT（F-16）
    ├── Slice 1-P: macro_series production-live 域策略（F-15）
    │
    ├── Slice 2a-0: scheduler quality child AcceptanceReport 接线（共用）
    │       ├── 2a-R1: revision_audit 接缝 + profile（macro/fred）
    │       ├── 2a-R2: revision diff + revision_log 表 + ndjson 双写
    │       ├── 2a-R3: revision_detected → BackfillJob
    │       ├── 2a-R4: 标记 affected feature/snapshot 需重算（§13.4.4 步骤 6）
    │       └── 2a-Q:  data_quality（cn_equity/baostock · daily_close 新增）
    │
    └── Slice 3 → Slice 4: daily_close 整单复验 → P1-GATE 关账
```

**推荐实施顺序：**

1. **Slice 0-N**（命名卫生 · 须先于改功能）
2. **Slice 1-E** ∥ **Slice 1-P**（可与 2a-0 并行；**文档/决议**，少动核心代码）
3. **Slice 1**（依赖 0-N；**1-P 决议「是」** 时 macro 域 YAML 须在 Slice 3 前落地）
4. **Slice 2a-0**（依赖 0-N；可与 1 / 1-E / 1-P 并行）
5. **2a-R1** → **2a-R2** → **2a-R3** → **2a-R4**（修订 diff 串行；步骤 6 在 R4）
6. **2a-Q**（2a-0 后可并行于 2a-R2/R3/R4）
7. **Slice 3** · **Slice 4**（Slice 3 宏观路径依赖 **Slice 1 + 1-P**）

**并行化：**

| 可并行                                                  | 须串行                                      |
| ------------------------------------------------------- | ------------------------------------------- |
| Slice 1 与 2a-0（**均在 0-N 之后**）                    | **0-N → 其余一切**                          |
| **Slice 1-E** ∥ **Slice 1-P** ∥ **2a-0**（文档/决议轨） | **Slice 3 宏观**依赖 **Slice 1 + 1-P**      |
| 2a-Q 与 2a-R2/R3/R4（2a-0 后）                          | 2a-R1→R2→R3→R4 串行                         |
| operator 文档（P2）                                     | Slice 3 依赖 Slice 1 + 2a-0 + 2a-R\* + 2a-Q |

---

## Project Definition of Done（每切片通用）

每条切片除自身 AC 外，还须满足：

- [ ] 不破坏 `ponytail`：最简 diff、根因一处修、无假绿
- [ ] **Authority Parity（关账硬约束）**：`MIGRATION_MAP.md` 索引的 Phase 1 权威文档凡写明须实现的行为/契约，本票须 **已落地** 或 **按设计**（如 F-17 默认禁用）；**禁止**以 NON-BLOCKING / P2/P3 /「阶段外置」跳过。`ponytail` 只约束**实现手法**（最少代码、可升级路径），**不**缩减已写入切片 AC 或权威文档的完成范围
- [ ] **禁止** mass-enable `source_registry.yaml`（AD-10 · F-17）；按源启用走 **Slice 1-E** 台账
- [ ] 正式代码改动：**先 RED 后 GREEN**（`test-driven-development`）
- [ ] 新/改 `test_*`：**五字段 docstring**（覆盖范围、测试对象、目的、验证点、失败含义）
- [ ] 最高接缝测优先：断言 `AcceptanceReport` / CLI 信封 / DB 证据，**不断言** private helper 调用顺序
- [ ] Mock 仅在**系统边界**（网络 port、时钟）；内部选路/状态机逻辑保持真实
- [ ] `uv run pytest -q` exit 0
- [ ] 改 symbol 前 GitNexus `impact()`；HIGH/CRITICAL 须告知用户
- [ ] 不通过改 `**/design/**` 贴合 runtime 过 parity；漂移用 `promote_design_runtime.py`
- [ ] **AC-CLOSE-1 · 回读对齐**（见下节）：本票 `task_plan.md` + 绑定权威文档完整回读；未做/做一半/与计划或权威不一致 → 补缺修齐，**严格对齐**后方可勾 PASS
- [ ] **AC-CLOSE-2 · 计划外记账**（见下节）：计划外发现/决策/偏离已全部写入 `note.md`

---

## 每切片关账 AC（AC-CLOSE · **绑定全部开放切片**）

> **SSOT：** 下列两条为**每一开放切片** Acceptance criteria 的**强制尾部**（与切片专属 AC 并列，缺一不可）。

### 三文件分工（勿混）

| 文件               | 记什么                                                                                                | 何时写                                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **`task_plan.md`** | 切片 Description · 专属 AC · Verification · 依赖 · **计划内** AD/决策                                 | 计划冻结 / 用户拍板（如 Slice 0 · Quiz）                   |
| **`findings.md`**  | **查码/审计暴露的问题** · P1-GATE 阻塞项 · **计划阶段**已登记 disposition（仍开放 / 已关闭 / 按设计） | 查证、评审、计划修订时；关账时 disposition → 已关闭/按设计 |
| **`note.md`**      | **执行过程中**才出现、**计划与权威均未写明**的发现 · 偏离 · **计划外决策**及验证                      | **仅**切片实现中；勾 PASS 前写入或记 N/A                   |

**规则：** 计划内已决事项进 `task_plan` / `findings`（含 Quiz、AD）；**不要**把应进权威的变更只塞 `note.md`（权威仍须 ADR/用户审阅）。`note.md` **不**替代 `findings.md` 关账 ledger。

### AC-CLOSE-1 · 回读对齐（权威 Parity 复检）

切片自称完成前，执行者须：

1. **完整回读**本票在 `task_plan.md` 中的：Description · Acceptance criteria · Verification · Dependencies · Authority/Files · 绑定 Finding/AD。
2. **完整回读**本票触及的 **MIGRATION_MAP 索引权威**（至少：`PHASE1_PRD.md` · `data_cli_contract.yaml` · 本票改动的 `specs/**` · 本票改动的 `docs/modules/design/**` 等）。
3. **对照结论** — 以下任一成立则 **不得勾本切片 PASS**，须当场修复后重新验证：
   - 执行计划写了，**没做**或**只做一半**
   - 权威文档写了（本票范围内），**没做**或**只做一半**
   - 做了，但与执行计划或权威文档**不一致**（字段语义、错误策略、profile/registry 形状、验收接缝等）
4. **合法例外**（不算缺口）：权威明确允许的诚实 `BLOCKED`/`FAIL_EXTERNAL`（真实前置缺失，如缺 `FRED_API_KEY`）；`findings.md` 已登记 **按设计**（如 F-17 默认禁用）。

### AC-CLOSE-2 · 计划外记账（`note.md`）

本票执行中凡 **执行计划与权威文档均未写明**、但在实现过程中**暴露或决定**的事项，须在勾 PASS 前写入：

`task/task-02-layer1-full/note.md`

**必须包含（产品/业务视角，但技术细节不得省略）：**

| 字段           | 写什么                                           |
| -------------- | ------------------------------------------------ |
| **切片 ID**    | 如 `Slice 1-P`                                   |
| **日期**       | 关账日                                           |
| **暴露的问题** | 用户/运营会看到什么不对；与哪条权威/计划预期不符 |
| **计划外点**   | 为何计划/权威没覆盖（或当时未预见）              |
| **决策**       | 选了什么、未选什么；谁的产品约束驱动             |
| **实现**       | 改了哪些路径/契约/配置；One-Version 接缝如何保持 |
| **验证**       | 哪条测/命令证明决策正确                          |
| **后续**       | 是否影响其他切片/findings（无则写「无」）        |

**禁止：** 口头关账无记账；记账缺决策或缺验证；把应进权威/design 的变更只写 note 而不走审阅（note 仅记**计划外**，权威变更仍须 ADR/用户审阅流程）。

### 切片 AC 引用方式

各开放切片 Acceptance criteria **末尾**须含两条（**第二条无计划外时写 N/A**）：

```markdown
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片全文 + 下列**本切片权威清单**；与计划/权威零缺口（§每切片关账 AC）
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**
```

**勾 PASS 前最小动作：** 打开本切片 → 对照权威清单逐项打勾 → 跑 Verification → 查 `note.md` 是否需记账。

## P1-GATE 总验收（关账清单）

| ID  | 条件                                                                                                    | 契约/证据                                                        |
| --- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| G1  | 四命令统一验收信封                                                                                      | `data_cli_contract.yaml` `official_commands_must_expose`         |
| G2  | live `gate_eligible=true`；无授权 → `BLOCKED`                                                           | `test_qmd_data_*_acceptance.py`                                  |
| G3  | PASS 路径 `observability_evidence` 非空                                                                 | F-03 已关 · 仍须回归                                             |
| G4  | backfill/full-load/scheduler 走同一 source-route-db CLI 接缝                                            | `source_route_db_cli_acceptance.py`（原 `phase1_acceptance.py`） |
| G5  | scheduler parent 诚实聚合                                                                               | `test_sync_scheduler_acceptance.py`                              |
| G6  | quality jobs 成品 + **修订 diff（含步骤 6 标记）** + **daily_close 四 job** + **路由启用轨**（1-E/1-P） | 2a-\* · AD-6/7/10/11                                             |
| G7  | `uv run pytest -q` 全绿                                                                                 | CI                                                               |
| G8  | `findings.md` 每条 disposition ∈ {**已关闭**, **按设计**}；**零**「仍开放」·**零**「阶段外置」          | Authority Parity · 与权威文档一致                                |

---

## 已完成切片（归档 · 勿重开）

| 切片             | Finding   | 证据                                                          |
| ---------------- | --------- | ------------------------------------------------------------- |
| P1-CLI-WIRING    | F-01 F-02 | `a36f905b` · `test_phase1_datasource_service_wiring.py`       |
| P1-ENVELOPE      | F-04      | `test_data_cli_contract.py` · `test_qmd_data_*_acceptance.py` |
| P1-OBS           | F-03      | `_collect_observability_from_job`                             |
| P1-LIVE-HONESTY  | F-05 F-11 | ADR-015/016 · `test_matrix_live_evidence_honesty.py`          |
| P1-BAOSTOCK-LIVE | F-10      | 本机真网 2026-07-09                                           |
| P1-SCHED-WEEKLY  | F-06 部分 | `weekly_backfill` child PASS                                  |

---

## Task List（剩余 · 纵向 Tracer Bullet）

### Slice 0 · Quality Job 范围决策 — **✅ 已关闭**

| 项         | 内容                                                                      |
| ---------- | ------------------------------------------------------------------------- |
| **决策**   | **A · 成品纳入 P1**                                                       |
| **日期**   | 2026-07-09                                                                |
| **含义**   | `revision_audit` + `data_quality` 均为 P1-GATE 必做；须满足 AD-6 成品契约 |
| **不适用** | Slice 2b（ADR defer）                                                     |

**Acceptance criteria:**

- [x] 书面决策：A 成品纳入 P1
- [x] `task_plan.md` AD-5 / AD-6 已更新
- [ ] `findings.md` F-08/F-09 disposition 保持「仍开放」直至 2a-R/2a-Q 关账
- [ ] `progress.md` 反映 Slice 0 决策
- [x] **AC-CLOSE-1 · 回读对齐**：Slice 0 与 AD-5/AD-6/Quiz 一致（2026-07-09 已拍板）
- [x] **AC-CLOSE-2 · 计划外记账**：**N/A** — 计划内用户决议，无执行期计划外

---

### Slice 0-N · `source_route_db_cli_acceptance` 正名（**第一个实现小任务**）

**Description：** 将误导性模块名 `phase1_acceptance.py` 改为反映职责的 **`source_route_db_cli_acceptance.py`**（正式 `qmd-data data` 四条命令的 source-route-db 生产等价验收接缝）。同步改公开 API 中嵌入 `phase1_` 的函数名与 `REPORT_VERSION`。**本模块是正式实现，留在 `backend/app/cli/`**；不得迁入 `phase-scripts/`（该目录仅放真·阶段性脚本）。

**Acceptance criteria:**

- [ ] 文件重命名：`phase1_acceptance.py` → `source_route_db_cli_acceptance.py`；模块 docstring 中文说明职责（生产等价 CLI 验收信封，非阶段性代码）
- [ ] 公开符号重命名（AD-8 表）：`require_source_route_db_data_root_for_live` 等；**无**残留 `from backend.app.cli.phase1_acceptance` import（含 lazy import）
- [ ] `REPORT_VERSION` → `source_route_db_cli_acceptance_v1`；契约测/信封测同步更新
- [ ] 调用方全量更新：`data_commands.py` · `scheduler.py` · `incremental_sync_router.py` · `limited_production_entry.py` · `scripts/check_acceptance_helper_consumers.py` · 全部相关 `tests/*`
- [ ] `task_plan.md` / `progress.md` 引用更新；**不**改 `data_cli_contract.yaml` 的 `phase1_gate` 里程碑键名（契约里程碑 ≠ 模块名）
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-8 · `data_cli_contract.yaml`（`phase1_gate` · `official_commands_must_expose`）· `PHASE1_PRD.md` §统一验收接缝 · 本切片改动后的 `source_route_db_cli_acceptance.py` 与调用方清单
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] `rg phase1_acceptance backend/ tests/ scripts/` **零命中**（`phase1_gate` / `PHASE1_PRD` / 测试文件名 `test_phase1_*` 可保留）
- [ ] `uv run pytest tests/test_data_cli_contract.py tests/test_qmd_data_acceptance_envelope.py tests/test_phase1_observability_evidence.py tests/test_phase1_datasource_service_wiring.py tests/test_bounded_backfill_cli_e2e.py tests/test_sync_scheduler_acceptance.py -q`
- [ ] `uv run pytest -q` exit 0
- [ ] 改前 GitNexus `impact()` 已跑；rename 后 `detect_changes()` 范围符合预期

**Dependencies:** Slice 0 ✅

**Files likely touched（预估 12–15）:**

- `backend/app/cli/phase1_acceptance.py` → `source_route_db_cli_acceptance.py`
- `backend/app/cli/data_commands.py`
- `backend/app/sync/scheduler.py`
- `backend/app/cli/incremental_sync_router.py`
- `backend/app/ops/sandbox_clean_write/limited_production_entry.py`
- `scripts/check_acceptance_helper_consumers.py`
- `tests/test_*`（见上 verification 列表）
- `task/task-02-layer1-full/progress.md`

**Production surfaces:** 四条 `qmd-data data` live 接缝 · scheduler binding/child 信封

**Estimated scope:** M（机械 rename + 全引用；**禁止**夹带功能改动）

**Triage label（实现后）:** `ready-for-agent`

---

### Slice 1 · Scheduler `daily_close` 中 fred live 路径诚实可用

**Description：** `daily_close` 的 fred incremental **有** binding 时走 `resolve_binding_datasource_service` → `_build_datasource_service` → `build_product_live_service`（**非** `execute_fred_matrix_live` / `enabled_fred_source_registry`）。须在 binding 路径对 fred 复用与矩阵一致的启用策略，消除 `DISABLED_SOURCE` 误报。

**GitNexus 佐证：** `enabled_fred_source_registry`（`fred_incremental_watermark.py`）调用方主要为测试与 `_run_fred_macro_live_sync`；scheduler binding **未**调用。

**Acceptance criteria:**

- [ ] fred child `AcceptanceReport` 含完整 `official_commands_must_expose` 字段
- [ ] binding 路径与 matrix spine 对 fred **启用策略一致**（One-Version Rule：一条语义，非两套规则）
- [ ] 无 key / 无 live 授权 → `BLOCKED` 或诚实 external failure，**非** traceback
- [ ] 现有 `test_fredRegistry_disabledByDefault_notProductionLive` 等行为保持或有意更新并文档化
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-10 · `findings.md` F-07/F-14 · `docs/modules/design/data_sources.md` §573 · `docs/modules/design/source_route_plan.md` · `sync_scheduler_profiles.yaml`（`daily_close`）
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED：`test_sync_scheduler_acceptance.py` 新增/扩展 — `daily_close` live fred child 在授权+启用条件下非 `DISABLED_SOURCE`（replay port 可 mock 网络边界）
- [ ] GREEN：实现后上述测试通过
- [ ] Manual：`QMD_ALLOW_LIVE_FETCH=1` + `FRED_API_KEY` + registry 启用策略下 JSON 输出 `failure_class` 诚实
- [ ] `uv run pytest -q` 全绿

**Production surfaces:** `scheduler._run_scheduler_entry` · `execute_spine_or_binding_live` · `resolve_binding_datasource_service` · `enabled_fred_source_registry` · `SourceRoutePlanner.plan`

**Tests strategy（testing-guidelines）:**

- 最高接缝：`qmd-data data scheduler run` → parent/child 信封
- Mock：**仅** fetch port / env；选路与 report 字段不断言 call order
- 五字段 docstring 必填

**Dependencies:** Slice 0-N

**Files likely touched（预估 ≤5）:**

- `backend/app/sync/scheduler.py`
- `backend/app/cli/source_route_db_cli_acceptance.py`
- `backend/app/ops/fred_incremental_watermark.py`（或共享启用 helper）
- `tests/test_sync_scheduler_acceptance.py`

**Finding:** F-07 · **F-14**

**User stories:** #4 统一验收标准 · #58 live 授权门 · #59 blocked sources 诚实

**Estimated scope:** M（3–5 文件）

**Triage label（实现后）:** `ready-for-agent`

---

### Slice 1-E · Tier A 运营启用清单 SSOT（补充 · F-16）

**Description：** 建立 **按源启用** 单一台账（非 mass-enable YAML）：Tier A 11 源 + P1 金路径（fred、baostock）每行记录 adapter/capability/replay/clean 证据、启用前置、flip 条件、owner、关账测。对齐 `data_sources.md` §5.9.1 · ADR-009 · **findings.md §6.4 步骤 2**。

**Acceptance criteria:**

- [ ] 新增活文档 `task/task-02-layer1-full/source_enable_ledger.md`（或 `docs/ops/` 登记路径在 ledger 首行写明）
- [ ] 每源一行：**READY_WITH_EVIDENCE** · DCP-05 canonical domain · clean 表 · replay 路径 · **禁止** bulk `enabled_by_default: true`
- [ ] fred 行 explicit：`FRED_API_KEY` · `QMD_ALLOW_LIVE_FETCH` · **Slice 1-P** 域策略 · **Slice 1** 接缝
- [ ] validation-only 源（akshare、yahoo 等）标 **不得 Primary**，仅 Validation/degraded 路径
- [ ] `findings.md` F-16 disposition → **已关闭**（台账存在且与 registry notes 可交叉核对）
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-10 · `docs/modules/design/data_sources.md` §5.9.1 · `docs/decisions/ADR-009` · `findings.md` §6.4
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] 人工核对：ledger 覆盖 ADR-009 表 11 源 + `daily_close` 涉及的 fred/baostock
- [ ] `task_plan.md` / `progress.md` 索引 ledger 路径
- [ ] **不**要求本切片改 `enabled_by_default` 批量值（违反 AD-10 即 FAIL）

**Dependencies:** Slice 0 ✅（可与 0-N / 2a-0 并行）

**Files likely touched:**

- `task/task-02-layer1-full/source_enable_ledger.md`（新建）
- `task/task-02-layer1-full/findings.md`（F-16 关账）
- `task/task-02-layer1-full/progress.md`（索引）

**Finding:** F-16

**Estimated scope:** S（文档轨 · 无核心代码）

---

### Slice 1-P · `macro_series` production-live 域策略落地（F-15 · **OQ-P1-Q6 = A**）

**Description：** **决议已拍板（A）**：`macro_series` 纳入 P1 `daily_close` production-live，与 profile 对齐。本切片将 `source_registry.yaml` 域策略从 sandbox-only 改为 production-live 语义；**fred 源**仍 disabled-by-default，靠 Slice 1 接缝 + 1-E 台账按源启用。**registry 变更须可审阅**（`MIGRATION_MAP` 索引）。

**Acceptance criteria:**

- [x] **书面决议 A**（AD-11 · Quiz · 用户 @ 2026-07-09）
- [ ] 更新 `source_registry.yaml` · `domain_roles.macro_series`：`domain_enabled_by_default` / `disabled_until_configured` / notes（去「not production-live」；写明 P1 `daily_close` production-live）；**不** mass-enable 其他域或源
- [ ] 增/改 pytest：**默认 registry** 下 macro 域在 scheduler/binding 路径行为与 AD-11 一致；**显式 enable + key** 条件下非误报 `DISABLED_SOURCE`（与 `test_r3h01`「源默认关」共存——测的是**域**与**接缝**，不是 bulk flip）
- [ ] `source_enable_ledger.md`（1-E）fred 行引用本决议：域 production-live · 源仍须 key + 按源 flip
- [ ] `findings.md` F-15 → **已关闭**（registry + 测 + 文档交叉核对）
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-11 · `specs/layer1_axes/sync_scheduler_profiles.yaml` · `specs/datasource_registry/source_registry.yaml`（`domain_roles.macro_series`）· `source_enable_ledger.md`（1-E 交叉）
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] registry diff 可审阅；`uv run pytest tests/test_source_route_planner.py tests/test_sync_scheduler_acceptance.py -q`
- [ ] `uv run pytest -q` 全绿

**Dependencies:** Slice 0 ✅（可与 1-E、0-N 并行；**Slice 3 宏观关账依赖本切片实现完成**）

**Files likely touched:**

- `specs/datasource_registry/source_registry.yaml`（仅 `domain_roles.macro_series`）
- `tests/test_source_route_planner.py` 或 `test_sync_scheduler_acceptance.py`
- `task/task-02-layer1-full/source_enable_ledger.md`（1-E 交叉引用）
- `task/task-02-layer1-full/findings.md`

**Finding:** F-15

**Estimated scope:** S（YAML + 测；决议已完成）

**Open Question:** **OQ-P1-Q6** — **已关闭 · A**

---

### Slice 2a-0 · Scheduler quality child `AcceptanceReport` 接线（共用）

**Description：** 纵向薄片：orchestrator 路径 child 须产出**真实** `AcceptanceReport`（含 `validation_run_ids` / revision 证据），**禁止**沿用 `data_commands.scheduler_run` L1189–1240 对无 `job.acceptance_report` 子任务**手工合成 PASS**（`write_grade=not_written`、`route_plan_id=None`）。`build_scheduler_child_live_envelope` **已存在**，但 orchestrator 路径从未填充 `job.acceptance_report`。

**Acceptance criteria:**

- [ ] quality child **不得**走 synthetic `AcceptanceReport(...)` 分支即标 PASS（对齐 `test_syncSchedulerAcceptance_weeklyBackfillLiveFullLoadChildPass` 对 binding 路径的要求）
- [ ] 新增 `capture_scheduler_quality_child_acceptance`（或扩 `acceptance_report_from_sync_job`）从 `SyncJobResult` + DB 回填证据
- [ ] dry-run / live 语义分离不变
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · `data_cli_contract.yaml` `official_commands_must_expose` · `PHASE1_PRD.md` §Scheduler · 代码核验 **V1**（禁 synthetic PASS）
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED：orchestrator child 当前 `acceptance_report is None`
- [ ] GREEN：scheduler 测断言 child 信封字段 ⊆ `official_commands_must_expose`
- [ ] `uv run pytest tests/test_sync_scheduler_acceptance.py -q`

**Dependencies:** Slice 0-N

**Files likely touched:** `scheduler.py` · `source_route_db_cli_acceptance.py` · `tests/test_sync_scheduler_acceptance.py`

**Estimated scope:** S–M

---

### Slice 2a-R1 · revision_audit 接缝 + profile（macro / fred）

**Description：** `daily_close.revision_audit` 补全 `instrument_id`（如 `DGS10`）；`scheduler._run_orchestrator_job` 传入 profile 字段；`run_revision_audit` 消灭「缺参即 FAIL」——进入 **VALIDATING** 状态机且 child 有 2a-0 小票。本切片**不含**修订 diff 算法。

**Acceptance criteria:**

- [ ] `sync_scheduler_profiles.yaml`：`revision_audit` · `macro_series` / `fred` · `lookback_days` · `instrument_id`
- [ ] live scheduler child 不再因 `instrument_id=None` 失败
- [ ] `qmd-data data revision-audit` live 传递相同 `instrument_id` / lookback 语义
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-7 · `sync_scheduler_profiles.yaml` · `docs/modules/design/data_sync_orchestrator.md` §13.4.4 步骤 1
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED → GREEN：`test_sync_scheduler_acceptance.py` · `test_b3f_quality_runners.py` 扩展
- [ ] `uv run pytest -q`

**Dependencies:** Slice 2a-0

**Finding:** F-08（部分）

**Estimated scope:** S

---

### Slice 2a-R2 · revision diff + revision 持久化（P1 必做）

**Description：** 设计 §13.4.4 **步骤 2–4**。实现 hash 比较 + **AD-9 双写**：新 migration **`revision_log` DuckDB 表**（主存储）+ 每次检出/审计事件 **同步 append** `data/audit/revision_log.ndjson`。比较链复用 `fetch_log.content_hash` / `schema_hash`；`validation_report` 已有。

**Acceptance criteria:**

- [ ] 新 migration：`revision_log` 表（含 `instrument_id` · 观测日 · `content_hash` · `schema_hash` · `revision_id` · `fetch_time` · `data_domain` · `source_id` · `sync_job_id` 等可查列）
- [ ] 测试夹具模拟**同一观测日**（`observation_date` / `trade_date`）下 **`content_hash` 变化** → runner **检出修订**（结果语义反映修订，**非**仅 `COMPLETED` 且无任何 diff 证据）
- [ ] **检出修订时：** DuckDB `revision_log` 有可查询行；**同一事件同步 append** `data/audit/revision_log.ndjson`（字段与表一致或可映射）
- [ ] **检出修订时：** `AcceptanceReport` / `observability_evidence` 含 **`schema_hash` / `content_hash`**（从 `fetch_log` 回填，对齐 `REQUIRED_ACCEPTANCE_REPORT_FIELDS`）及 revision/validation 证据 ID
- [ ] **未检出修订时：** 诚实 **PASS** 且 `observability_evidence` **非空**（`fetch_log_ids` / `validation_run_ids` 等，禁止空壳 PASS）
- [ ] 外网重抓尊重 `QMD_ALLOW_LIVE_FETCH`；pytest **仅在网络边界** mock replay/fixture（不 mock 内部 hash 比较逻辑）
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-9 · `docs/modules/design/data_sync_orchestrator.md` §13.4.4 步骤 2–4 · `specs/contracts/design/log_audit_contract.yaml` `required_logs` · migration `revision_log` 表定义
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED：无 hash 比较；无 `revision_log` 表/ndjson 写入
- [ ] GREEN：行为测断言 — 表行 + ndjson 行 + report hash 字段 + 无修订分支证据非空
- [ ] 契约：`log_audit_contract.yaml` `required_logs` 含 `revision_log.ndjson` 路径在验收根下可验证
- [ ] `uv run pytest -q`

**Dependencies:** Slice 2a-R1 · **OQ-P1-Q5 已关闭（AD-9）**

**Production surfaces:** `QualityJobRunner.run_revision_audit` · revision 持久化写口 · `data/audit/revision_log.ndjson` append

**Finding:** F-08（核心）

**Estimated scope:** M–L（migration + runner + ndjson 双写 + 行为测；超 5 文件则拆 R2a 表/migration vs R2b runner，但**双写同属 P1 不可拆票 defer**）

---

### Slice 2a-R3 · revision_detected → BackfillJob（P1 必做）

**Description：** 设计 §13.4.4 **步骤 5**：当 2a-R2 检出修订，**创建可观测 BackfillJob**（`job_id` 入 `observability_evidence` / job events），`trigger_reason=revision_detected`。步骤 6 由 **2a-R4** 承接。

**Acceptance criteria:**

- [ ] 修订检出 → 新 `backfill` job 行 + 状态机 PLANNED/可执行入口；非仅 log 一行字
- [ ] 未检出修订 → **不**创建 backfill（无假 job）
- [ ] scheduler child / parent 信封可看到关联 backfill `job_id` 或 honest skip
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-7 · `docs/modules/design/data_sync_orchestrator.md` §13.4.4 步骤 5 · `sync/jobs.py` `BACKFILL_TRIGGER_REASONS`
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED → GREEN：orchestrator 行为测 + job 表断言
- [ ] `uv run pytest -q`

**Dependencies:** Slice 2a-R2

**Finding:** F-08（部分；步骤 5）

**Estimated scope:** S–M

---

### Slice 2a-R4 · 标记 affected feature / snapshot 需重算（§13.4.4 步骤 6 · P1 必做）

**Description：** 设计权威 `data_sync_orchestrator.md` §13.4.4 **步骤 6**（及 §13.4.3 BackfillJob 步骤 6 同语义）：`revision_detected` + BackfillJob 创建后，**可观测地标记**受影响 feature / snapshot 进入 `pending` 重算队列。**P1 范围 = 标记契约**（结构化字段 + job events / `observability_evidence`），**非** Phase 2 62-indicator feature engine 实际执行（`PHASE1_PRD.md` 非目标 §196–197）。

**现有接缝（GitNexus）：** `phase1_acceptance._affected_snapshot_mark` 已在 backfill/full-load **CLI 证据**路径产出 `affected_snapshot_recompute`；**revision_audit orchestrator 路径尚未接线**（仅 backfill evidence 有标记）。

**Acceptance criteria:**

- [ ] `revision_detected` 检出且 BackfillJob 已创建 → `observability_evidence` / job events 含 **`affected_snapshot_recompute`**（或权威等价字段）：`status=pending` · `clean_table` / `data_domain` · 可追溯 `revision_id` 或 `sync_job_id`
- [ ] 未检出修订 → **不**产生假标记（`deferred` 或字段缺失，与 backfill 诚实语义一致）
- [ ] scheduler revision_audit child `acceptance_report` 可看到步骤 6 标记证据（经 2a-0 小票，非 synthetic PASS）
- [ ] 与 backfill CLI 路径 **One-Version 标记形状**（复用或提取共享 helper；禁止 revision 与 backfill 两套互不兼容字段）
- [ ] **不**在本切片启动 Phase 2 feature 计算；若代码留升级钩，须 `ponytail:` 注明「标记 vs 执行重算」边界
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · `docs/modules/design/data_sync_orchestrator.md` §13.4.3-6 · §13.4.4-6 · 现有 `_affected_snapshot_mark` / backfill CLI 证据形状 · `PHASE1_PRD.md` 非目标 §196–197
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED：revision_audit 路径无 `affected_snapshot_recompute`（对比 `test_bounded_backfill_cli_e2e` 已有 backfill 标记测）
- [ ] GREEN：orchestrator / quality runner 行为测 + scheduler child 信封断言
- [ ] `uv run pytest -q`

**Dependencies:** Slice 2a-R3 · Slice 2a-0

**Files likely touched:**

- `backend/app/sync/runners.py`（`QualityJobRunner.run_revision_audit`）
- `backend/app/sync/orchestrator.py`
- `backend/app/cli/source_route_db_cli_acceptance.py`（提取/复用 `_affected_snapshot_mark` 或共享模块）
- `tests/test_b3f_quality_runners.py` · `tests/test_sync_scheduler_acceptance.py`

**Finding:** F-08（关账 · 含步骤 6）

**Estimated scope:** S–M

**Authority：** `docs/modules/design/data_sync_orchestrator.md` §13.4.3-6 · §13.4.4-6

---

### Slice 2a-Q · data_quality 成品（cn_equity / baostock · daily_close）

**Description：** profile 用 **`cn_equity_daily_bar`**（与 incremental 一致）；runner/validator 须走既有 domain 映射（`validators/source_conflict.py`：`cn_equity_daily_bar` ↔ `market_bar_1d` 规则集）。**注意：** 当前 `QualityJobRunner._count_rows` 只认 `market_bar_1d`，直接写 profile 域名会 **数不到行**——2a-Q 须一并修 domain 映射。

**Acceptance criteria:**

- [ ] profile 含 `data_quality` 条目（domain/source/instrument_id/检查日或窗口）
- [ ] `run_data_quality` 产出 `DataQualityReport`；`validation_run_ids` 非空（PASS）
- [ ] scheduler child `acceptance_report` 完整；`core: false` 不拉红 parent
- [ ] `qmd-data data quality-check` live 与 profile 语义一致（baostock 股线）
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 本切片 · AD-6 · `specs/contracts/data_quality_rules.yaml` · `docs/modules/design/data_validation_and_conflict.md` · 代码核验 **V3**（`cn_equity_daily_bar` ↔ `market_bar_1d`）
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] RED：profile 无 data_quality 或 stub 行为
- [ ] GREEN：`test_sync_scheduler_acceptance.py` + quality 行为测
- [ ] Manual：本机 `QMD_ALLOW_LIVE_FETCH=1` 跑 `daily_close` 可见 baostock quality child 小票
- [ ] `uv run pytest -q`

**Dependencies:** Slice 2a-0（可与 2a-R2/R3/R4 并行）

**Finding:** F-09

**Estimated scope:** M

---

### ~~Slice 2a-R~~（已拆为 2a-0 · 2a-R1 · 2a-R2 · 2a-R3 · **2a-R4**）

### ~~Slice 2b~~ · ADR defer — **不适用**

### Slice 3 · `daily_close` 整 Profile P1-GATE 复验

**Description：** tracer bullet 关账：Slice 1 + **1-P 决议落地** + 全部 2a 小票完成后，整 profile live 复验；parent/child 信封齐全。宏观路径语义须与 **AD-11 / Slice 1-P** 一致（纳入 production-live 则 fred core 须诚实 PASS 条件；否则宏观 child 诚实非 PASS 且文档化）。

**Acceptance criteria:**

- [ ] `qmd-data data scheduler run --profile daily_close --no-dry-run` parent `gate_eligible=true`（在 source-route-db live 根下；**授权+启用+域策略（AD-11 A）齐全**时宏观 core child 须满足诚实 PASS 条件，不得域级误挡）
- [ ] `daily_close` 含 **4 类 job**：baostock/fred incremental · fred `revision_audit`（含 diff）· baostock `data_quality`
- [ ] 所有 **core: true** child 诚实非假绿；quality child 有完整小票
- [ ] `findings.md` F-06/F-07/F-08/F-09/F-13/F-14/F-15 → **已关闭**；**F-16** 台账已存在
- [ ] **AC-CLOSE-1 · 回读对齐**：回读本切片 + **权威清单**：`task_plan.md` 全依赖链切片 AC · `sync_scheduler_profiles.yaml` `daily_close` · AD-11 · G1–G6 相关契约 · `findings.md` F-06–F-16
- [ ] **AC-CLOSE-2 · 计划外记账**：`note.md` 已追加本切片条目，或 **N/A — 本切片无计划外**

**Verification:**

- [ ] `uv run pytest tests/test_sync_scheduler_acceptance.py -q`
- [ ] Manual JSON：`missing_envelope: []`（父单细节在 `child_envelopes`）
- [ ] 更新 `progress.md` §1–§2

**Dependencies:** Slice 0-N · Slice 1 · **Slice 1-P** · **Slice 1-E**（台账）· 2a-0 · 2a-R1 · 2a-R2 · 2a-R3 · **2a-R4** · 2a-Q

**Estimated scope:** S

---

### Slice 4 · P1-GATE 关账与 Ledger

**Description：** **Authority Parity 关账**：`findings.md` 每条 finding 仅允许 `已关闭` 或 `按设计`；与 `MIGRATION_MAP.md` 索引的 Phase 1 权威文档 **完全一致**（写了就必须做；未做 = 未 PASS）。**不接受**阶段外置、待修复清单 defer、或非 P0/P1 标签豁免。

**Acceptance criteria:**

- [ ] `findings.md` ledger：**零**「仍开放」·**零**「阶段外置」·**零**「待修复」；每条 ∈ {**已关闭**, **按设计**}（含 F-07–F-16 路由/quality 轨）
- [ ] 权威对照：Phase 1 范围内 `PHASE1_PRD.md` · `data_cli_contract.yaml` · `sync_scheduler_profiles.yaml` · `data_sources.md` · `data_sync_orchestrator.md`（§13.4.4 等本票映射切片）· `source_registry.yaml` — **无未实现缺口**（诚实 `BLOCKED`/`FAIL_EXTERNAL` 仅当**真实前置缺失**如缺 key，非 registry 双轨/域策略/product stub）
- [ ] G1–G8 全部勾选
- [ ] `progress.md` P1-GATE → **已绿**
- [ ] **AC-CLOSE-1 · 回读对齐**：**全票**回读 — `task_plan.md` 全文 · `PHASE1_PRD.md` · `data_cli_contract.yaml` · `sync_scheduler_profiles.yaml` · `data_sources.md` · `data_sync_orchestrator.md`（本票映射节）· `source_registry.yaml` · `findings.md` 逐条 ledger · G1–G8
- [ ] **AC-CLOSE-2 · 计划外记账**：全票 `note.md` 条目已闭合，或逐切片 **N/A** 已在 `progress.md` 索引

**Verification:**

- [ ] `uv run pytest -q` exit 0
- [ ] `uv run python scripts/check_module_boundaries.py`（若本票触及边界）
- [ ] 人工：逐条核对 `findings.md` ledger 与上列权威文档（非摘要 PASS）

**Dependencies:** Slice 3

**Estimated scope:** XS

---

## Checkpoints

### Checkpoint α · Slice 0 决策后 — **✅ 已通过**

- [x] Quality job 范围：A 成品纳入 P1
- [x] 切片粒度：2a-0 · 2a-R1–R3 · 2a-Q
- [x] OQ-P1-Q2：`data_quality` → **cn_equity/baostock**
- [x] OQ-P1-Q3：**P1 必做修订 diff**（拆 R2/R3）
- [x] OQ-P1-Q5：**DuckDB 表 + ndjson 双写**（AD-9）
- [ ] **Slice 0-N 完成**（正名后再开 Slice 1 / 2a-0）
- [ ] GitNexus `impact()` 已对 Slice 1 / 2a-R 目标 symbol 跑过（实现前）

### Checkpoint α-N · Slice 0-N 完成后

- [ ] `rg phase1_acceptance backend/ tests/ scripts/` 零命中
- [ ] `uv run pytest -q` 绿
- [ ] `progress.md` 接缝路径更新为 `source_route_db_cli_acceptance.py`
- [ ] **AC-CLOSE-1/2** 已勾（`note.md` 或 N/A）

### Checkpoint β · Slice 1 完成后

- [ ] fred scheduler 路径测绿（binding ≡ matrix 启用语义）
- [ ] `uv run pytest -q` 绿
- [ ] `findings.md` **F-07 · F-14** → 已关闭
- [ ] **AC-CLOSE-1/2** 已勾（`note.md` 或 N/A）

### Checkpoint β-E · Slice 1-E 完成后

- [ ] `source_enable_ledger.md` 存在且覆盖 Tier A + P1 金路径
- [ ] `findings.md` **F-16** → 已关闭

### Checkpoint β-P · Slice 1-P 完成后

- [ ] **OQ-P1-Q6 = A** 已入档（AD-11）；registry + 测已落地
- [ ] `findings.md` **F-15** → 已关闭

### Checkpoint γ · 2a-R2+R3+R4 + 2a-Q 完成后

- [ ] revision diff + **DuckDB `revision_log` + ndjson 双写** 行为测绿
- [ ] `revision_detected` → BackfillJob 可观测
- [ ] **步骤 6**：`affected_snapshot_recompute` 标记可观测（revision 路径）
- [ ] baostock `data_quality` 在 `daily_close` profile 绿
- [ ] `findings.md` F-08/F-09 可关账

### Checkpoint δ · P1-GATE Complete

- [ ] `daily_close` 复验通过（Slice 3）
- [ ] G1–G8 全满足
- [ ] **全票 AC-CLOSE-2**：`note.md` 与 `progress.md` N/A 索引闭合
- [ ] **人类确认可开 Phase 2**

---

## Issue 草稿（to-issues · 暂不发布）

> **用户决定（2026-07-09）：** **暂不**发布到 GitHub 或 `.scratch/`。下表仅作计划内索引；待你明确说「可以发 issue」再双写。

| #      | Title                                  | Blocked by                             | Scope          |
| ------ | -------------------------------------- | -------------------------------------- | -------------- |
| 00     | Rename source_route_db_cli_acceptance  | None                                   | M              |
| 01     | ~~Decide quality scope~~               | —                                      | **已关闭 · A** |
| 02     | Scheduler fred binding（F-07/F-14）    | **#00**                                | M              |
| 02-E   | Tier A source enable ledger            | None                                   | S              |
| 02-P   | macro_series production-live（F-15）   | None                                   | S              |
| 02a-0  | Quality child AcceptanceReport seam    | **#00**                                | S–M            |
| 02a-R1 | revision_audit profile + 接缝          | #02a-0                                 | S              |
| 02a-R2 | revision diff + revision_log 表+ndjson | #02a-R1                                | M–L            |
| 02a-R3 | revision_detected → BackfillJob        | #02a-R2                                | S–M            |
| 02a-R4 | 标记 affected feature/snapshot 重算    | #02a-R3                                | S–M            |
| 02a-Q  | data_quality baostock in daily_close   | #02a-0                                 | M              |
| 04     | daily_close full profile P1-GATE       | #02 · #02-P · #02-E · #02a-\*（含 R4） | S              |
| 05     | P1-GATE ledger close                   | #04                                    | XS             |

---

## Quiz 记录

| 问题                           | 你的决定                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Slice 2a 拆票？                | **是** → 2a-0 · R1·R2·R3 · Q                                                  |
| Slice 0                        | **A · 成品纳入 P1**                                                           |
| `data_quality` 金路径          | **cn_equity / baostock**（daily_close 必含）                                  |
| `revision_audit` 深度          | **P1 必做修订 diff**（R2+R3+**R4 步骤 6 标记**）                              |
| 两条都进 daily_close？         | **是**，均 Phase 1 完成，不留给后续                                           |
| 发 GitHub / `.scratch/`？      | **否**                                                                        |
| `phase1_acceptance.py` 正名？  | **是** → Slice 0-N · `source_route_db_cli_acceptance.py`                      |
| OQ-P1-Q5 revision 存储？       | **DuckDB 表 + ndjson 双写** · P1 必做                                         |
| 路由 mass-enable？             | **禁止**（AD-10 · F-17）· 按源启用 **Slice 1-E**                              |
| macro_series production-live？ | **A · 纳入** · 与 `daily_close` profile 对齐 · **OQ-P1-Q6 已关闭** 2026-07-09 |

**下一步可开工：** **Slice 0-N** → **Slice 1-E ∥ 1-P ∥ 2a-0**（文档/决议可与 2a-0 并行）→ **Slice 1**

---

---

## 代码核验（GitNexus · 2026-07-09 刷新后）

> 索引：`node .gitnexus/run.cjs analyze --force` → **11,758 nodes · 23,546 edges · 300 flows**

### 计划断言 — 属实 ✅

| 断言                                                                 | 证据                                                                                                                                               |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `run_revision_audit` 是 stub（只数行）                               | GitNexus `run_revision_audit` outgoing 仅 `_fail_quality_job`、`_count_rows_for_instrument`；**未**调用 `SyncValidationPipeline`                   |
| `_run_orchestrator_job` 写死 `instrument_id=None`                    | `scheduler.py` L118–130                                                                                                                            |
| orchestrator child 未设 `acceptance_report`                          | `scheduler.py` L425–435 返回 `SchedulerJobResult` 无 report 字段                                                                                   |
| `capture_scheduler_binding_child_acceptance` 存在但 quality 无对等物 | GitNexus：仅 binding incremental/backfill/full*load 调用；**无** `capture_scheduler_quality*\*`                                                    |
| fred binding 与矩阵路径分叉                                          | `execute_spine_or_binding_live` 在「无 binding」incremental 才走；有 binding 时 `resolve_binding_datasource_service` → `_build_datasource_service` |
| `revision_detected` 已在 `BACKFILL_TRIGGER_REASONS`                  | `sync/jobs.py` L84–95                                                                                                                              |
| `data_quality_log` / `validation_report` 表已有                      | `migrations/005_ingestion_validation.sql`                                                                                                          |
| baostock 规则集存在                                                  | `data_quality_rules.yaml` `market_bar_p0` + `cn_equity_daily_bar` binding                                                                          |

### 计划漏洞 / 缺口 ⚠️（须补进切片）

| #      | 缺口                                                                                                                                            | 严重度 | 建议                                                                                      |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------- |
| **V1** | **`scheduler_run` 合成假绿**：无 `job.acceptance_report` 时 L1189–1240 把 `COMPLETED` 合成 `PASS`（`route_plan_id=None`，几乎无 observability） | **高** | 2a-0 必须**禁止** quality job 走该分支；加 RED 测（对标 weekly_backfill 非 synthetic 测） |
| **V2** | **无 `revision_log` DuckDB 表**；`revision_log.ndjson` 未双写                                                                                   | **高** | **已决 AD-9**：2a-R2 表+ndjson 同票必做，禁止 defer                                       |
| **V3** | **`cn_equity_daily_bar` vs `market_bar_1d`**：`QualityJobRunner` 只查 `market_bar_1d`/`macro_series`                                            | **中** | 2a-Q 须 domain 映射；profile 仍用 `cn_equity_daily_bar`                                   |
| **V4** | **双份 `enabled_fred_source_registry`**（`fred_incremental_run.py` vs `fred_incremental_watermark.py`）                                         | **中** | Slice 1 统一 SSOT（矩阵路径用 watermark 版）                                              |
| **V5** | **测试缺口**：无 `daily_close` live `revision_audit`/`data_quality` 非 synthetic 测                                                             | **中** | 2a-0/R/Q 各加 RED                                                                         |
| **V6** | **`revision_audit_plan` / `quality_check` CLI** 仍 `instrument_id=None`                                                                         | **中** | 纳入 2a-R1 / 2a-Q                                                                         |
| **V7** | **2a-R2 重抓样本** 依赖 fred key；与「baostock 金路径」仅覆盖 data_quality                                                                      | **低** | fred audit 用 replay mock 网络；本机 manual 标 fred 前置                                  |

### 计划表述需微调 📝

| 原表述                                 | 核验结论                                                                                                        |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 「scheduler 父单无 acceptance_report」 | **半真**：`scheduler.py` 无，但 `scheduler_run` 会为无 report child **合成** envelope——比「无」更糟（假绿风险） |
| 「2a-0 新建 capture helper」           | **半真**：`build_scheduler_child_live_envelope` 已有；缺的是 **orchestrator 路径填 report + 禁 synthetic**      |
| 「completed 切片 F-01–F-03」           | **仍属实**（未在本轮推翻）                                                                                      |

### Impact（改前必读）

| Symbol                                    | Risk           | 直接上游                                                 |
| ----------------------------------------- | -------------- | -------------------------------------------------------- |
| `DataSyncOrchestrator.run_revision_audit` | LOW · 4        | `scheduler._run_orchestrator_job`、`revision_audit_plan` |
| `run_revision_audit`（runner）            | LOW · 0 direct | 经 orchestrator 委托                                     |

---

## Risks and Mitigations

| Risk                                   | Impact   | Mitigation                                                     |
| -------------------------------------- | -------- | -------------------------------------------------------------- |
| revision diff 无 DB 表/ndjson（V2）    | **High** | AD-9 已关闭；2a-R2 AC 含双写行为测                             |
| synthetic child PASS（V1）             | **High** | 2a-0 显式 FAIL 或 BLOCKED，禁止 route_plan_id=None 的 PASS     |
| domain 别名（V3）                      | Med      | 2a-Q 复用 `source_conflict` 映射                               |
| R2+R3 超 5 文件                        | Med      | 已拆 R1/R2/R3；单票仍超则再拆 fetch vs persist                 |
| fred 修复引入 matrix/binding 双轨回归  | Med      | Slice 1 单一 `enabled_source_registry`；F-14 关账测            |
| 误 mass-enable registry                | **High** | AD-10 · Project DoD 禁止项 · F-17 按设计                       |
| macro_series 域未决议挡 daily_close    | Med      | **OQ-P1-Q6=A 已决** · Slice 1-P 落地 registry                  |
| 本机无 `FRED_API_KEY` 无法 manual live | Low      | replay port 测 + `--run-network` 可选                          |
| GitNexus 索引滞后                      | Low      | 改前 `impact()`；必要时 `node .gitnexus/run.cjs analyze`       |
| 误用 generic `.audit-sandbox` 过 gate  | Med      | `gate_eligible` 契约测已存在；Manual 须含 `source-route-db` 段 |

---

## Open Questions

| ID       | 决策                                                                                                             | 日期                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| OQ-P1-Q0 | A · 成品纳入 P1                                                                                                  | 2026-07-09                                     |
| OQ-P1-Q1 | fred：binding 路径修 `_build_datasource_service`；SSOT=`fred_incremental_watermark.enabled_fred_source_registry` | 开放 · Slice 1                                 |
| OQ-P1-Q2 | **`data_quality` → cn_equity/baostock**；daily_close 必含                                                        | **已关闭** 2026-07-09                          |
| OQ-P1-Q3 | **P1 必做修订 diff**（R2）；BackfillJob（R3）；**步骤 6 标记（R4）**                                             | **已关闭** 2026-07-09 · **R4 补入** 2026-07-09 |
| OQ-P1-Q4 | `instrument_id`：fred 用矩阵 indicator；baostock 用 profile 显式字段                                             | 开放                                           |
| OQ-P1-Q5 | **DuckDB `revision_log` 表 + `revision_log.ndjson` 同步双写**；P1 必做，禁止 defer                               | **已关闭** 2026-07-09 · AD-9                   |
| OQ-P1-Q6 | **A · `macro_series` 纳入 P1 `daily_close` production-live**（AD-11 · 与 profile 对齐）                          | **已关闭** 2026-07-09 · 实现见 Slice 1-P       |

---

## 复验命令 SSOT

```powershell
$env:QMD_DATA_ROOT = ".audit-sandbox/source-route-db-p1-verify"
$env:QMD_ALLOW_LIVE_FETCH = "1"

# 四命令金路径（baostock）
uv run qmd-data data sync --domain cn_equity_daily_bar --no-dry-run --format json
uv run qmd-data data backfill --domain cn_equity_daily_bar --source-id baostock --start 2024-06-01 --end 2024-06-03 --no-dry-run --format json
uv run qmd-data data full-load --domain cn_equity_daily_bar --source-id baostock --start 2024-06-01 --end 2024-06-03 --max-shards 2 --no-dry-run --format json
uv run qmd-data data scheduler run --profile weekly_backfill --no-dry-run --format json

# P1 阻塞复验
uv run qmd-data data scheduler run --profile daily_close --no-dry-run --format json

# 契约回归（data_cli_contract.yaml required_tests 子集）
uv run pytest tests/test_data_cli_contract.py tests/test_qmd_data_sync_acceptance.py tests/test_sync_scheduler_acceptance.py -q

# 关账
uv run pytest -q
```

---

## 文档索引

| 文件                                        | 用途                                  |
| ------------------------------------------- | ------------------------------------- |
| `PHASE1_PRD.md`                             | 产品完成口径                          |
| `findings.md`                               | Finding 台账                          |
| `progress.md`                               | 切片进度                              |
| `note.md`                                   | **计划外决策/偏离记账**（AC-CLOSE-2） |
| `task_plan.md`                              | 执行计划 · **§每切片关账 AC**         |
| `../audit/task-02-layer1-full/Findings.txt` | **已过期**                            |

---

## Plan 自检（planning-and-task-breakdown）

- [x] 每切片有 acceptance criteria
- [x] 每切片有 verification（含 pytest 命令）
- [x] 依赖已排序；checkpoint 每 2–3 切片
- [x] 开放切片 ≤ M（2a-R/2a-Q 各 M）
- [x] 纵向 tracer bullet
- [x] **Slice 0-N 已批准**（正名首任务）
- [x] **Slice 0 已批准 · A 成品纳入 P1**
- [x] **OQ-P1-Q6 = A**（macro production-live）
- [x] **步骤 6 → Slice 2a-R4**（Authority Parity · 非 ponytail defer）
- [x] **AC-CLOSE** 已绑定全部开放切片 AC + `note.md` 记账规则
- [x] **findings.md §6 路由/启用** → AD-10/11 · Slice 1-E/1-P
