# Phase 1 完成度清单（防遗漏 SSOT）

> **用途：** 独立于 `task_plan.md` 的**全量统计台账**；重写执行计划时**以本文件为核对底稿**，避免丢项。  
> **权威来源：** `PHASE1_PRD.md` · `task-02-layer1-full-task_plan.md` · `task-02-layer1-full-findings.md` · `specs/contracts/data_cli_contract.yaml` · `sync_scheduler_profiles.yaml`  
> **编制：** 2026-07-10  
> **维护规则：** findings disposition 变更 · 切片关账 · 计划修订后，**同步更新本文件对应行**；关账前逐项勾选 §9 总表。

---

## 0. Phase 1 到底要完成什么（产品一句话）

**把四条正式数据命令（`sync` / `backfill` / `full-load` / `scheduler`）统一到 task-01 的「生产等价验收库」上**，用同一套 `AcceptanceReport` 证明八步金路径在隔离库上**真实可走、失败诚实、不可被 replay/mock/dry-run 冒充 live PASS**；其中 **`daily_close` 调度 profile 整单过关**是 tracer bullet 关账代表。

**做到什么程度 = R4 产品形态**（代码与设计/契约一致），**不是** R5 运维（监控、runbook、告警等）。

**明确不做（Phase 1 非目标）：**

- Phase 2 的 62 指标 feature engine **实际重算**（revision 步骤 6 只做**标记**，不做重算执行）
- 22 个数据源**每条**都 live PASS 或都挂进 `daily_close`
- 批量 `enabled_by_default: true` 全开 registry
- validation-only 源（akshare、yahoo 等）升格为生产 Primary
- R5：dashboard、SLO、pager、长期监控、operator 全套文档

---

## 1. 关账硬标准（P1-GATE · G1–G8）

| ID     | 关账条件                                                                              | 当前状态                               | 主要 Finding / 切片                         |
| ------ | ------------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------- |
| **G1** | 四命令统一验收信封（`official_commands_must_expose` 七字段齐全）                      | ✅ 已满足                              | F-04 已关闭                                 |
| **G2** | live 路径 `gate_eligible=true`；缺授权 → `BLOCKED`（非 traceback）                    | ⚠️ 部分路径未验完                      | F-01 · F-07                                 |
| **G3** | PASS 路径 `observability_evidence` **非空**                                           | ❌ 未满足                              | **F-03 复核重开**                           |
| **G4** | backfill/full-load/scheduler 走同一 CLI 验收接缝                                      | ⚠️ 模块仍名 `phase1_acceptance.py`     | Slice **0-N**                               |
| **G5** | scheduler parent **诚实聚合**（required child 非 PASS → parent 非 PASS）              | ⚠️ 机制有；quality child 可能合成 PASS | F-06 部分 · Slice **2a-0**                  |
| **G6** | quality jobs 成品 + 修订 diff（含步骤 6 标记）+ `daily_close` **四 job** + 路由启用轨 | ❌ 未满足                              | F-07–09 · F-14–16 · 2a-\* · Slice 1/1-E/1-P |
| **G7** | `uv run pytest -q` exit 0                                                             | ✅ 当前绿（关账时仍须复验）            | —                                           |
| **G8** | `findings.md` **每条** ∈ {已关闭, 按设计}；**零**仍开放/阶段外置                      | ❌ **15 项仍开放** + 1 项部分仍开放    | 见 §4                                       |

**P1-GATE 总状态：❌ 未绿**

---

## 2. 八步金路径 · 模块完成度

> 链路 SSOT：`PHASE1_PRD.md` · `data_sync_orchestrator.md`  
> 状态图例：**✅ 成品** · **⚠️ 有机制/有缝** · **❌ 未成品/阻塞** · **📋 按设计**（非缺陷）

| 步骤 | 模块 / 能力                                | P1 要求程度                         | 当前状态                                  | Finding / 备注                  |
| ---- | ------------------------------------------ | ----------------------------------- | ----------------------------------------- | ------------------------------- |
| 0    | **source_registry / capabilities**         | 路由前可读；默认不全开              | 📋 大量 `disabled_by_default` **按设计**  | F-17；启用走 F-16 台账          |
| 1    | **SourceRoutePlanner** → SourceRoutePlan   | 先 plan 后 fetch；可审计 ROUTE_PLAN | ✅ 成品                                   | F-12：22 源矩阵有证据           |
| 2    | **DataSourceService**（产品 fetch 边界）   | 正式路径不得直调 adapter            | ⚠️ binding 路径 registry 注入不一致       | F-07 · F-14                     |
| 3    | **fetch port / adapter** → raw + fetch_log | 真 fetch 写 raw 证据                | ⚠️ 部分入口 `fetch_port is required` 崩溃 | **F-01**                        |
| 4    | **staging**                                | 来自真实 fetch，非 seed 造假        | ✅ 金路径有（baostock 本机已证）          | F-10                            |
| 5    | **DataQualityValidator**                   | clean 写前执行；quality job 须真跑  | ❌ `run_data_quality` 空壳                | **F-09** · Slice **2a-Q**       |
| 6    | **SourceConflictValidator**                | 严重冲突阻塞或 reconcile            | ✅ 机制有（金路径已走）                   | —                               |
| 7    | **WriteManager**（唯一 clean 写边界）      | 带 lineage、role、hash              | ✅ 金路径有                               | task-01.5 S7 已降复杂度         |
| 8    | **downstream read probe**                  | 证明 clean 可被 Layer 消费          | ⚠️ 部分路径证据回填不全                   | **F-03**                        |
| —    | **AcceptanceReport 信封**                  | 统一字段 + `gate_eligible` 语义     | ✅ 四命令形状统一                         | F-04                            |
| —    | **observability_evidence**                 | PASS 时非空（IDs、rows、hash）      | ❌ 可为空                                 | **F-03**                        |
| —    | **live vs replay 诚实**                    | 不得混用冒充 live PASS              | ✅ 产品路径诚实                           | F-05；CI replay **按设计** F-11 |

---

## 3. 正式入口 · 命令 / Profile 完成度

### 3.1 四条主命令（`qmd-data data …`）

| 命令                | P1 要求程度                                       | 当前状态                                                    | Finding / 切片                 |
| ------------------- | ------------------------------------------------- | ----------------------------------------------------------- | ------------------------------ |
| **`sync`**          | 生产等价验收根 + live 诚实 + 完整证据链           | ⚠️ baostock 本机 PASS；证据链可空                           | F-03 · F-10                    |
| **`backfill`**      | 交易日 cap（5/20）+ no-dry-run 同语义 + 可 resume | ⚠️ 金路径有；空分片可拖死整单                               | F-18 · task-01.5 S5 已对齐 cap |
| **`full-load`**     | 超出单源试点语义 + 同一验收接缝                   | ⚠️ baostock 试点 PASS；接线缝仍在                           | F-01                           |
| **`scheduler run`** | parent+child 信封；live 非 dry-run 展开器         | ⚠️ `weekly_backfill` 子任务可 PASS；`daily_close` 整单 FAIL | F-06 部分 · F-07–09            |

**CLI 验收接缝模块：**

| 模块          | P1 目标名                           | 当前名                 | 状态      | 切片          |
| ------------- | ----------------------------------- | ---------------------- | --------- | ------------- |
| CLI live 信封 | `source_route_db_cli_acceptance.py` | `phase1_acceptance.py` | ❌ 待正名 | **Slice 0-N** |

**须暴露字段（契约）：** `acceptance_report` · `gate_eligible` · `report_version` · `run_id` · `job_kind` · `observability_evidence` · `failure_class`

### 3.2 辅命令（与 scheduler 同语义）

| 命令                 | P1 要求程度                                   | 当前状态                     | 切片      |
| -------------------- | --------------------------------------------- | ---------------------------- | --------- |
| **`revision-audit`** | live 与 profile 同 `instrument_id` / lookback | ❌ `instrument_id=None` 失败 | **2a-R1** |
| **`quality-check`**  | live 与 profile 同语义（baostock 股线）       | ❌ 空壳 runner               | **2a-Q**  |

### 3.3 Scheduler Profile

| Profile               | P1 要求程度                                                   | 当前状态                     | 备注             |
| --------------------- | ------------------------------------------------------------- | ---------------------------- | ---------------- |
| **`weekly_backfill`** | live backfill + full_load child 诚实 PASS                     | ✅ 本机已证（replay 注入时） | F-06 部分已关    |
| **`daily_close`**     | **四 job 整单** parent `gate_eligible` + core child 诚实 PASS | ❌ 整单 FAIL                 | Slice 3 复验关账 |

### 3.4 `daily_close` 四 Job 明细（AD-6 · 用户决议 A）

| #   | job_type       | domain              | source   | core  | P1 成品定义                                            | YAML 现状               | 实现现状                 | 切片                  |
| --- | -------------- | ------------------- | -------- | ----- | ------------------------------------------------------ | ----------------------- | ------------------------ | --------------------- |
| 1   | incremental    | cn_equity_daily_bar | baostock | true  | 真网增量 + 完整小票                                    | ✅ profile 有           | ✅ 可 PASS               | F-10                  |
| 2   | incremental    | macro_series        | fred     | true  | 授权+启用条件下非误报 DISABLED                         | ✅ profile 有           | ❌ binding 双轨 DISABLED | Slice **1** · **1-P** |
| 3   | revision_audit | macro_series        | fred     | false | **修订 diff 六步**（见 §5）                            | ⚠️ 缺 `instrument_id`   | ❌ 空壳 runner           | **2a-R1–R4**          |
| 4   | data_quality   | cn_equity_daily_bar | baostock | false | `DataQualityValidator` + 规则集 + `validation_run_ids` | ❌ **profile 尚未写入** | ❌ 空壳 runner           | **2a-Q**              |

---

## 4. Findings 全量台账（23 项 · 防遗漏）

> **关账：** 仅允许 disposition = **已关闭** 或 **按设计**（G8）。

| ID   | 标题                       | disposition            | 计划切片绑定                         | 关账条件（摘要）           | plan 是否覆盖 |
| ---- | -------------------------- | ---------------------- | ------------------------------------ | -------------------------- | ------------- |
| F-01 | fetch_port 崩溃            | **仍开放**（复核重开） | ⚠️ **无专门切片**（plan 误标已完成） | 全正式入口不经 patch 可跑  | ❌ 漏票       |
| F-02 | monkeypatch 接线           | 已关闭                 | P1-CLI-WIRING                        | —                          | ✅            |
| F-03 | sync 证据链空              | **仍开放**（复核重开） | ⚠️ **无专门切片**（G3 写已关）       | 全路径 observability 非空  | ❌ 漏票       |
| F-04 | 四命令信封统一             | 已关闭                 | P1-ENVELOPE                          | —                          | ✅            |
| F-05 | live/replay 诚实           | 已关闭                 | P1-LIVE-HONESTY                      | —                          | ✅            |
| F-06 | scheduler 诚实聚合         | **部分仍开放**         | 2a-0 · Slice 3                       | `daily_close` 整单 PASS    | ✅            |
| F-07 | scheduler fred DISABLED    | **仍开放**             | Slice **1**                          | binding ≡ matrix 启用语义  | ✅            |
| F-08 | revision_audit 空壳        | **仍开放**             | **2a-R1–R4**                         | 修订 diff 六步成品         | ✅            |
| F-09 | data_quality 空壳          | **仍开放**             | **2a-Q**                             | validator + profile + 小票 | ✅            |
| F-10 | 本机 baostock 真网         | 已关闭                 | P1-BAOSTOCK-LIVE                     | —                          | ✅            |
| F-11 | replay 测试轨道            | 按设计                 | —                                    | CI 彩排 ≠ live 关账        | ✅            |
| F-12 | 仅 baostock？              | 按设计                 | —                                    | 22 源矩阵已有              | ✅            |
| F-13 | 全链路缝隙汇总             | **仍开放**             | 随 §4 各项关闭                       | 无独立切片                 | ⚠️ 汇总项     |
| F-14 | 双轨启用语义               | **仍开放**             | Slice **1**（同 F-07）               | One-Version enable         | ✅            |
| F-15 | macro_series 域 A          | **仍开放**（决议已定） | Slice **1-P**                        | registry 域策略落地        | ✅            |
| F-16 | 运营启用清单 SSOT          | **仍开放**             | Slice **1-E**                        | `source_enable_ledger.md`  | ✅            |
| F-17 | 大量 disabled              | 按设计                 | —                                    | 按源启用，禁止 mass-enable | ✅            |
| F-18 | 空分片拖死 backfill        | **仍开放**             | ⚠️ **无专门切片**                    | 续跑/跳过 + 行为测         | ❌ 漏票       |
| F-19 | ResourceGuard autouse 假绿 | **仍开放**             | ⚠️ **无专门切片**                    | 分层 fixture               | ❌ 漏票       |
| F-20 | scheduler 宽窗集成测缺口   | **仍开放**             | ⚠️ **无专门切片**                    | 集成行为测                 | ❌ 漏票       |
| F-21 | 弱测试无 outcome           | **仍开放**             | ⚠️ **无专门切片**                    | 替换/删除无效测            | ❌ 漏票       |
| F-22 | profile YAML 无 schema     | **仍开放**             | ⚠️ **无专门切片**                    | schema + 契约测            | ❌ 漏票       |
| F-23 | Orchestrator 单体债        | **仍开放**             | ⚠️ **无专门切片**                    | 拆分或 ADR 边界            | ❌ 漏票       |

**统计（2026-07-10）：**

| disposition | 数量                              |
| ----------- | --------------------------------- |
| 已关闭      | 4（F-02 · F-04 · F-05 · F-10）    |
| 按设计      | 3（F-11 · F-12 · F-17）           |
| 部分仍开放  | 1（F-06）                         |
| **仍开放**  | **15**（含 F-01 · F-03 复核重开） |
| **合计**    | **23**                            |

**plan 漏票（8 项）：** F-01 · F-03 · F-18 · F-19 · F-20 · F-21 · F-22 · F-23 — 修订 `task_plan.md` 时必须补切片或显式绑定。

---

## 5. revision_audit 六步 · 逐步完成度（AD-7）

设计权威：`data_sync_orchestrator.md` §13.4.4

| 步骤 | 产品行为                                                     | P1 必做 | 当前                   | 切片      |
| ---- | ------------------------------------------------------------ | ------- | ---------------------- | --------- |
| 1    | 选取 data_domain + `instrument_id` + lookback                | ✅      | ❌ profile/runner 缺参 | **2a-R1** |
| 2    | 重抓小范围历史/修订窗口                                      | ✅      | ❌ 无算法              | **2a-R2** |
| 3    | 比较 content_hash / schema_hash / revision_id                | ✅      | ❌ 无比较              | **2a-R2** |
| 4    | 变化 → 写 revision_log（**DuckDB 表 + ndjson 双写** AD-9）   | ✅      | ❌ 无表/无双写         | **2a-R2** |
| 5    | 创建 BackfillJob（`trigger_reason=revision_detected`）       | ✅      | ❌ 无 job              | **2a-R3** |
| 6    | **标记** affected feature/snapshot 需重算（非 Phase 2 执行） | ✅      | ❌ revision 路径未接线 | **2a-R4** |

**共用前置：** Slice **2a-0** — orchestrator quality child 须有真实 `AcceptanceReport`，**禁止** synthetic PASS（`route_plan_id=None`）。

---

## 6. data_quality 成品要素（AD-6 · 2a-Q）

| 要素         | P1 要求                                                   | 当前                           |
| ------------ | --------------------------------------------------------- | ------------------------------ |
| profile 条目 | `daily_close` 含 `data_quality` · cn_equity/baostock      | ❌ YAML 未写入                 |
| domain 映射  | `cn_equity_daily_bar` ↔ `market_bar_1d` 规则集            | ❌ runner 只认 `market_bar_1d` |
| 执行         | `DataQualityValidator` + `data_quality_rules.yaml`        | ❌ stub                        |
| 证据         | `validation_run_ids` 非空；child `acceptance_report` 完整 | ❌                             |
| CLI          | `quality-check` live 与 profile 同语义                    | ❌ `instrument_id=None`        |
| parent       | `core: false` — 失败不拉红 parent（须诚实非假绿）         | 未验                           |

---

## 7. 路由与启用 · 完成度（AD-10 · AD-11）

| 能力                         | P1 要求                      | 当前                     | 切片 / Finding            |
| ---------------------------- | ---------------------------- | ------------------------ | ------------------------- |
| SourceRoutePlanner 成品      | ✅ 必须先 plan               | ✅                       | F-17 按设计               |
| 禁止 mass-enable             | ✅ 不得批量改 YAML           | ✅ 契约测锁定            | F-17                      |
| binding ≡ matrix 启用语义    | ✅ 一条规则                  | ❌ fred 双轨             | Slice **1** · F-07 · F-14 |
| macro_series production-live | ✅ 决议 A                    | ❌ registry 域策略未落地 | Slice **1-P** · F-15      |
| 运营启用台账                 | ✅ Tier A 11 源 + 金路径逐行 | ❌ 无 SSOT 文档          | Slice **1-E** · F-16      |
| 缺 key / 无授权              | ✅ 诚实 BLOCKED              | ✅ 机制有                | ADR-015/016               |

---

## 8. 执行切片全表（含状态）

| 切片                  | 描述                                       | 状态                        | 绑定 Finding           | plan 备注            |
| --------------------- | ------------------------------------------ | --------------------------- | ---------------------- | -------------------- |
| **（前置）task-01.5** | 清场 · 契约 · backfill cap · 去 legacy CLI | ✅ **ALL GREEN** 2026-07-10 | 债迁入 §4 F-18–F-23 等 | 硬前置已满足         |
| **Slice 0**           | quality job 范围决策（A 成品纳入 P1）      | ✅ 已关闭                   | F-08/09 决策           | —                    |
| **Slice 0-N**         | `source_route_db_cli_acceptance` 正名      | ❌ 未做                     | G4                     | 计划首项实现任务     |
| **Slice 1-E**         | Tier A 运营启用清单 SSOT                   | ❌ 未做                     | F-16                   | 文档轨               |
| **Slice 1-P**         | macro_series production-live 域策略        | ❌ 未做（决议 A 已签字）    | F-15                   | YAML + 测            |
| **Slice 1**           | fred binding 路径启用一致                  | ❌ 未做                     | F-07 · F-14            | —                    |
| **Slice 2a-0**        | quality child 真实 AcceptanceReport        | ❌ 未做                     | F-06 · F-13            | 禁 synthetic PASS    |
| **Slice 2a-R1**       | revision 接缝 + profile 参数               | ❌ 未做                     | F-08 部分              | —                    |
| **Slice 2a-R2**       | revision diff + 表/ndjson 双写             | ❌ 未做                     | F-08 核心              | AD-9                 |
| **Slice 2a-R3**       | revision → BackfillJob                     | ❌ 未做                     | F-08 部分              | —                    |
| **Slice 2a-R4**       | 步骤 6 标记需重算                          | ❌ 未做                     | F-08 关账              | 非 Phase 2 执行      |
| **Slice 2a-Q**        | data_quality 成品 + profile                | ❌ 未做                     | F-09                   | —                    |
| **Slice 3**           | `daily_close` 整 profile 复验              | ❌ 未做                     | F-06–F-16 等           | 依赖上列全部         |
| **Slice 4**           | P1-GATE ledger 关账                        | ❌ 未做                     | **G8 全 findings**     | AC 须覆盖 F-01–F-23  |
| **（建议补）P0 轨**   | F-01/03/18–23 漏票承接                     | ❌ plan 未建                | 见 §4 漏票             | **修订 plan 时必加** |

**推荐顺序（与 plan 一致处）：**  
`0-N` → `1-E ∥ 1-P ∥ 2a-0` → `1` → `2a-R1→R2→R3→R4` + `2a-Q` → `3` → `4`  
**建议修订：** 在 `0-N` 之前或并行增加 **P0 轨**（至少 F-01 · F-03 · F-18）。

---

## 9. 关键模块 / 文件触点（实现时防漏）

| 区域           | 路径 / 符号                                                    | P1 触及原因                             |
| -------------- | -------------------------------------------------------------- | --------------------------------------- |
| CLI 主入口     | `backend/app/cli/data_commands.py`                             | 四命令 + revision-audit + quality-check |
| CLI 验收接缝   | `backend/app/cli/phase1_acceptance.py` → **正名**              | G4 · Slice 0-N                          |
| 增量路由       | `backend/app/cli/incremental_sync_router.py`                   | sync live 路径                          |
| 调度           | `backend/app/sync/scheduler.py`                                | daily_close · child 信封 · fred binding |
| 编排           | `backend/app/sync/orchestrator.py`                             | quality/backfill job                    |
| Quality runner | `backend/app/sync/runners.py` · `QualityJobRunner`             | revision_audit · data_quality           |
| 路由           | `SourceRoutePlanner` · `DataSourceService`                     | F-07 · F-14                             |
| fred 启用      | `fred_incremental_watermark.enabled_fred_source_registry`      | Slice 1 SSOT                            |
| 矩阵 live      | `matrix_live_handlers.execute_fred_matrix_live`                | 对比 binding 路径                       |
| 注册表         | `specs/datasource_registry/source_registry.yaml`               | Slice 1-P · `domain_roles.macro_series` |
| Profile        | `specs/layer1_axes/sync_scheduler_profiles.yaml`               | daily_close 四 job · F-22 schema        |
| 契约           | `specs/contracts/data_cli_contract.yaml`                       | G1–G3                                   |
| 修订存储       | 新 migration `revision_log` + `data/audit/revision_log.ndjson` | AD-9 · 2a-R2                            |
| 测试           | `tests/test_sync_scheduler_acceptance.py`                      | G5 · G6 · daily_close                   |
| 测试           | `tests/conftest.py`                                            | F-19 ResourceGuard                      |
| 测试           | `tests/test_bounded_backfill_*.py` · runners 集成              | F-18 · F-20                             |
| 文档           | `task/.../source_enable_ledger.md`（待建）                     | F-16 · Slice 1-E                        |

---

## 10. 已拍板产品决策（重写 plan 不可丢）

| ID               | 决策                                                       | 日期       | 实现状态     |
| ---------------- | ---------------------------------------------------------- | ---------- | ------------ |
| Slice 0 / AD-5   | `revision_audit` + `data_quality` **均 P1 成品**，不 defer | 2026-07-09 | ❌ 待 2a-\*  |
| AD-6             | `data_quality` 金路径 = **cn_equity / baostock**           | 2026-07-09 | ❌           |
| AD-7             | revision **必做 diff** 六步（含步骤 6 **标记**）           | 2026-07-09 | ❌           |
| AD-8             | 模块正名 `source_route_db_cli_acceptance`                  | 2026-07-09 | ❌ Slice 0-N |
| AD-9             | revision **DuckDB 表 + ndjson 双写**，禁止 defer           | 2026-07-09 | ❌ 2a-R2     |
| AD-10            | **禁止** mass-enable；按源启用                             | 2026-07-09 | F-16 待做    |
| AD-11 / OQ-P1-Q6 | `macro_series` **纳入** daily_close production-live        | 2026-07-09 | ❌ Slice 1-P |
| Quiz             | 不发 GitHub issue（计划内索引 only）                       | 2026-07-09 | —            |
| task-01.5        | Phase 1 前置 **ALL GREEN**                                 | 2026-07-10 | ✅           |

---

## 11. plan 与 findings 已知冲突（修订 plan 时先消）

| #   | 冲突                                                   | 应以谁为准            |
| --- | ------------------------------------------------------ | --------------------- |
| C1  | plan 标 F-01/F-03「已完成」；findings **复核重开**     | **findings**          |
| C2  | plan 页眉阻塞仅 F-07–F-16；findings **15 项仍开放**    | **findings + G8**     |
| C3  | plan「约 70%」基于旧 disposition                       | 重算或改表述          |
| C4  | plan 写 task-01.5「须先关账」；已 **ALL GREEN**        | 改为已满足            |
| C5  | plan 引用 `progress.md` **文件不存在**                 | 新建或删引用          |
| C6  | Slice 4 AC 只关 F-07–F-16；G8 要求 **全部 23 项**      | 扩 Slice 4 / 补 P0 轨 |
| C7  | plan 代码核验 L901「F-01–F-03 仍属实」与 findings 相反 | 删除或更正            |

---

## 12. 关账前勾选总表（复制用于收尾）

```
Phase 1 关账自检
[ ] G1–G8 全部满足
[ ] findings F-01–F-23 逐条 ∈ {已关闭, 按设计}
[ ] daily_close 四 job 已写入 profile 且 live 复验 PASS
[ ] revision 六步 + data_quality 成品 + 双写 revision_log
[ ] fred binding ≡ matrix；macro 域策略落地；启用台账存在
[ ] fetch_port 根因消除；observability 全路径非空
[ ] F-18–F-23 测试/架构债已关
[ ] uv run pytest -q exit 0
[ ] 本文件 §4 §8 行状态已同步更新
```

---

## 13. 文档索引（本票）

| 文件                                           | 角色                                               |
| ---------------------------------------------- | -------------------------------------------------- |
| **`PHASE1_COMPLETION_INVENTORY.md`（本文件）** | **防遗漏全量统计 SSOT**                            |
| `completion-check-audit-layer1-modules.md`     | **completion-check 对抗审计落盘（7 模块 CC-0–7）** |
| `PHASE1_PRD.md`                                | 产品完成口径                                       |
| `task-02-layer1-full-task_plan.md`             | 可执行切片（可能与 findings 滞后）                 |
| `task-02-layer1-full-findings.md`              | 问题 disposition 活台账                            |
| `note.md`                                      | 执行期计划外决策                                   |
| `docs/quality/待修复清单.md`                   | 开放债登记                                         |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.2.1     | 路线图承接                                         |

---

_最后同步：2026-07-10 · 若 disposition 或切片状态变化，请更新 §4 统计与 §8 切片表。_
