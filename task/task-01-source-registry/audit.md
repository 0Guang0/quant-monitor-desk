## 📋 Code Review Report

**Project Positioning:** L5 Critical（D3 + R4 + C2 · 金融量化监控）  
**Review Scope:** 抓取→入库主路径 — `backend/app/sync/*`、`datasources/service.py`、`db/write_manager.py`、`ops/*incremental*`、`ops/sandbox_clean_write/clean_write_targets.py`（对照 `layer1_axes/ingestion_commit.py`）  
**Language:** Python（multi-paradigm；已按 language-adjustments 放宽 OOP 教条，不放宽正确性/事务/审计）  
**Reviewer skill:** pragmatic-clean-code-reviewer  
**Date:** 2026-07-12

### 🔴 Critical Issues (Must Fix)

- **[runners.py:319-356 + write_manager.py:168-186 + connection.py:179-190] Sync 金路径 `own_transaction=False` 且外层未 `BEGIN`，`upsert_by_pk` 的 DELETE/INSERT 非原子**
  - Rule: PP-40 (Resources / transactional integrity) + PP-36 (Error Handling)
  - Principle: `WriteManager` 契约假定调用方持有事务；测试与 Layer1 `ingestion_commit` 都先 `BEGIN`。`SyncWritePipeline` / `IncrementalJobRunner` 却在 `ConnectionManager.writer()`（无事务）上直接写。`upsert_by_pk` 先 DELETE 再 INSERT，中间失败会留下「已删未插」的 clean 空洞，金融行情/宏观观测不可接受。
  - Suggestion: 在 `_finalize_staged`（或 `writer()`）对 clean 写入显式 `BEGIN`…`COMMIT`/`ROLLBACK`；或对本路径改用 `own_transaction=True`；并为「DELETE 成功、INSERT 失败」加回归测试。
  - Effort: Medium
    - 改 runners + 可能 connection；需补事务边界测试
    - 与 ADR-001 crash-window（COMPLETED 在 commit 后）需对齐设计
  - Benefit: High
    - 金路径默认 `write_mode=upsert_by_pk`（`clean_write_targets.py`）
    - 最坏后果是 clean 表数据丢失

---

- **[runners.py:250-276] 生产冲突校验对空 peer staging「永远 PASSED」**
  - Rule: PP-75 (Correctness) + CA-8 (SRP / false safety)
  - Principle: `conflict_staging_table` 仅 `CREATE TABLE IF NOT EXISTS` 空表后立刻 `validate_table`。peer 行只在测试 adapter（`_conflict_peer_rows`）或 e2e monkeypatch 里注入；生产 adapter/fetch 从不填充。门禁表面存在，实际不拦严重多源分歧。
  - Suggestion: 在 fetch 后由编排器拉取 validation/fallback 源写入 peer staging，或无 peer 数据时 fail-closed（不得标 PASSED）；删除「空表即通过」路径。
  - Effort: High
    - 需多源二次 fetch 或历史 peer 策略；触达 registry、runner、acceptance
  - Benefit: High
    - 冲突是 clean 写入前最后一道防脏价闸门
    - 当前等于未启用

---

- **[macro_incremental_common.py:171-225, 326-353, 446-451] 宏观「金路径」靠全局 monkeypatch + `staged_fixture_mode=True`**
  - Rule: PP-47 (Global State) + PP-57 (Concurrency) + CA-12 (Dependency Rule)
  - Principle: 运行时改写 `_PipelineMixin._validate_staging` 与 `create_test_adapter`；服务以 `staged_fixture_mode=True` 走测试适配器工厂。并发任务会互相覆盖 patch；生产编排依赖测试替身，边界与审计语义漂移。
  - Suggestion: 用显式 adapter/validator 注入替代 class setattr；live 路径 `staged_fixture_mode=False` + `create_adapter`；patch 仅保留在 pytest。
  - Effort: High
    - 多源 `*_incremental_run.py` 同源模式需一并收敛
  - Benefit: High
    - 宏观增量是 gold tier；全局 patch 在并行/重入下不可审计

### 🟡 Important Issues (Should Fix)

- **[binding_executor.py:126-134, 249-269] `execute_binding` 计算了 watermark/`since` 却未写入 `SyncJobSpec.date_start`**
  - Rule: PP-75 (Correctness)
  - Principle: dry-run 消息展示 watermark，live incremental 仍可能 `date_start=None`，窗口依赖外层 CLI/proxy；scheduler→binding 路径易全量重拉或窗口错误。
  - Suggestion: incremental 时把 `since` 写入 `spec.date_start`（及 `date_end`），与 CLI baostock/mootdx 窗口逻辑对齐。
  - Effort: Low
    - 主要改 binding_executor + 少量测试
  - Benefit: High
    - scheduler/binding 是自动化入口；窗口错则重复写或漏写

---

- **[runners.py:263-266] validation sources 缺失时硬编码 `("qmt_xtdata", "baostock")`**
  - Rule: PP-43 (YAGNI vs wrong default) + CC-175 (Magic)
  - Principle: 非 A 股/无 registry 绑定时仍假定 CN 双源，冲突语义错误且掩盖配置缺失。
  - Suggestion: 无 validation/fallback 时返回 `None` 并 fail-closed 或显式 `CONFLICT_CHECK_SKIPPED`，禁止伪造源 ID。
  - Effort: Low
    - 单点改 + 契约测试
  - Benefit: Medium
    - 错误默认会误导审计与 reconcile

---

- **[orchestrator.py:358-374] `recover_stuck_writing_job` 只查 `WRITING`+`write_id`，不核验 `write_audit_log.status=SUCCESS`**
  - Rule: PP-36 (Error Handling)
  - Principle: ADR-001 允许 COMPLETED 在 commit 后；但 FAILED 写也可能带 `write_id`。未核验审计成功即标 COMPLETED，作业状态与数据真相脱节。
  - Suggestion: 恢复前 `SELECT status FROM write_audit_log WHERE write_id=?`，仅 SUCCESS 可 COMPLETED，否则 FAILED_FINAL。
  - Effort: Low
    - 一处查询 + 扩展现有 crash-window 测试
  - Benefit: Medium
    - 恢复路径低频，但金融作业账本必须诚实

---

- **[macro_incremental_common.py:303, STAGING_TABLE] 全局共享 `stg_axis_observation_smoke`，fetch 时 `DELETE FROM` 全表**
  - Rule: PP-57 (Concurrency)
  - Principle: 多进程/交错作业会互删 staging；表名含 `smoke` 却用于 clean promote。
  - Suggestion: per-job staging 表名（含 job_id）；生产表名去掉 smoke。
  - Effort: Medium
    - DDL/迁移与多源 incremental 对齐
  - Benefit: High
    - 并发或重入时直接污染入库批次

---

- **[macro_incremental_common.py:547-555] `total_rows_written` 累加 indicator 全表 COUNT，非本 job 写入行数**
  - Rule: PP-75 (Correctness)
  - Principle: 报告夸大写入量，运维/验收误判增量成功规模。
  - Suggestion: 用 `WriteResult.rows_inserted/rows_updated` 或按 `write_id`/时间窗计数。
  - Effort: Low
    - 改计数来源即可
  - Benefit: Medium
    - 影响验收与监控，不直接改库

---

- **[runners.py:292-300] `DESCRIBE` 失败被 `except Exception` 吞掉并回退列集合**
  - Rule: PP-36 (Error Handling)
  - Principle: staging 结构异常时质量校验可能对照错误列集，放行坏批次。
  - Suggestion: DESCRIBE 失败应 fail-closed，禁止宽泛 `Exception` 吞没。
  - Effort: Low
  - Benefit: Medium
    - 异常 staging 是脏数据入口

### 🔵 Minor Issues (Nice to Have)

- **[orchestrator.py:180-227 等] `run_incremental` / `run_backfill` / `run_full_load` 参数面远超 L5（≤2）阈值**
  - Rule: CC-26 (Function Arguments)
  - Suggestion: 收敛为单一 `PipelineConfig`（已部分存在）作为唯一配置入参。

- **[write_manager.py:244-245] `fallback_reason` 复用 `stale_reason` 审计列（已有 ponytail）**
  - Rule: PP-15 (DRY/honesty of audit)
  - Suggestion: 按注释升级路径增加独立 audit 列，避免运维误读。

### 📝 Verdict

🚫 Major rework needed — 至少 3 项 Critical：upsert 无事务边界（数据丢失风险）、冲突门禁空跑、宏观金路径依赖全局 monkeypatch/`staged_fixture`。L5 金融入库完成前须先修这三项。

---

# pragmatic-clean-code-reviewer · task-01 Source Registry 架构与设计评审

**Date:** 2026-07-12  
**Reviewer skill:** pragmatic-clean-code-reviewer  
**Language:** Python（multi-paradigm；已按 language-adjustments 调整，不放宽正确性/边界/审计）  
**Focus:** 架构与设计（非行级风格）；对照执行计划、权威 design、ADR-017、ADR-018 的最终成品形态  
**Branch context:** `feat/g1-02-ask-activation-03` · 票 01–05 切片 CLOSED；G1-02 整包 / 模块 R4 仍 OPEN

## 定位与范围

| 项                       | 结论                                                                                                                                                                                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **问卷**                 | D3 外部/产品 · R4 最高标准 · C2 核心依赖（金融数据策略地基）→ **目标等级 L5**                                                                                                                                                                     |
| **本次要求**             | 分别按 **L3 / L4 / L5** 审架构与设计（不因目标是 L5 而跳过 L3/L4）                                                                                                                                                                                |
| **最终成品形态（权威）** | 稳定 Registry（YAML/DB）≠ 启用覆盖层（overlay）≠ Capability；ADR-018 两层「问开关 → 安检」；默认 fail-closed；全入口同参同结论；禁止内存撬门；ADR-017 来源/质量独立标签 + 三区数据生命周期（本票交策略契约与启用 SSOT，RoutePlan 算法归 task-02） |
| **审查对象**             | design：ADR-017/018、`data_sources.md` §5.2.1、`source_capability_registry.md`；实现：`activation_overlay` / `source_registry` / `capability_registry` / `route_planner` / `service` / 边界与接线计划                                             |
| **权威链**               | `MIGRATION_MAP` 索引 design > `g1-02-execution-brief` > `task_plan` > inventory；见 `EXECUTION-DOC-INDEX.md`                                                                                                                                      |

### 权威依据（只读遵守）

- `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`
- `docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`
- `docs/modules/design/data_sources.md`（含 §5.2.1 `source_activation_overlay`）
- `docs/modules/design/source_capability_registry.md`
- `task/task-01-source-registry/task_plan.md` · `g1-02-execution-brief.md` · `findings.md`

---

## 📋 Code Review Report — L3 🤝 Team

**Project Positioning:** L3 Team（「同事能否接手？」）  
**Review Scope:** task-01 权威设计 + `backend/app/datasources` 策略核心（registry / capability / overlay / planner / service）

### 🔴 Critical Issues (Must Fix)

- **[`route_planner.py:185` + `service.py:214-231`] 路由 READY 只验 domain 级 capability，不验 operation**
  - Rule: PP-75 (Correctness) · CA-1 (Design/Architecture same)
  - Principle: 权威把 capability 定义为 source–domain–**operation** 契约；planner 用 `is_capability_declared`，READY 路径又跳过 `assert_source_domain_operation`。未声明 operation 可 READY，策略与取数边界脱节，金融场景会调度「账本上不存在的操作」。
  - Suggestion: planner 对每个候选调用 operation 级断言；service 在 READY 路径也必须二次 gate 或删除「仅 override 再 assert」的捷径。
  - Effort: Low
    - 改 planner 一处 + service 一处，补 2–3 个边界测试
  - Benefit: High
    - 热路径：每次 plan/fetch
    - 错误 READY 会进入取数/血缘，后果是错误路由与不可信证据

---

- **[`capability_registry.py:70-82`] capability 加载只检查键存在，不校验类型/非空/允许值**
  - Rule: PP-36 (Error Handling) · PP-75
  - Principle: L3 要求配置错误在边界失败关闭。`frequency: null`、`fields: []`、`requires_auth: "x"` 可被 load，等于把坏契约放进生产 SSOT。
  - Suggestion: load 时校验 frequency 非空字符串、fields 非空、requires_auth 为 bool；非法文档拒绝加载。
  - Effort: Medium
    - 校验 + 非法样例测试 + 可能修 YAML 脏数据
  - Benefit: High
    - 启动/加载即拦；避免静默错误策略

### 🟡 Important Issues (Should Fix)

- **[`activation_overlay.py:66-110`] `write_activation_overlay` 信任边界过松**
  - Rule: PP-72 / PP-73 (Attack surface / Validate all)
  - Principle: 金融策略写入应受控。当前只校验 reason/changed_by 非空与 sandbox 字样，不验隔离根、不验 source/domain/operation 是否已登记。
  - Suggestion: 产品写入口强制鉴权+登记存在性；sandbox 路径强制 `is_audit_sandbox_data_root`（或等价）。
  - Effort: Medium
    - 写路径 + 测试夹具分流
  - Benefit: High
    - 错误/滥用写入会污染启用审计链

---

- **[`route_planner.py:81-85`] `plan(con=None)` 回落 YAML 内存 `is_enabled`，形成第二套启用 SSOT**
  - Rule: CA-12 (DIP/稳定依赖) · PP-15 (DRY 业务知识)
  - Principle: ADR-018 要求正式入口只问开关本。无 con 回落使「同参」在不同调用形状下可分裂，同事无法只靠一处策略推理行为。
  - Suggestion: 正式 API 强制 `con`；无 con 仅测试桩且不得进产品路径；完成 4a/4b 后删除回落。
  - Effort: Medium
    - 调用方补 con + 删回落 + 测
  - Benefit: High
    - 消除入口分裂根因之一

---

- **[`route_planner.py:291-312`] `reason_code` 取首个 candidate.skip，而非最终决策原因**
  - Rule: PP-75 · 可观测性（3-OBS）
  - Principle: 团队排障依赖可解释拒绝。`DISABLED_SOURCE` 却带 `user_authorization_required` 会误导 on-call。
  - Suggestion: reason 绑定最终 `route_status` 的决定性 candidate（Primary 或 selected 失败原因）。
  - Effort: Low
  - Benefit: Medium
    - 非数据损坏，但运维误判成本高

---

- **[`source_registry.py:255-264`] multi-validation 列表只保留首项**
  - Rule: CA-3 (Behavior vs Structure) · ADR-017 固定次源优先级
  - Principle: YAML 可写多 validation，运行时静默丢弃，接手者读配置会误判候选集。
  - Suggestion: load 时拒绝多值，或完整保留有序列表并由 planner 消费（G1-03 范围需钉死）。
  - Effort: Medium
  - Benefit: Medium
    - 影响降级连续性设计预期

### 🔵 Minor Issues (Nice to Have)

- **[`route_planner.py:100-118`] `_platform_allows` 混合平台矩阵与 license gate**
  - Rule: CA-8 (SRP)
  - Suggestion: 平台矩阵与 license 分步命名/分函数，便于单测与审计叙述。

- **[`source_registry.py` ~570 行] 解析、校验、同步、运行时查询同文件**
  - Rule: CA-8 / CA-15 (CCP)
  - Suggestion: 按「解析校验 / 运行时查询 / DB sync」分包，降低接手成本（非阻塞正确性）。

### 📝 Verdict

🚫 Major rework needed — 至少 2 项 Critical 正确性缺口（operation 门控 + capability fail-open），叠加启用 SSOT 双路径与写边界，尚不满足 L3「同事只信一条策略」的接管标准。

---

## 📋 Code Review Report — L4 🚀 Infra

**Project Positioning:** L4 Infra（「我改坏了别人会不会遭殃？」）  
**Review Scope:** 同上 + 跨模块启用接缝（Gate1 / ADR-018 删除顺序 / 消费者同路）

### 🔴 Critical Issues (Must Fix)

- **[架构·One-Version] 策略 SSOT 仍未成为全库唯一执行接缝**
  - Rule: CA-22 (Independence) · CA-24 · ADR-018 §1/§4 · PP-47 (avoid dual truth)
  - Principle: L4 基础设施要求可替换消费者而不改变决策语义。核心 planner 已接 `ask_activation`，但 `plan(con=None)` 回落、测试/夹具仍有 `__setattr__` 构造、ledger 仍记 F05/F06/F07；发布证据若混档位，下游 task-02/17/18 会建立在假绿上。
  - Suggestion: 严格按 ADR-018 删除顺序收口 4a/4b/4x；rg 生产路径零撬门；关账证据只用正式入口 + 隔离根正规 overlay。
  - Effort: High
    - 跨 CLI/增量/验收多文件 + 大量测试迁移
  - Benefit: High
    - 所有路由消费者共享根因；分裂会扩散到调度与回补

---

- **[`route_planner.py:185` + `service.py:214-231`] operation 级 capability 缺口（同 L3）**
  - Rule: PP-75 · `source_capability_registry.md` §3
  - Principle: 下游把 RoutePlan 当调度权威；错误 READY 会变成跨模块「合法计划」。
  - Suggestion: 同上，且 RoutePlan 候选应记录 operation 级 capability 结果。
  - Effort: Low
  - Benefit: High

---

- **[`capability_registry.py:70-82`] 契约校验不完整（同 L3，L4 升为 Critical）**
  - Rule: PP-36 · CA-4 (preserve structure)
  - Principle: 配置 SSOT 是基础设施；坏配置被接受 = 全系统策略基线腐烂。
  - Suggestion: 完整 schema/契约校验，与 `source_capability_contract.yaml` 对齐。
  - Effort: Medium
  - Benefit: High

---

- **[`activation_overlay.py:66-110`] overlay 写路径缺少隔离与登记约束（L4 为 Critical）**
  - Rule: PP-72/73 · ADR-017 §1（受控、可撤销、可审计）
  - Principle: 启用覆盖层是运营控制面；无边界写入破坏审计与回滚语义，影响所有依赖 overlay 的入口。
  - Suggestion: 管理员 API/CLI 唯一写入口 + 登记校验 + sandbox 根硬门。
  - Effort: Medium
  - Benefit: High

### 🟡 Important Issues (Should Fix)

- **[design↔impl] `data_sources.md` §5.2.1「有效启用」公式与 ADR-018 两层接缝叙述易揉层**
  - Rule: CA-1 · CA-23 (Decouple layers)
  - Principle: 设计把 base+overlay+license+platform+cap+ResourceGuard 写成一条「有效启用」，实现上 ResourceGuard 在 service fetch 之后、license 塞进 `_platform_allows`。L4 文档与实现分层不一致会导致新代码再次揉层（ADR-018 方案 A 复辟）。
  - Suggestion: design 明确「开关本输出」vs「安检合成输出」两个类型/字段集；ResourceGuard 归安检第 N 步而非开关本。
  - Effort: Medium
    - 须用户审阅 design + promote（不可静默改）
  - Benefit: High
    - 防止后续工作包再次揉层

---

- **[`route_planner.py:233-264`] domain_enabled_by_default 与 overlay 的否决/放行优先级不完整**
  - Rule: PP-75 · ADR-018 执行 brief 证据 2
  - Principle: 代码已对「READY + selected 有 revision」放行域默认关，但非 READY 时 domain_disabled 抢先改写 status，掩盖 platform/auth 真因；无 revision 的 DB 基础启用与域开关关系仍不直观。
  - Suggestion: 写成单一决策表（域默认 / overlay / base）并测四象限；拒绝原因不得被域开关吞掉。
  - Effort: Medium
  - Benefit: High
    - 宏观域（如 FRED）运营启用是热路径

---

- **[`route_planner.py:291-312`] 可观测 reason_code 与决策不一致**
  - Rule: PP-75 · task_plan 3-OBS
  - Effort: Low
  - Benefit: Medium
    - 跨模块排障

---

- **[`route_models.py` / ADR-017] 缺少独立 `source_grade`/`quality_grade` 一等公民字段**
  - Rule: CA-3 · ADR-017 §3
  - Principle: 仅有 `route_grade` + quality*flags 字符串，不足以稳定跨 Layer/前端消费「PRIMARY|DEGRADED × QUALITY*\*」；下游易重新发明标签。
  - Suggestion: 在本票契约中定义稳定枚举字段（可附加不改义），task-02 持久化同名字段。
  - Effort: High
    - 跨模块 schema/血缘
  - Benefit: High
    - 审计与前端一致性

---

- **[API 稳定性] `ask_activation` / `ActivationDecision` 无版本化错误码表与 Hyrum 清单**
  - Rule: L4 API stability · ADR-018 「只许附加」
  - Principle: 下游已依赖 reason_code 与 revision；无冻结表则静默改义会伤消费者。
  - Suggestion: 在 design 或 contract YAML 枚举开关本 reason_code；变更走审阅。
  - Effort: Medium
  - Benefit: Medium

### 🔵 Minor Issues (Nice to Have)

- **[`_platform_allows`] 平台与 license 耦合**（同 L3）

- **`assert_domain_schedulable` 不读 overlay**，与 planner 合成语义并行，易被旧调用方误用
  - Rule: PP-15
  - Suggestion: 标记 deprecated 或改为委托安检结果

### 📝 Verdict

🚫 Major rework needed — ≥3 Critical：跨入口 One-Version 未完成、operation 门控、契约 fail-open、overlay 写边界；尚不满足 L4「改一处不伤全站」的基础设施标准。

---

## 📋 Code Review Report — L5 🏛️ Critical（金融 · 目标等级）

**Project Positioning:** L5 Critical（「能否过审计？」· D3+R4+C2）  
**Review Scope:** 同上 + 审计链、fail-closed、生命周期与证据档位

### 🔴 Critical Issues (Must Fix)

- **[审计失败模式] 策略决策不可被外部审计员端到端复现为「唯一真相」**
  - Rule: PP-75 · PP-72 · L5 「Can it pass audit?」
  - Principle: 金融审计要求：同一输入在 CLI/服务/调度得到同一 source/status/reason/revision，且证据档位不可升格。当前模块设计（ADR-017/018）合格，但成品态未达成：双路径启用、reason 可撒谎、capability 可假 READY、overlay 可写任意连接、关账仍 OPEN。
  - Suggestion: 以 Gate1 同参探针 P-\* 作为发布阻断；任何 con=None / monkeypatch / danger_skip 不得进入证据包。
  - Effort: High
  - Benefit: High
    - 无 workaround：错误策略直接污染监控与回测信任根

---

- **[`route_planner.py:185` + `service.py:214-231`] 未声明 operation 可 READY（数据策略正确性）**
  - Rule: PP-75 · CC 正确性优先
  - Principle: L5 对错误调度零容忍；能力账本与路由脱节即合规缺口。
  - Suggestion: operation 级 gate 为硬门禁；补反证测试「未声明 op → 不得 READY」。
  - Effort: Low
  - Benefit: High

---

- **[`capability_registry.py`] 契约校验不足以称为机器权威**
  - Rule: PP-36 · design §3 「未声明不可调度」
  - Principle: 能加载畸形 capability 的系统无法声称 fail-closed 配置治理。
  - Suggestion: 与 contract YAML 双向强制；CI 拒绝残缺 SSOT。
  - Effort: Medium
  - Benefit: High

---

- **[`activation_overlay.py`] 启用控制面写路径未达受控变更标准**
  - Rule: PP-72/73 · ADR-017 §1（操作者/时间/原因/版本/撤销）
  - Principle: 表字段设计支持审计，但 API 不强制登记合法性、隔离与权限；审计员会问「谁能写、写到哪、能否写不存在源」。当前答案不充分。
  - Suggestion: 唯一受控写入口 + 强制字段完整 + 撤销路径 + 隔离根硬约束 + 拒绝无登记键。
  - Effort: Medium
  - Benefit: High

---

- **[`route_planner.py:291-312`] 拒绝原因可观测字段与决策不一致**
  - Rule: PP-75 · 审计可解释性
  - Principle: 错误 reason_code 会使事后复盘指向错误根因（授权 vs 域禁用 vs 能力），审计不可接受。
  - Suggestion: reason_code 必须等于最终决策分类的规范码（对齐 ERROR_CODE_GUIDE）。
  - Effort: Low
  - Benefit: High
    - 审计/事件响应热路径

---

- **[ADR-017 §3–§5 vs 本票交付] 来源等级/质量等级独立标签与三区生命周期未在策略契约层落地为稳定类型**
  - Rule: CA-3 · ADR-017
  - Principle: 设计已选用「可信 clean / 连续监控 / 审计归档」与双标签；实现侧 `route_grade` 粗粒度且 PRIMARY/DEGRADED、QUALITY\_\* 未作为一等契约。L5 不能把「标签语义」留给各 Layer 自由发挥。
  - Suggestion: 本票交付跨模块标签契约（字段名、枚举、禁止伪装规则）；写入/读取边界由下游实现但契约由本票冻结。
  - Effort: High
  - Benefit: High
    - 防止异常数据伪装主值进入回测

---

- **[`plan(con=None)` / 测试 `__setattr__`] 仍存在非 overlay 启用构造面**
  - Rule: ADR-018 §2 · PP-47
  - Principle: L5 证据链禁止「测试专用真理」。残留构造面会使「产品默认关闭」无法被独立复现。
  - Suggestion: 生产符号删除回落；测试一律隔离根 overlay；静态/测试门禁扫描撬门模式。
  - Effort: High
  - Benefit: High

### 🟡 Important Issues (Should Fix)

- **[设计完备性] domain 默认关 × 精确 overlay 的优先级仅在实现注释中，未在 design 钉死四象限**
  - Rule: CA-1 · PP-75
  - Principle: L5 业务规则必须在权威 design 可引用，不能靠代码注释。
  - Suggestion: 用户审阅后写入 `data_sources.md` §5.2.1 + 测试矩阵 promote。
  - Effort: Medium
  - Benefit: High

---

- **[设计完备性] 开关本 `reason_code` 枚举在 research 标 UNVERIFIED，实现用 `DISABLED_SOURCE`/空串**
  - Rule: L5 API + audit trail
  - Suggestion: design 冻结枚举与「允许时 reason 是否为空」的语义。
  - Effort: Medium
  - Benefit: Medium

---

- **[`_normalize_validation_source`] 多 validation 静默截断**
  - Rule: ADR-017 固定次源序
  - Effort: Medium
  - Benefit: Medium
    - 降级连续性

---

- **[依赖方向] `SourceRoutePlanner` 直接依赖具体 `SourceRegistry`/`SourceCapabilityRegistry`/文件系统 matrix，无端口抽象**
  - Rule: CA-12 (DIP)
  - Principle: L5 可测性/替换性要求策略核心可对伪造端口做确定性审计用例；当前可测但绑定具体类。
  - Suggestion: 最小 Protocol（get/is_declared/ask）即可，避免大框架。
  - Effort: Medium
  - Benefit: Medium

---

- **[组件边界] `datasources` 包同时含 registry 策略、RoutePlan、adapters、live gate、incremental sandbox**
  - Rule: CA-16 (CRP) · CA-8
  - Principle: 策略 SSOT 与 vendor adapter 同包，增加误 import 与发布表面积（matrix 已禁部分方向，但包内耦合仍高）。
  - Suggestion: 中期拆 `policy/`（registry+overlay+capability+planner models）与 `adapters/`；非本票阻塞但 L5 演进应规划。
  - Effort: High
  - Benefit: Medium

### 🔵 Minor Issues (Nice to Have)

- **`plan` 函数体偏长、状态机分支多**（L5 长度阈值敏感）
  - Rule: CC-20
  - Suggestion: 抽出「候选评估 / 状态收敛 / 事件发射」纯函数，便于证明决策表完备。

- **结构化日志仅 stderr JSON，无关联到持久 audit 表**
  - Rule: L5 documentation/audit trail
  - Suggestion: 与 job_event_log / 策略审计索引对齐（可阶段外置但须有台账）。

### 📝 Verdict

🚫 Major rework needed — 权威 **设计方向（ADR-017/018 两层接缝、fail-closed、禁止内存撬门）达到金融级决策质量**，但**当前实现距离 L5 可审计成品仍有结构性缺口**：错误 READY、契约 fail-open、控制面写边界、可观测原因失真、标签/生命周期契约未冻结、One-Version 未关账。按 skill 判定：**不得**以 L5 宣称 R4/可发布。

---

## 等级对照（同一问题如何升级）

| 主题                   | L3           | L4                      | L5                       |
| ---------------------- | ------------ | ----------------------- | ------------------------ |
| operation 不验就 READY | Critical     | Critical                | Critical                 |
| capability 弱校验      | Critical     | Critical                | Critical                 |
| overlay 写边界         | Important    | Critical                | Critical                 |
| con=None / 双 SSOT     | Important    | Critical（One-Version） | Critical（审计不可复现） |
| reason_code 撒谎       | Important    | Important               | Critical                 |
| 双标签/三区契约        | Minor/范围外 | Important               | Critical                 |
| 包内策略+adapter 混放  | Minor        | Minor–Important         | Important（演进）        |
| **Verdict**            | Major rework | Major rework            | Major rework             |

---

## 相对「最终成品形态」的差距（一句话）

**设计已给出金融级目标态**（稳定目录 + 可审计开关本 + 安检合成 + 禁止撬门 + 风险标签不伪装）；**实现处于 G1-02 中后段**：问开关与 planner 接线已现，但 **策略正确性门控、契约硬度、控制面审计、全入口 One-Version 与 ADR-017 标签契约** 仍未达到 L3 可交接，更未达到 L5 可过审。

### 建议修复序（与 effort/benefit 一致）

1. operation 级 capability + service 必 gate
2. capability 类型校验
3. reason_code = 最终决策
4. overlay 写信任边界
5. 删 `con=None` 回落并收口 4a/4b
6. 冻结标签/reason 枚举 design（须用户审阅）
7. 再谈 R4/L5 关账

### 台账交叉引用（已有 findings，本报告不另改 ledger）

| 本报告主题            | findings 近似 ID                 |
| --------------------- | -------------------------------- |
| operation 不验 READY  | T01-F08                          |
| domain×overlay 优先级 | T01-F09                          |
| overlay 写边界        | T01-F10                          |
| capability 弱校验     | T01-F11                          |
| reason_code 失真      | T01-F12                          |
| con=None 回落         | T01-F07                          |
| 测试内存构造 / 4a·4b  | T01-F05 / T01-F06 / T01-F03 余债 |
