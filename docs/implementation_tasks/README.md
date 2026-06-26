# Implementation Tasks README

本目录是给 Claude Code / Codex 等 AI Coding Agent 逐轮执行的正式实施任务包。它不是临时进度记录，也不是草稿目录。

## 执行顺序

必须按以下顺序执行：

1. `ROUND_0_PROJECT_SCAFFOLD/`：项目骨架与执行规则。
2. `ROUND_1_DATA_FOUNDATION/`：本地数据底座、资源保护、写入边界。
3. `ROUND_2_DATA_INGESTION_VALIDATION/`：数据源接入、同步、质量检查与冲突治理。
4. `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/`：进入 Round3 前的数据源能力、路由、运维、模块边界与隐私契约对齐（只改设计文档与执行计划，不改代码）。
5. `ROUND_3_MODELING_LAYERS/`：Layer 1-5 建模层、快照层、证据链。
6. `ROUND_3_DATA_PRODUCTION_READINESS/`：Round 3D/3E 后续生产就绪任务卡（模型输入白名单、受控真实源试点、data health v2）；**未来工作规划入口**见根目录 `PROJECT_IMPLEMENTATION_ROADMAP.md`。
7. `ROUND_3_VERIFIED_AUDIT_CLEANUP/`：Round 3V verified audit cleanup（`VR-*` 底座加固与 Layer5/模型 schema 核对）；**Batch 3V 执行入口**见 `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`。
8. `ROUND_3_BATCH6_DATA_GOVERNANCE/`：Round 3F Batch6 data governance（已完成；保留作历史 evidence 与 3F-R 输入）。
9. `ROUND_3_REFERENCE_ADOPTION_REFACTOR/`：Round 3F-R reference adoption refactor；**当前下一执行入口**见 `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`。
10. `ROUND_3_SANDBOX_CLEAN_WRITE/`：Round 3G clean-write rehearsal；被 Round 3F-R 阻塞，直到 reference adoption refactor 完成或 ADR defer。
11. `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/`：Round 3H 全部目标 source 真实接入与生产入口闭环；Round4 前强制门禁，不能只完成一组 adapter。
12. `ROUND_4_API_FRONTEND_AGENT_BACKTEST/`：API、前端、Agent、通知、回测与动作语义保护；必须等 Round 3H PASS 或 ADR narrowing 后启动。
13. `ROUND_5_INTEGRATION_RELEASE/`：集成测试、资源边界测试、文档一致性、最终包清理。

每个原始任务文件都必须独立可读，供 Plan 阶段在上下文丢失时重新定位范围、边界和输入来源。

## 完成度与反过度工程规则

- 根目录 `MODULE_COMPLETION_RATING.md` 是当前实现完成度快照，只能用于规划、任务卡与审计；设计文档、契约、架构设计、规则定义仍描述完整成品形态，不在其中标注当前完成度。
- 参考项目采纳全局护栏 SSOT：`specs/contracts/reference_adoption_guardrails.yaml`（`license_gate` / `completion_rules` / 禁止 runtime import `参考项目/**`）；执行细节必须在具体任务卡 `reference_project:` 块，禁止中央 executable inventory。
- `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 只是覆盖地图，用来检查哪些模块还没到完整生产级；它不是工单。真正执行时，仍以对应 batch 的具体任务卡为准。通俗说：地图告诉你哪里还没修，任务卡告诉你怎么修。
- 每个模块或重大功能最多用三个实施批次达到完整生产可用稳定形态：第一批至少交付真实最小垂直闭环，第二批完成声明范围的生产可用主体，第三批只允许做硬化、回归、发布 gate。
- 已有部分实现的模块，其下一个实施批次必须直接补齐主承诺范围，不能继续拆成“加一个指标/加一个字段/加一个 guard/加一个 registry note”的微切片。
- 任务卡必须写明本批次要推动的完成度变化；若不能推动，必须说明为什么这是硬化/回归批而非功能批。

## Plan 阶段必读

Plan agent 在将原始执行任务转写为 `.trellis/tasks/**/MASTER.plan.md`、`AUDIT.plan.md`、`REPAIR.plan.md` 与 jsonl manifest 前，必须先读取：

- `TASK_INPUT_CONTEXT_INDEX.md` — Plan 阶段上下文桥；用于建立原始任务、设计/契约/规则/定义与 Trellis 详细计划之间的追溯关系
- `UNRESOLVED_ITEM_TASK_COVERAGE.md` — 未闭合项到原始执行任务卡的覆盖索引；Plan 必须按当前 registry 核对目标批次相关 ID，避免只看任务目标而漏掉待修复项
- `GLOBAL_EXECUTION_RULES.md`
- `GLOBAL_TESTING_POLICY.md`
- `GLOBAL_RESOURCE_LIMITS.md`
- `GLOBAL_TASK_TEMPLATE.md`
- `MODULE_COMPLETION_RATING.md` — 当前实现完成度快照，仅用于规划/任务卡；设计、契约、架构文档仍描述完整成品形态
- `docs/AUDIT_DEFERRED_REGISTRY.md` — 问题须 **RESOLVED** 或 **DEFERRED（含解决阶段）**
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

## 最终包规则

最终 zip 中保留本目录下的正式任务文件；不得保留执行过程中生成的 `task_plan.md`、`findings.md`、`progress.md`、round progress report、scratch、tmp、一次性 self-check 等临时文件。

# Task Inventory

## ROUND_0_PROJECT_SCAFFOLD

- `ROUND_0_PROJECT_SCAFFOLD/000_global_execution_rules.md` — 建立全局执行规则
- `ROUND_0_PROJECT_SCAFFOLD/001_create_project_scaffold.md` — 创建项目骨架
- `ROUND_0_PROJECT_SCAFFOLD/002_create_config_and_env_templates.md` — 创建配置与环境模板
- `ROUND_0_PROJECT_SCAFFOLD/003_create_testing_baseline.md` — 创建测试基线
- `ROUND_0_PROJECT_SCAFFOLD/004_create_documentation_index.md` — 创建文档索引

## ROUND_1_DATA_FOUNDATION

- `ROUND_1_DATA_FOUNDATION/005_create_schema_sql.md` — 创建 DuckDB schema 初始化
- `ROUND_1_DATA_FOUNDATION/006_implement_resource_guard.md` — 实现 ResourceGuard
- `ROUND_1_DATA_FOUNDATION/007_implement_duckdb_connection_manager.md` — 实现 DuckDB 连接管理
- `ROUND_1_DATA_FOUNDATION/008_implement_write_manager.md` — 实现 WriteManager
- `ROUND_1_DATA_FOUNDATION/009_implement_file_registry_and_raw_store.md` — 实现 file_registry 与 Raw Store
- `ROUND_1_DATA_FOUNDATION/010_foundation_smoke_tests.md` — 数据底座 smoke test

## ROUND_2_DATA_INGESTION_VALIDATION

- `ROUND_2_DATA_INGESTION_VALIDATION/011_implement_source_registry.md` — 实现 source_registry
- `ROUND_2_DATA_INGESTION_VALIDATION/012_implement_data_adapter_contract.md` — 实现 Data Adapter Contract
- `ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md` — 实现核心数据源 adapter skeleton
- `ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md` — 实现 DataSyncOrchestrator
- `ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md` — 实现 DataQualityValidator
- `ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md` — 实现 SourceConflictValidator

## ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT

> **Scope:** Phase A only changes design docs, machine contracts, and execution plans. Code changes require a separate user instruction.

- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md` — 定义 SourceCapabilityRegistry
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md` — 定义 SourceRoutePlan 与 DataSourceService
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016C_define_module_boundary_contract.md` — 定义模块边界契约
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` — 定义数据同步速查与错误手册
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016E_define_platform_source_matrix_and_qmt_xqshare.md` — 定义平台数据源矩阵与 qmt_xqshare 可选源
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md` — 定义生产等价规模基准计划

## ROUND_3_MODELING_LAYERS

> **Gate:** complete Trellis `round2-repair-alignment` (Round 2.5) and Trellis **`06-19-round2-6-routing-service-gate`** (Round 2.6 Phase C/D) before **017**. Contract gate: `.trellis/tasks/archive/2026-06/06-19-round2-6-contract-gate/`. Routing service gate evidence: `.trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate/`. See `docs/quality/ROUND2_REPAIR_ALIGNMENT_TRACKER.md` and `docs/AUDIT_DEFERRED_REGISTRY.md`.
>
> **Round 3 early ops（用户自持设计，不新增 task 文件）：** 本地 DuckDB 只读检查 CLI。完整设计文档已冻结为 `docs/ops/db_inspect_cli.md`，契约为 `specs/contracts/ops_db_inspect_contract.yaml`；执行者只能按冻结设计实现 CLI + 测试，不复用 `.tmp` 脚本。交接索引：`ROUND3_EARLY_CLOSE_PLAN.md` · `docs/ROUND3_HANDOFF.md` · `ROUND3_BATCH_IMPLEMENTATION_MAP.md`。

- `ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md` — 实现 Layer 1 五轴 loader
- `ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` — 实现 Layer 1 解释快照
- `ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md` — Batch 2.5：Layer 1 observation 真实/授权接入桥；五阶段 Gate，逐阶段审计
- `ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md` — 实现 Layer 2 跨资产传感器
- `ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` — 实现 Layer 3 产业链配置 loader
- `ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md` — 实现 Layer 3 快照构建
- `ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` — 实现 Layer 4 市场结构
- `ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md` — 实现 Layer 5 证据链

## ROUND_3_DATA_PRODUCTION_READINESS

> **Forward planning:** `PROJECT_IMPLEMENTATION_ROADMAP.md`（根目录）为 Round 3D/3E/3F/3G 及后续 Round 的前向规划 SSOT；`ROUND3_BATCH_IMPLEMENTATION_MAP.md` 保留历史批次与证据索引。  
> **First batch entrypoint:** `ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/README.md`

- `ROUND_3_DATA_PRODUCTION_READINESS/README.md` — 包范围、执行顺序、全局边界
- `ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md` — 五层模型首批真实输入白名单
- `ROUND_3_DATA_PRODUCTION_READINESS/R3E_fred_authorized_sandbox_pilot.md` — FRED 授权 sandbox 试点
- `ROUND_3_DATA_PRODUCTION_READINESS/R3E_tdx_manual_probe_addendum.md` — TDX 手动探测 addendum（018C 延伸）
- `ROUND_3_DATA_PRODUCTION_READINESS/R3E_real_data_staged_pilot_v3.md` — 模型驱动的 staged real-data pilot v3
- `ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md` — 只读 data health v2（源就绪证据）
- `ROUND_3_DATA_PRODUCTION_READINESS/FIRST_BATCH_SELF_CHECK.md` — 首批任务卡静态自检
- `ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/README.md` — Batch 01 执行入口
- `ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_TASK_CARD_MANIFEST.md` — Batch 01 任务卡清单
- `ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_ADVERSARIAL_AUDIT.md` — Batch 01 对抗审计清单
- `ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md` — Batch 01 硬化规则

## ROUND_3_VERIFIED_AUDIT_CLEANUP

> **Forward planning:** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3V。  
> **Batch entrypoint:** `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`  
> **Coordinator playbook:** `BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`

- `ROUND_3_VERIFIED_AUDIT_CLEANUP/README.md` — Round 3V 范围、路由、禁止项
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md` — Batch 3V 执行入口
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md` — 主会话六路协调手册
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_TASK_CARD_MANIFEST.md` — 任务卡清单与分支归属
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_HARDENING_RULES.md` — Batch 3V 硬化规则
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_SELF_CHECK.md` — Batch 3V 静态自检
- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_ADVERSARIAL_AUDIT.md` — Batch 3V 对抗审计
- `docs/quality/coordination/BATCH_3V_COORDINATOR_PLAYBOOK_POINTER.md` — 协调手册索引
- `docs/quality/coordination/BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` — 零遗留闭合策略
- `docs/quality/coordination/BATCH_3V_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` — Playbook 对抗审计报告
- `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` — VR 路由索引

- `ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_01`..`B02_05`、`B03_01` — 六张任务卡

## ROUND_3_BATCH6_DATA_GOVERNANCE

> **Status:** Batch 3F complete on `integration/round3-batch3f` @ `d0393153`; retained as history/evidence and as direct input to 3F-R.  
> **Canonical package:** `ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`

- `ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md` — Batch 3F canonical entrypoint and constraints
- `ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_TASK_CARD_MANIFEST.md` — Batch 3F eight-track task manifest
- `ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_COORDINATOR_STATUS.md` — integration status and full-pytest evidence summary

## ROUND_3_REFERENCE_ADOPTION_REFACTOR

> **Forward planning:** root `PROJECT_IMPLEMENTATION_ROADMAP.md` §1.4 and Round 3F-R.  
> **Current executable entrypoint:** `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`  
> **Batch-folder maintenance:** `BATCH_FOLDER_REHOME_PLAN.md`

- `BATCH_FOLDER_REHOME_PLAN.md` — future unfinished task-card batch-folder rehome plan
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/README.md` — Round 3F-R purpose and reference adoption posture
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md` — Batch 3F-R canonical entrypoint
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_TASK_CARD_MANIFEST.md` — task manifest
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_COORDINATOR_PLAYBOOK.md` — coordinator playbook
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_HARDENING_RULES.md` — hardening rules
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md` — task-local reference rules and license gate
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_01_REFERENCE_INVENTORY_AND_LICENSE_MATRIX.md` — redirected historical card; do not implement directly
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md` — EasyXT data health refactor
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_03_TDX_PROVIDER_REFACTOR.md` — TDX provider refactor
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md` — Round4 backtest adoption plan
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_05_PROVIDER_CATALOG_OPENBB_REFERENCE.md` — OpenBB-inspired provider catalog plan
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md` — `qmd data health` runtime wiring
- `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` — cleanup and batch-folder rehome plan

## ROUND_3_SANDBOX_CLEAN_WRITE

> **Future canonical package:** `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`  
> **Blocked by:** Round 3F-R unless all open items have ADR deferral.  
> **Structure:** one Task ID = one executable task card; reference-adoption details live inside the relevant `R3G_*` card, not in a separate inventory document.

- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md` — Round 3G canonical entrypoint
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_TASK_CARD_MANIFEST.md` — Batch 3G manifest
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_HARDENING_RULES.md` — Batch 3G hardening rules
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/BATCH_3G_COORDINATOR_PLAYBOOK.md` — Batch 3G coordinator playbook
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md` — R3G-01 sandbox rehearsal with task-local EasyXT/JQ2PTrade/OpenBB adaptation details
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` — R3G-02 adversarial audit
- `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md` — R3G-03 limited approved entry

## ROUND_3_REAL_DATA_PRODUCTION_ENTRY

> **Canonical package:** `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`  
> **Gate:** Round4 is blocked until R3H-05 returns PASS or WARN with explicit ADR narrowing.  
> **Scope:** all target sources in source registry/capability must be implemented or ADR-disabled; completing only one sample adapter is not enough.

- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/README.md` — Round 3H purpose and Round4 blocking rule
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md` — Batch 3H canonical entrypoint
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_TASK_CARD_MANIFEST.md` — all-source manifest
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_HARDENING_RULES.md` — all-source hardening rules
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_COORDINATOR_PLAYBOOK.md` — coordinator playbook
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` — official macro/disclosure adapters
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_02_MARKET_DATA_ADAPTERS.md` — market/crypto adapters
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md` — CN market adapters
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md` — probability/web evidence adapters
- `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` — final Layer/source production-entry audit

## ROUND_4_API_FRONTEND_AGENT_BACKTEST

> **Canonical package:** `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/README.md`  
> **Admission gate:** blocked until `ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` returns PASS or WARN with ADR narrowing.  
> **Loose `024`–`030` cards:** historical inputs with pointer notices.  
> **Reference rule:** roadmap §1.4 applies before implementing backtest, Agent artifact, UI artifact, or provider-facing logic from scratch.

- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/README.md` — Batch 04 canonical entrypoint
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_TASK_CARD_MANIFEST.md` — Batch 04 manifest and loose-card mapping
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_HARDENING_RULES.md` — Batch 04 hardening rules
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_COORDINATOR_PLAYBOOK.md` — Batch 04 coordinator playbook
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_01_api_runtime_security.md` — API runtime security
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_02_agent_policy_runtime.md` — Agent policy runtime
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_03_frontend_error_boundary_and_routes.md` — frontend route/error boundary runtime
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_04_notification_report_runtime.md` — notification/report runtime
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md` — backtest/review runtime
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md` — historical input for B04_01
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/025_implement_agent_tool_layer.md` — historical input for B04_02
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md` — historical input for B04_03
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md` — historical input for B04_03
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md` — historical input for B04_04
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md` — historical input for B04_05; must be read with roadmap §1.4 and R3FR-04
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/030_implement_no_action_semantics_guard.md` — historical input for B04_02/B04_05

## ROUND_5_INTEGRATION_RELEASE

> **Canonical package:** `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/README.md`  
> **Loose `031`–`036` cards:** historical inputs with pointer notices.

- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/README.md` — Batch 05 canonical entrypoint
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/BATCH_05_TASK_CARD_MANIFEST.md` — Batch 05 manifest and loose-card mapping
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/BATCH_05_HARDENING_RULES.md` — Batch 05 hardening rules
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/BATCH_05_COORDINATOR_PLAYBOOK.md` — Batch 05 coordinator playbook
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_01_security_ci_release_gate.md` — security CI release gate
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_02_integration_and_resource_smoke.md` — integration/resource smoke gate
- `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_03_release_manifest_and_package_cleanup.md` — release manifest/package cleanup
- `ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md` — historical input for B05_02
- `ROUND_5_INTEGRATION_RELEASE/032_implement_resource_limit_tests.md` — historical input for B05_02
- `ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md` — historical input for B05_01
- `ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md` — historical input for B05_01/B05_03
- `ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md` — historical input for B05_03
- `ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md` — historical input for B05_03
