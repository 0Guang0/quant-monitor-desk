# Implementation Tasks README

本目录是给 Claude Code / Codex 等 AI Coding Agent 逐轮执行的正式实施任务包。它不是临时进度记录，也不是草稿目录。

> **Trellis 复杂任务 Plan 硬门禁：** 在编写或冻结 `.trellis/tasks/<slug>/MASTER.plan.md` 之前，**必须先完整阅读**本目录下与本任务相关的：全局规则（下表）→ 所属 `ROUND_*/README.md` → `DECISIONS.md` → `NNN_*.md` 任务卡 → 任务卡 §3 列出的 specs/architecture 文档。`MASTER` 只负责实现方案与验收细节，**不得扩大或缩小**本目录已定义的范围；冲突时先更新 `DECISIONS.md` 并获用户确认。

项目导航地图见仓库根目录 [`MIGRATION_MAP.md`](../../MIGRATION_MAP.md)；文档索引见 [`docs/INDEX.md`](../INDEX.md)。

## 执行顺序

必须按以下顺序执行：

1. `ROUND_0_PROJECT_SCAFFOLD/`：项目骨架与执行规则。
2. `ROUND_1_DATA_FOUNDATION/`：本地数据底座、资源保护、写入边界。
3. `ROUND_2_DATA_INGESTION_VALIDATION/`：数据源接入、同步、质量检查与冲突治理。
4. `ROUND_3_MODELING_LAYERS/`：Layer 1-5 建模层、快照层、证据链。
5. `ROUND_4_API_FRONTEND_AGENT_BACKTEST/`：API、前端、Agent、通知、回测与动作语义保护。
6. `ROUND_5_INTEGRATION_RELEASE/`：集成测试、资源边界测试、文档一致性、最终包清理。

每个任务文件都必须独立可读。AI 执行时如果上下文丢失，重新打开当前任务文件和本目录下的全局规则文件即可恢复。

## 全局规则文件

执行任何任务前必须先读取：

- `GLOBAL_EXECUTION_RULES.md`
- `GLOBAL_TESTING_POLICY.md`
- `GLOBAL_RESOURCE_LIMITS.md`
- `GLOBAL_TASK_TEMPLATE.md`

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

执行前先读 `ROUND_1_DATA_FOUNDATION/DECISIONS.md`（已确认的路径/范围/依赖决策）与本轮 `README.md`（依赖图、Checkpoint）。每个任务的可执行细节（TDD 步骤、API 签名、命令与预期输出）见 `ROUND_1_DATA_FOUNDATION/plans/`。

- `ROUND_1_DATA_FOUNDATION/DECISIONS.md` — 本轮已确认决策（先读）
- `ROUND_1_DATA_FOUNDATION/005_create_schema_sql.md` — 创建 DuckDB schema 初始化（→ `plans/005_schema.plan.md`）
- `ROUND_1_DATA_FOUNDATION/006_implement_resource_guard.md` — 实现 ResourceGuard（→ `plans/006_resource_guard.plan.md`）
- `ROUND_1_DATA_FOUNDATION/007_implement_duckdb_connection_manager.md` — 实现 DuckDB 连接管理（→ `plans/007_connection.plan.md`）
- `ROUND_1_DATA_FOUNDATION/008_implement_write_manager.md` — 实现 WriteManager（→ `plans/008_write_manager.plan.md`）
- `ROUND_1_DATA_FOUNDATION/009_implement_file_registry_and_raw_store.md` — 实现 file_registry 与 Raw Store（→ `plans/009_raw_store.plan.md`）
- `ROUND_1_DATA_FOUNDATION/010_foundation_smoke_tests.md` — 数据底座 smoke test（→ `plans/010_smoke.plan.md`）

## ROUND_2_DATA_INGESTION_VALIDATION

执行前先读 `ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` 与 `README.md`（四批次、Checkpoint）。**Execute 按批次进行**；Batch A Plan 见 `.trellis/tasks/06-17-round2-batch-a-sources/`。

| Batch | 任务 | 深度计划 |
|-------|------|----------|
| A | 011+012 | MASTER §8（`.trellis/tasks/archive/2026-06/06-17-round2-batch-a-sources/`） |
| B | 013 | MASTER §8（`plans/013_batch_b.plan.md` 索引） |
| C | 015+016 | MASTER §8（`plans/015_016_batch_c.plan.md` 索引） |
| D | 014 | （待 Plan） |

- `ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` — 本轮已确认决策（先读）
- `ROUND_2_DATA_INGESTION_VALIDATION/011_implement_source_registry.md` — 实现 source_registry（Batch A）
- `ROUND_2_DATA_INGESTION_VALIDATION/012_implement_data_adapter_contract.md` — 实现 Data Adapter Contract（Batch A）
- `ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md` — 实现核心数据源 adapter skeleton（Batch B）
- `ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md` — 实现 DataSyncOrchestrator（Batch D）
- `ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md` — 实现 DataQualityValidator（Batch C）
- `ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md` — 实现 SourceConflictValidator（Batch C）

## ROUND_3_MODELING_LAYERS

- `ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md` — 实现 Layer 1 五轴 loader
- `ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` — 实现 Layer 1 解释快照
- `ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md` — 实现 Layer 2 跨资产传感器
- `ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md` — 实现 Layer 3 产业链配置 loader
- `ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md` — 实现 Layer 3 快照构建
- `ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md` — 实现 Layer 4 市场结构
- `ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md` — 实现 Layer 5 证据链

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
