# task-01-source-registry · Progress

> **planning-with-files 会话日志** · 更新：2026-07-11

## Session: 2026-07-11

### Phase 0: 权威对齐、审计与方案评审门
- **Status:** in_progress（Gate 0 + ADR-018；G1-01 READY；票 **01–05** Execute CLOSED；下一刀 **06∥07**（4a/4b）；开放债 F05-A/F06/F07；R4 / G1-02 仍 OPEN）
- **Started:** —
- Actions taken:
  - 三件套占位创建（planning-with-files）
  - 2026-07-11：完成 README、MIGRATION_MAP 与 design 倒查；独立 R4 审计结论为 OPEN（见 `completion-check-audit.md`）。
  - 2026-07-11：复核 task-19 候选项；F-15/F-16 不满足 task-01 的当前 design/职责归属，未迁移。新增当前可复现的 capability、registry 可调度性与 SSOT 边界发现。
  - 2026-07-11：将占位 `task_plan.md` 改写为 R4 规格化执行计划；以 Gate 0 锁定「唯一启用机制」的设计决定，拆分为 capability 契约、默认策略、策略接缝、消费者迁移、端到端验证和关账六组可验收工作包。
  - 2026-07-11：以接口设计、证据驱动、问题分诊、上下文工程和可观测性视角补强计划：新增 T01-F03 的内部策略查询契约、跨 task 交接责任、问题状态机、权威来源→证据账本、最小遥测与切片上下文包；未改实现或权威设计。
  - 2026-07-11：按 `/completion-check` 以 Plan 模式复核，新增 `completion-check-plan.md`。结论为 `PLAN-BLOCKED`：Gate 0 的用户设计批准及 Gate 1 的 task-02/17/18 带证据接线清单尚未完成；模块实现的既有 R4 结论仍为 `OPEN`。
  - 2026-07-11：用户确认动态次源降级、质量异常连续监控、按领域回补与审计归档生命周期；创建 `docs/decisions/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`（Proposed），并将计划扩展为 4c RoutePlan/调度、4d 标签传播、4e 回补归档三个跨模块切片。未改索引 design 或运行时代码。
  - 2026-07-11：用户确认 ADR-017 正式进入 `design/`，并确认共享来源/质量契约、可归一化质量异常进入连续监控区、质量风险告警分层和 `MIGRATION_MAP.md` 索引更新；已逐份更新权威设计，创建共享契约并按官方脚本推广运行副本，尚未开始运行时代码实现。
  - 2026-07-11：用户指出“文末 ADR 补充”不足以消除歧义。复核确认旧原文仍含 `degraded clean`、只读 clean/snapshot、验证源“完全不接管”和统一一年留存等冲突/不完整口径；开始直接改写原有规则与字段清单，不删除未冲突内容。
  - 2026-07-11：已把冲突原文直接收敛为唯一规则：注册表基础状态 + `source_activation_overlay` 的有效启用；RoutePlan 固定候选链与版本字段；可信最终库/连续监控区/审计归档三目标；按领域回补窗口；普通内容一年留存、可信历史不自动清理、异常 payload 分频保留。来源/质量字段已写入原有 API、前端、Layer、通知、审计、质量和写入 schema/字段清单，而不只留 ADR 注记。
  - 2026-07-11：重新执行设计→运行副本推广；`test_design_runtime_parity.py` 2 项通过，7 份设计 YAML 解析通过，旧冲突词检索为零，范围内 `git diff --check` 无新增格式错误（仅显示 Git CRLF 转换提示）。
  - 2026-07-11：按 spec、任务拆分、接口契约与分诊方法更新执行计划：新增 `gate1-integration-spec.md`，将 Gate 1 拆成策略接线（G1-01～G1-05）与风险标签/恢复闭环（G1-06～G1-08），保留既有工作包 1～5 并将最终关账升级为商业级生产发布门；同步更新 task-02 README/计划为“可信最终库／连续监控区／审计归档区”口径。
  - 2026-07-11：完成 G1-01 首版：GitNexus query/context + 源码/契约核实主要正式入口；落盘 `g1-01-wiring-inventory.md`。发现：`validation` YAML 列表运行时只取首项；回补缓冲无 per-domain 数字表（ADR-017 规则已够用）；OVERRIDE 消费者全表登记入 G1-02。
  - 2026-07-11：刷新 GitNexus 后重跑 Plan completion-check（`completion-check-plan-g1-01.md`）：`PLAN-OPEN`。`SourceRegistry.sync_to_db` 尚有 `qmd-init-db --sync-registry` 与 `DataSyncOrchestrator.bootstrap(sync_registry=True)` 两个未登记入口；须补齐其档位、DB 根、可观察写入和反证后重审。针对性 registry/CLI/orchestrator pytest exit 0，但不作为入口全量或 R4 完成证明。
  - 2026-07-11：**补完 G1-01**：GitNexus `context(sync_to_db)` / `context(bootstrap)` + Read `scripts/init_db.py`、`orchestrator.bootstrap`、`acceptance_isolation._ensure_isolated_db_cached`；清单新增 E-REG-03/04、E-ACC-ISO-01、E-TEST-03/04；§4 补 `qmd-init-db`；闭合勾选更新。未改运行时代码、未宣称 `PLAN-READY`。
  - 2026-07-11：独立 Plan completion-check r2（`completion-check-plan-g1-01-r2.md`）：**仍为 `PLAN-OPEN`**。决定性缺口：未把「补两行」升格为完备；`qmd-ops` 未入 §4；`skip_data_root_validation` 暗门未登记；E-ACC-ISO 过陈述 API 隔离保证；health/revision-audit/reconcile/quality-check 无逐行降档。**未**为冲 `PLAN-READY` 放宽门禁。
  - 2026-07-11：**按 r2 CC-3/CC-4 改清单** `g1-01-wiring-inventory.md`：E-OPS-01～03、E-ACC-SKIP-01、`danger_skip_isolation`；重写 E-ACC-ISO-01（API 不强制 assert）；E-CLI-40～43；E-TEST-05/06。未改运行时代码、未自认 `PLAN-READY`。
  - 2026-07-11：独立 Plan completion-check r3（`completion-check-plan-g1-01-r3.md`）：**仍为 `PLAN-OPEN`**。r2 入口漏登大体闭合（CC-3 PASS）；决定性缺口 CC-4：E-ACC-SKIP-01 过陈述「CLI 不传 skip」，与 `execute_documented_matrix`（`--all-documented-sources`）冲突。**未**放宽门禁。
  - 2026-07-11：按 r3 改清单：拆 E-OPS-03a/03b；E-ACC-SKIP-01 仅覆盖无先验隔离的 skip；删除「CLI 不传 skip」过陈述。待独立 Plan r4。
  - 2026-07-11：用户确认启用接缝 #1–#4 → 写入 `decision-map-enable-seam.md`；**Accepted ADR-018** 纳入 `docs/decisions/design/` 并索引 `MIGRATION_MAP.md`；`data_sources.md` §5.2.1 交叉引用；`CONTEXT.md` 术语；台账 `T01-ENABLE-FRED-MERGE-001`。下一步：G1-01 按 r5 修清单。
  - 2026-07-11：独立对抗式 Plan completion-check r5（`completion-check-plan-g1-01-r5.md`）：**`PLAN-OPEN`**。决定性：CC-5 E-CLI-20「fred 专用」与 `_gold_path_backfill_route_preview` 全金路径 OVERRIDE 冲突；CC-3 `source_route_matrix_bridge` 可写 registry 未登记/未降档。不采信 §5/r4。
  - 2026-07-11：**按 r5+ADR-018 改清单**：E-CLI-20 全金路径 OVERRIDE；E-ACC-01 preview/live 双轨澄清；E-ACC-BRIDGE-01；E-INC-FRED 对齐 ADR-018。未改运行时代码、未自认 READY。
  - 2026-07-11：独立 Plan completion-check r6（`completion-check-plan-g1-01-r6.md`）：**`PLAN-READY`**。八行无 FAIL/UNKNOWN；消 r5 CC-3/CC-5。≠ 实现/R4 完成。可开 G1-02 RED。
  - 2026-07-11：**多 skill 对抗审计 + 计划优化**：落盘 `g1-02-execution-brief.md` + `research-g1-02-enable-seam-sources.md`；重写 `task_plan` §3/§4A/工作包 3·4a·4b·4x/§8/§9；`gate1` 两层接口与 G1-02 验证扩展；decision-map 勾选 G1-01 READY。GitNexus：`enabled_source_registry` impact=**CRITICAL**。
  - 2026-07-11：**文档缝隙关闭**：`EXECUTION-DOC-INDEX.md`；3A→3-OBS、4c=G1-03～05、brief/fred-builder/README；拆票草案待确认。
  - 2026-07-11：**本地票落地**（不发 GitHub）：`.scratch/task-01-g1-02-enable-seam/issues/01–10`；06∥07∥08 并行；frontier=01/02/03。
  - 2026-07-11：**票 03 Execute CLOSED** + ponytail 可选收紧（删 `_BASE_REVISION`/薄包装/`isinstance`）；`task_plan` 下一刀改为 1/2∥3B/3C；`findings` 记 T01-F03-3A 已修复切片、T01-F03 余待修、T01-F04 清单已补齐。
  - 2026-07-11：**票 01/02 Execute CLOSED**（追加 `completion-check-execute.md` 对象 B/C）；T01-F01/F02 已修复；诚实修正契约假 evidence（工作区）。下一刀 04∥05；R4/G1-02 仍 OPEN。
  - 2026-07-11：**testing-guidelines + phase-scripts 路径复查**：无私有断言（已改 YAML+公开 API）；缺 op 三案改为 parametrize；无阶段性代码混入正式路径。已更新 `task_plan` §9 / findings Issues。
  - 2026-07-11：票 04/05 接线后全量 pytest 失败分类写入 `findings.md`（T01-F05-A/B），删除独立稿 `findings-pytest-classify-g1-02-3b.md`；待用户确认修法范围后再动夹具。
  - 2026-07-11：**T01-F05-B 已修**：`seed_activation_base`（sync_to_db）；6 条 B 测绿。未动 `sync_to_db` 符号本身（impact HIGH）。A 类仍挂 4a/4b。
  - 2026-07-11：**台账同步**：更新 `findings` / `task_plan` §3 / `g1-02-execution-brief` §6 / `EXECUTION-DOC-INDEX`；重写 [`note.md`](note.md) 记录票 03–05 与 F05 现场裁定。
  - 2026-07-11：**ponytail/质量复核（04/05 范围）**：缩 `_emit_source_policy_event`；`bootstrap_vendor_e2e_db` 复用 `seed_activation_base`；etest 去重断言。挂票债 T01-F06/F07 + F05-A 登记 `docs/quality/待修复清单.md`。无 phase-scripts 混放问题。
  - 2026-07-11：**票 04/05 Execute CLOSED**（`completion-check-execute.md` 对象 D/E）；关账前闭环 A7；余 F05-A/F06/F07 严格后置票 06/07。下一刀 06∥07；G1-02/R4 仍 OPEN。
  - 2026-07-11：**完整重写 [`HANDOFF.md`](HANDOFF.md)**（下一刀 06∥07）；同步 scratch README Frontier；对齐 findings F03 / progress 文首。
  - 2026-07-12：**补台账缺口**：findings F05-A **完整 node-id 表**（基线 terminal 652051 + `test:quick` 现红 mootdx Layer5）；新建最小 [`PROJECT_IMPLEMENTATION_ROADMAP.md`](../../PROJECT_IMPLEMENTATION_ROADMAP.md) 完成双登记；scratch 票 06/07 勾选 F05-A；HANDOFF/INDEX/待修复清单已交叉引用。
- Files created/modified:
  - `task_plan.md` · `findings.md` · `progress.md` · `note.md`
  - `g1-02-execution-brief.md` · `EXECUTION-DOC-INDEX.md`
  - `route_planner.py` · `route_models.py` · `service.py` · `event_payload.py`
  - `tests/service_path_support.py` · `test_route_planner_activation.py` · `test_etest_overlay_governance.py`
  - `test_datasource_service.py` · `test_datasource_route_grade_payload.py` · `test_sync_orchestrator.py`
  - `capability_registry.py` · `source_capabilities.yaml` · `source_capability_contract.yaml`
  - `source_registry.py` · `source_registry.yaml` · 相关测试 / fixture
  - `completion-check-execute.md` · `activation_overlay.py` · `017_*.sql` · `tests/test_activation_overlay.py`
  - `completion-check-audit.md` · `completion-check-plan.md`
  - `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`
  - `specs/contracts/design/source_provenance_quality_contract.yaml` 与关联 design 文件
  - `gate1-integration-spec.md` · 更新后的 `task_plan.md`
  - `g1-01-wiring-inventory.md`（含 E-OPS / E-ACC-SKIP / E-CLI-40～43 / E-TEST-05/06；E-ACC-ISO 诚实表述）

### Phase 2: RED
- **Status:** done（票 01/02/03）；票 04 RED 已走过（`test_route_planner_activation`）
- Actions taken:
  - 票 03：先写 `tests/test_activation_overlay.py`（ImportError RED）再实现
  - 票 01：capability load 边界 RED（draft/gap/残缺 op/生产仍 draft）
  - 票 02：validation_only Primary 加载 RED + macro_supplementary 默认路由仍 VALIDATION_ONLY_BLOCKED
  - 票 04：`tests/test_route_planner_activation.py` RED→GREEN
- Files created/modified:
  - `tests/test_activation_overlay.py` · `tests/test_source_capabilities.py` · `tests/test_source_registry.py` · `tests/test_source_route_planner.py` · `tests/test_route_planner_activation.py`

### Phase 3: GREEN
- **Status:** done（票 01–05 AC + Execute CLOSED）；下一刀 06/07 尚未 RED
- Actions taken:
  - `activation_overlay.py` + `017_source_activation_overlay.sql`；CC 闭环修复后复验绿
  - `_validate_capability_document` + YAML/契约升级；`_validate_domain_roles` 拒 validation_only+默认启用；三域失败关闭
  - 票 04：`ask_activation` 接线 + `overlay_revision` + stderr 策略日志
  - 票 05：`enable_source_route` overlay；`seed_activation_base`（F05-B）
- Files created/modified:
  - `backend/app/datasources/activation_overlay.py` · migration 017 · schema.sql 表形对齐
  - `backend/app/datasources/capability_registry.py` · `source_registry.py` · `route_planner.py` · `route_models.py` · `service.py`
  - `specs/datasource_registry/source_capabilities.yaml` · `source_registry.yaml`
  - `specs/contracts/source_capability_contract.yaml`
  - `tests/service_path_support.py` 等夹具

### Phase 4: 关账验证
- **Status:** 票 01/02/03 票级 AC 已关；票 04/05 / G1-02 / 模块 R4 仍 OPEN
- Actions taken:
  - `completion-check-execute.md` CC-0～CC-7；歧视反证：删 overlay 行 → 重回 DISABLED_SOURCE
  - 票 01/02：相关 + 全量 `uv run pytest -q` exit 0（当时）
  - 票 04/05 后全量红 → 分诊；B 6 测复验 exit 0；**未**宣称 04/05/G1-02 CLOSED
- Files created/modified:
  - `completion-check-execute.md` · `findings.md` · `note.md` · scratch 票 01/02 done

## Test Results

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| 票 01 capability load | `uv run pytest -q tests/test_source_capabilities.py` | 拒 draft/gap/残缺；生产 active 可加载 | exit 0 | ✅ 票 01 AC（≠ R4） |
| 票 02 default domain | `uv run pytest -q tests/test_source_registry.py tests/test_source_route_planner.py` | macro_supplementary → DISABLED_SOURCE；加载拒 validation_only Primary | exit 0 | ✅ 票 02 AC（≠ G1-02） |
| 票 03 ask-activation | `uv run pytest -q tests/test_activation_overlay.py tests/test_schema_migration.py` | 三字段/隔离 overlay/禁撬门/017 迁移 | exit 0；删 overlay 行歧视反证 OK | ✅ 票 03 AC（≠ G1-02） |
| T01-F05-B 夹具 | service×4 + route_grade + plannedJob | READY/顺序断言绿 | 6 passed | ✅ 夹具债清（≠ 全量绿） |
| registry / capability / route | `python -m pytest -q tests/test_source_registry.py tests/test_source_capabilities.py tests/test_source_route_planner.py` | 当前契约测试全绿 | exit 0 | ✅（不构成 R4 关账） |
| full suite（04/05 后） | `uv run pytest -q` | — | ~20 FAIL（A 类为主） | ⏳ 挂 4a/4b；非本切片关账阻塞 |
| design/runtime parity | `python -m pytest -q tests/test_design_runtime_parity.py` | design→runtime 镜像一致 | `2 passed` | ✅ |
| direct-conflict sweep | `rg` 检查旧冲突词 + YAML 解析 + scoped `git diff --check` | 无 `degraded clean`、固定 5 日回补、验证源“完全不接管”或统一 365 天口径；契约可加载、无新增格式错误 | 旧冲突词命中 0；YAML OK；格式检查通过 | ✅ |

## Error Log

| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-07-11 | `planning-with-files` 会话恢复脚本调用 `python`，但系统 PATH 中无该命令 | 1 | 不重复调用；已直接读取任务三件套与 Git 差异，后续可使用项目 `uv run python` 或已配置 Python 绝对路径。 |
| 2026-07-11 | 一次跨文件 `apply_patch` 含空 hunk，整批未应用 | 1 | 已确认未写入；移除无内容 hunk 后按同一已确认语义重试。 |
| 2026-07-11 | `uv run python scripts/promote_design_runtime.py` 因 `uv` 不在 PATH 而未启动 | 1 | 未产生任何同步写入；将使用已配置 Python 运行同一官方脚本，并以 parity 测试验证。 |
| 2026-07-11 | 票 04/05 接线后全量 pytest ~20 FAIL | 1 | 分诊 A/B；B 修夹具；A 不删测、挂 4a/4b；见 note.md |

## 关账勾选

| 项 | 状态 |
|----|------|
| Gate 0（用户产品决策） | ✅ 已确认、ADR Accepted、索引设计已更新、design→runtime parity 通过；⏳ 待用户改后详细审阅 |
| task_plan AC | ⏳ |
| findings 清零 | ⏳（开放：T01-F03 余、T01-F05-A） |
| pytest 关账复验 | ⏳（全量仍有 A 类红） |

## 5-Question Reboot Check

| Question | Answer |
|----------|--------|
| Where am I? | 3B/3C 代码已接线；F05-B 已清；04/05 Execute CC 与 G1-02 未关 |
| Where am I going? | 下一刀 **4a∥4b**（迁 ESR / acceptance overlay）；或先做 04/05 completion-check（诚实标 A 外置） |
| What's the goal? | 源注册与 capability → R4 |
| What have I learned? | 见 `findings.md` + `note.md`（有 con 读库；先开关再安检；清理≠删测） |
| What have I done? | 见上文 Session + note.md |

---
*每完成一阶段或遇错后更新*
