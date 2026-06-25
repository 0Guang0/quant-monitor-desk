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
8. `ROUND_4_API_FRONTEND_AGENT_BACKTEST/`：API、前端、Agent、通知、回测与动作语义保护。
9. `ROUND_5_INTEGRATION_RELEASE/`：集成测试、资源边界测试、文档一致性、最终包清理。

每个原始任务文件都必须独立可读，供 Plan 阶段在上下文丢失时重新定位范围、边界和输入来源。

## Plan 阶段必读

Plan agent 在将原始执行任务转写为 `.trellis/tasks/**/MASTER.plan.md`、`AUDIT.plan.md`、`REPAIR.plan.md` 与 jsonl manifest 前，必须先读取：

- `TASK_INPUT_CONTEXT_INDEX.md` — Plan 阶段上下文桥；用于建立原始任务、设计/契约/规则/定义与 Trellis 详细计划之间的追溯关系
- `UNRESOLVED_ITEM_TASK_COVERAGE.md` — 未闭合项到原始执行任务卡的覆盖索引；Plan 必须按当前 registry 核对目标批次相关 ID，避免只看任务目标而漏掉待修复项
- `GLOBAL_EXECUTION_RULES.md`
- `GLOBAL_TESTING_POLICY.md`
- `GLOBAL_RESOURCE_LIMITS.md`
- `GLOBAL_TASK_TEMPLATE.md`
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

## ROUND_4_API_FRONTEND_AGENT_BACKTEST

- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md` — 实现 FastAPI 路由
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/025_implement_agent_tool_layer.md` — 实现 Agent Tool Layer
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md` — 实现前端 shell
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md` — 实现前端 Layer 页面数据绑定
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md` — 实现报告与通知
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md` — 实现回测与复盘
- `ROUND_4_API_FRONTEND_AGENT_BACKTEST/030_implement_no_action_semantics_guard.md` — 实现 No Action Semantics Guard

## ROUND_5_INTEGRATION_RELEASE

- `ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md` — 实现集成 smoke tests
- `ROUND_5_INTEGRATION_RELEASE/032_implement_resource_limit_tests.md` — 实现资源限制测试
- `ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md` — 实现安全与边界测试
- `ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md` — 实现文档一致性检查
- `ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md` — 实现最终包清理
- `ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md` — 创建最终发布清单
