# MIGRATION_MAP

> Last updated: 2026-07-02
>
> 本文件已经从“旧设计内容 → 新文件位置”的迁移表，升级为项目级地图（Project Map）。它用于让 Claude Code / Codex / 人类维护者在实施前精准定位：某个模块的设计文档、契约、定义、规则、执行任务、运行实现目录分别在哪里。
>
> **导航分工：** 本文件 = **人类 narrative** + 精选模块映射；`specs/` + `docs/modules/` = 契约与设计权威。  
> **活规划 SSOT（2026-07-02 收敛）：** 根目录**仅** `PROJECT_IMPLEMENTATION_ROADMAP.md` + `MODULE_COMPLETION_RATING.md`；旧 ROUND/Wave 任务包与 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 已迁入 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（只读）。

## 0. 强制边界：`docs/` 与 `specs/` 不是实现地址

- **必须强调并保持不变**：`docs/` 与 `specs/` 是设计文档、契约、定义、规则、计划、验收与治理资料目录，**不是运行时代码目录，也不是功能实现地址**。
- `docs/` 负责叙述型设计、架构说明、模块说明、运维规则、ADR、实施任务和质量治理。
- `specs/` 负责机器可读或半机器可读的契约、schema、registry、domain specs、规则定义。
- 真正的实现目录是 `backend/`、`frontend/`、`scripts/`、`configs/`、`tests/` 等。本文件会同时给出实现目录入口，但任何 `docs/` / `specs/` 路径只能作为实施依据、验收依据或契约输入，不能当作代码落点。
- 后续实施时，若任务要求“按某设计文档实现”，应先在本地图找到对应的 `docs/` / `specs/` 输入，再落到本文件列出的实现目录；不得把文档路径误写为实现路径。

## 1. 文件定位

- 本文件是 `docs/implementation_tasks/ROUND_0_PROJECT_SCAFFOLD/004_create_documentation_index.md` 的强制输入，也是当前仓库的**项目级导航地图**（**全部任务** Plan / Execute / Audit / Repair 共同必读）。
- 本文件不是运行时代码，不参与数据库 migration。
- 本文件用于防止执行角色在多个文档版本之间迷路、误用旧口径，或把设计目录误认为实现目录。
- `docs/INDEX.md` 是普通文档入口；`MIGRATION_MAP.md` 是跨目录、跨模块、跨契约的精准索引。
- **活工单入口：** `docs/implementation_tasks/README.md`（v2 模块票队列）；历史 `ROUND_*` 路径在 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（只读，**非**开工 SSOT）。
- `MANIFEST.json` 是 2026-06-19 修复包输出清单；其保护性边界原文已逐字移入 `README.md`。

## 2. 当前项目进度快照

| 事项                        | 当前状态                                                                                                                                                                                                                                              | 主要索引                                                                                                 |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 根目录卫生收敛 (2026-07-02) | 根目录**无** `ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md`、`research/`、`_tmp-wave4-dcp-parallel/`；历史材料已迁入 `docs/archive/` 与 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/` | `docs/archive/README.md`、`docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/README.md`    |
| 活规划 SSOT                 | **仅**根目录 `PROJECT_IMPLEMENTATION_ROADMAP.md` + `MODULE_COMPLETION_RATING.md`（模块轨道 v2；MCR Pass E @ 2026-07-02）                                                                                                                              | 路线图 §0–§3 · 附录 C；`MODULE_COMPLETION_RATING.md` §0 · §4–§5                                          |
| 历史 Wave / ROUND           | Round 0–5、Wave 3/4 DCP、Batch 3V/3FR/3H 等**已归档只读**；Wave 代码已 merge，但模块 Rating 多数未达 R4（MCR Pass E：G1/G2/G4/K1/K2 仍 R3，G5 仍 R2）                                                                                                 | 归档 `legacy-pre-module-v2-20260702/`；CLOSED 证据 → 路线图**附录 C**                                    |
| **当前下一队列 (v2)**       | **M-DATA-03** → **M-G1-03** → **M-G2/G4/G5-FULL**（可并行）→ **M-PASS-01**（末位 `PASS_ROUND4_REAL_DATA_READY` 门禁）；任务卡 Plan 冻结时创建                                                                                                         | `docs/implementation_tasks/README.md`；路线图 §3 v2；`MIGRATION_MAP.md`                                  |
| Round4/5 产品               | I 组 I1–I8 除 I3 壳外仍 R0–R1；**须 M-PASS-01 后** B04 开工                                                                                                                                                                                           | `BATCH_04_TASK_CARD_MANIFEST.md`；历史 `ROUND_4_*` / `ROUND_5_*` 见归档 `legacy-pre-module-v2-20260702/` |

## 3. 仓库顶层目录地图

| 路径                                                               | 类型               | 用途                                                                                                                                         | 是否实现地址         |
| ------------------------------------------------------------------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `backend/app/`                                                     | Python 后端实现    | FastAPI、数据源、同步、DB、五层模型、Agent、通知、校验等后端实现                                                                             | 是                   |
| `frontend/src/`                                                    | 前端实现           | Vite + React + TypeScript Dashboard shell 与后续页面                                                                                         | 是                   |
| `scripts/`                                                         | CLI / 维护脚本实现 | 初始化 DB、同步 registry、文档检查、生产 gate、smoke 等                                                                                      | 是                   |
| `configs/`                                                         | 本地配置           | datasource、alert、resource limits、market registry、qmt、layer1 axes 等运行配置                                                             | 是，配置入口         |
| `tests/`                                                           | 自动化测试         | pytest、contract gate、smoke、边界测试                                                                                                       | 是，测试实现         |
| `data/`                                                            | 运行数据           | DuckDB、raw、parquet、reports、audit、cache、files                                                                                           | 运行产物，不是源代码 |
| `docs/`                                                            | 设计/治理文档      | 架构、模块、运维、任务、质量、ADR、交接                                                                                                      | **否：设计依据**     |
| `specs/`                                                           | 契约/定义/spec     | schema、contracts、registry、Layer specs                                                                                                     | **否：契约依据**     |
| `MIGRATION_MAP.md`                                                 | 项目地图           | 跨目录索引、旧口径防恢复、MANIFEST 说明                                                                                                      | 否                   |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                                | 前向实施规划 SSOT  | 根目录**唯一活规划**；51 Module ID 模块闭环队列 v2（M-DATA-03→M-G\*→M-PASS-01）；历史 Wave 见 §3L / 附录 C；**地图不是工单，任务卡才是工单** | 否                   |
| `MODULE_COMPLETION_RATING.md`                                      | 模块完成度快照     | **活评级 SSOT**（Pass E @ 2026-07-02）；Rating 只信代码+测试；不得用文档 alone 冒充 `R6_FULL_PRODUCTION_STABLE`                              | 否                   |
| `docs/archive/`                                                    | 历史归档           | 旧版路线图备份（`planning/PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md`）、Wave4 协调笔记（`coordination/wave4-dcp-parallel/`）等       | 否                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/` | 历史任务包归档     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 全文、全部 `ROUND_*` 历史任务卡等（只读证据，**非**开工 SSOT）                                          | 否                   |
| `MANIFEST.json`                                                    | 发布输出清单       | 修复包文件清单与 hash；不是权威输入                                                                                                          | 否                   |
| `README.md`                                                        | 稳定入口           | 项目简介、边界、启动步骤、关键保护规则                                                                                                       | 否                   |

## 4. `docs/` 设计文档目录地图

### 4.1 根入口与角色指南

| 路径                                 | 用途                                                                   |
| ------------------------------------ | ---------------------------------------------------------------------- |
| `docs/START_HERE.md`                 | 第一阅读入口；说明角色路由、Round2.6 边界、只改设计文档/执行计划等提示 |
| `docs/INDEX.md`                      | 普通文档导航 hub；交叉引用根 `MIGRATION_MAP.md`                        |
| `docs/DEVELOPER_GUIDE.md`            | 开发者入口；Round2.6、验证命令、实施提示                               |
| `docs/OPERATOR_GUIDE.md`             | 本地运维与安全数据同步入口                                             |
| `docs/RESEARCHER_GUIDE.md`           | Layer/review 研究入口                                                  |
| `docs/ROUND3_HANDOFF.md`             | Round 3 建模层交接资料                                                 |
| `docs/AUDIT_DEFERRED_REGISTRY.md`    | 审计延后项 / resolved 项的权威登记                                     |
| `docs/RESOLVED_ISSUES_REGISTRY.md`   | 已解决问题登记；用于避免重复修复或误判仍 OPEN                          |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | 未解决问题登记；用于后续任务精准接续                                   |

### 4.2 架构文档 `docs/architecture/`

| 路径                                                           | 用途                                                             |
| -------------------------------------------------------------- | ---------------------------------------------------------------- |
| `docs/architecture/00_project_overview.md`                     | 总体项目定位：本地优先、监控而非自动交易、五层模型总览           |
| `docs/architecture/01_context_and_scope.md`                    | 上下文、使用范围、非目标、人工确认边界                           |
| `docs/architecture/02_solution_strategy.md`                    | 总体方案策略                                                     |
| `docs/architecture/03_runtime_flows.md`                        | 运行链路：数据抓取、写入、前端、Agent 主链路                     |
| `docs/architecture/04_data_architecture.md`                    | 数据架构：DuckDB、Raw Store、Parquet、WriteManager               |
| `docs/architecture/05_module_map.md`                           | 模块地图：各模块职责与边界                                       |
| `docs/architecture/06_deployment_and_local_ops.md`             | 本地部署与运维策略，含 Round2.6 平台矩阵补充                     |
| `docs/architecture/07_project_directory_structure.md`          | 项目目录结构说明                                                 |
| `docs/architecture/08_decision_log_index.md`                   | ADR/决策索引                                                     |
| `docs/architecture/09_phase_plan.md`                           | 分阶段交付计划                                                   |
| `docs/architecture/10_external_references.md`                  | 外部参考与采纳边界                                               |
| `docs/architecture/11_final_conclusion.md`                     | 最终结论                                                         |
| `docs/architecture/module_boundary_matrix.md`                  | Round2.6 import/module boundary matrix；只定义设计边界，不改代码 |
| `docs/architecture/layer1_ingestion_refactor_rollback_plan.md` | Layer1 ingestion 重构回滚计划                                    |

### 4.3 ADR 与决策记录

| 路径                                                                        | 用途                                                 |
| --------------------------------------------------------------------------- | ---------------------------------------------------- |
| `docs/adr/ADR-0001-use-duckdb-local-first.md`                               | DuckDB local-first 决策                              |
| `docs/adr/ADR-0002-agent-readonly-boundary.md`                              | Agent 只读边界决策                                   |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                          | Layer 1 标准化范围决策                               |
| `docs/adr/ADR-0004-layer3-shock-anchor-model.md`                            | Layer 3 shock-anchor 模型决策                        |
| `docs/adr/ADR-0005-primary-validation-fallback-source-model.md`             | Primary / Validation / FallbackPolicy 数据源角色决策 |
| `docs/decisions/README.md`                                                  | 工程决策目录入口（ADR-001～015）                     |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | ingestion / validation / write transaction 边界      |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`                      | DB CHECK 与应用层 validation 分工                    |
| `docs/decisions/ADR-003-implementation-path-mapping.md`                     | 实现路径映射决策                                     |
| `docs/decisions/ADR-004-write-path-complexity-ceiling.md`                   | 写入热路径 C901 复杂度不修                           |
| `docs/decisions/ADR-006-sync-datasource-service-fail-closed.md`             | 生产 Sync 须显式 `datasource_service=`               |

### 4.4 模块设计文档 `docs/modules/`

| 路径                                                | 模块/主题                             | 备注                                                         |
| --------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------ |
| `docs/modules/README.md`                            | 模块文档索引                          | 标明权威文件 vs 兼容索引                                     |
| `docs/modules/data_sources.md`                      | 数据源与 adapter 设计                 | Primary / Validation / FallbackPolicy；Round2.6 三层边界补充 |
| `docs/modules/source_capability_registry.md`        | Source Capability Registry            | Round2.6 权威补充模块                                        |
| `docs/modules/source_route_plan.md`                 | SourceRoutePlan                       | Round2.6 权威补充模块                                        |
| `docs/modules/datasource_service.md`                | DataSourceService facade              | Round2.6 权威补充模块                                        |
| `docs/modules/qmt_xtdata_adapter.md`                | QMT / xtdata adapter                  | QMT 默认禁用，用户授权后启用                                 |
| `docs/modules/data_sync_orchestrator.md`            | 数据同步 orchestrator                 | FullLoad、Incremental、Backfill、RevisionAudit、Reconcile    |
| `docs/modules/data_validation_and_conflict.md`      | 数据质量与多源冲突                    | 权威设计文档                                                 |
| `docs/modules/data_validation_write_concurrency.md` | validation/write concurrency 兼容索引 | 勿作唯一实现依据；拆分到 validation 与 write_manager         |
| `docs/modules/write_manager.md`                     | WriteManager 与写入并发               | 权威设计文档                                                 |
| `docs/modules/duckdb_and_parquet.md`                | DuckDB / Parquet                      | 本地存储设计                                                 |
| `docs/modules/local_file_system.md`                 | 本地文件系统                          | raw/files/reports/audit 等本地数据组织                       |
| `docs/modules/layer1_global_regime_panel.md`        | 五层模型 Layer 1：Global Regime Panel | 全量标准化主要发生在 L1                                      |
| `docs/modules/layer2_cross_asset_sensor.md`         | Layer 2：Cross Asset Sensor           | 跨资产传感器                                                 |
| `docs/modules/layer3_industry_shock_anchor.md`      | Layer 3：Industry Shock Anchor        | 全球产业链与冲击锚                                           |
| `docs/modules/layer4_market_structure.md`           | Layer 4：Market Structure             | 市场结构                                                     |
| `docs/modules/layer5_security_evidence.md`          | Layer 5：Security Evidence            | 个股证据链                                                   |
| `docs/modules/fastapi_backend.md`                   | FastAPI 后端                          | 权威后端 API 设计                                            |
| `docs/modules/frontend_dashboard.md`                | 前端 Dashboard                        | 权威前端设计；正式实现前需用户确认 UI                        |
| `docs/modules/fastapi_and_frontend.md`              | FastAPI/frontend 兼容索引             | 兼容旧链接，勿作唯一实现依据                                 |
| `docs/modules/agent_module.md`                      | Agent 模块                            | 只读、白名单、抗提示注入                                     |
| `docs/modules/notification_and_reports.md`          | 通知与报告                            | 去重、冷却、隐私、留存                                       |
| `docs/modules/backtest_and_review.md`               | 回测与复盘                            | 防前视偏差、冻结样本、参数快照                               |
| `docs/modules/backtest_review_lifecycle.md`         | Backtest Review Lifecycle             | Round2.6 权威补充模块                                        |
| `docs/modules/review_sandbox_api.md`                | Review Sandbox API                    | Round2.6 权威补充模块                                        |
| `docs/modules/ops_and_performance.md`               | 运维与性能                            | ResourceGuard、本机低占用、性能边界                          |

### 4.5 API 叙述文档 `docs/api/`

| 路径                               | 用途                                         |
| ---------------------------------- | -------------------------------------------- |
| `docs/api/fastapi_routes.md`       | FastAPI 路由、分页、鉴权、查询预算等叙述设计 |
| `docs/api/agent_tool_contracts.md` | Agent tool 契约叙述说明                      |

### 4.6 运维与安全文档 `docs/ops/`

| 路径                                         | 用途                                                |
| -------------------------------------------- | --------------------------------------------------- |
| `docs/ops/agent_security_policy.md`          | Agent 安全、只读、固定来源、抗提示注入              |
| `docs/ops/agent_workflow_boundaries.md`      | `.cursor` / `.trellis` 信任边界与 workflow 清理     |
| `docs/ops/backup_and_recovery.md`            | 备份与恢复策略                                      |
| `docs/ops/config_secret_policy.md`           | Secret 与 `.env.local` 策略                         |
| `docs/ops/daily_weekly_monthly_checklist.md` | 日/周/月例行检查                                    |
| `docs/ops/data_sync_command_matrix.md`       | Round2.6 数据同步 CLI 命令矩阵                      |
| `docs/ops/data_sync_quick_reference.md`      | Round2.6 安全数据同步速查                           |
| `docs/ops/ERROR_CODE_GUIDE.md`               | Round2.6 错误码指南                                 |
| `docs/ops/db_inspect_cli.md`                 | QMD 本地只读 DB inspect CLI 设计；Round3 early 输入 |
| `docs/ops/frontend_security_policy.md`       | 前端安全策略                                        |
| `docs/ops/idempotency_retry_dlq_policy.md`   | 幂等、重试、DLQ 策略                                |
| `docs/ops/incident_playbook.md`              | 事件处理 playbook                                   |
| `docs/ops/layer3_config_health_check.md`     | Layer 3 配置健康检查                                |
| `docs/ops/lock_and_concurrency_policy.md`    | 锁与并发策略                                        |
| `docs/ops/logs_health_audit.md`              | 日志、健康检查、审计                                |
| `docs/ops/migration_recovery_policy.md`      | migration 备份恢复策略                              |
| `docs/ops/ops_and_performance_v1_2.md`       | 运维手册；旧文件名但内容仍当前                      |
| `docs/ops/performance_limits.md`             | ResourceGuard 与性能限制权威                        |
| `docs/ops/privacy_data_flow.md`              | Round2.6 local-only / privacy data flow             |
| `docs/ops/privacy_retention_policy.md`       | 隐私与留存策略                                      |
| `docs/ops/qmt_xqshare_setup.md`              | 可选 qmt_xqshare 设置边界                           |
| `docs/ops/TROUBLESHOOTING.md`                | 故障排查入口                                        |
| `docs/ops/verification_commands.md`          | Windows / 本地验证命令                              |
| `docs/ops/user_intervention_policy.md`       | Agent vs 用户介入边界（Loop Engineering）           |
| `docs/ops/data_health_cli.md`                | 数据健康 CLI 设计                                   |
| `docs/ops/ops_report_cli.md`                 | 运维报告 CLI 设计                                   |

### 4.7 质量与发布治理 `docs/quality/`

| 路径                                           | 用途                                                                                |
| ---------------------------------------------- | ----------------------------------------------------------------------------------- |
| `docs/quality/待修复清单.md`                   | 全项目开放待修复 SSOT                                                               |
| `docs/quality/final_package_rules.md`          | 最终发布包规则                                                                      |
| `docs/quality/PENDING_USER_DECISIONS.md`       | 用户已拍板 D-01 至 D-12，执行角色不得反复询问                                       |
| `docs/quality/production_live_pilot_policy.md` | Batch 2.75 受控生产/live 数据试点门禁；授权、sandbox、raw-only、no-mutation 规则    |
| `docs/quality/staged_acceptance_policy.md`     | 分阶段验收策略                                                                      |
| `docs/quality/KNOWN_PYTEST_SKIPS.md`           | 已知 pytest skip 登记                                                               |
| `rules/GLOBAL_TESTING_POLICY.md` §7            | 测试五字段 docstring 规范与 CI 门禁（`tests/test_docstring_quadruple_coverage.py`） |

### 4.8 Schema 迁移说明 `docs/schema/`

| 路径                                | 用途                                     |
| ----------------------------------- | ---------------------------------------- |
| `docs/schema/MIGRATION_COVERAGE.md` | 设计 schema 与已应用 migrations 覆盖矩阵 |

### 4.9 实施任务包 `docs/implementation_tasks/`

> **2026-07-02 布局：** 活目录仅保留全局契约（下表「活路径」）；全部 `ROUND_*` / Wave / DCP 历史任务卡已迁入 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/`（**历史归档**，只读证据）。路径解析：`scripts/repo_path_resolve.py` · `tests/repo_paths.py`（`impl_task()` / `resolve_repo_path()`）。**活规划 SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · §4.12 模块票队列。
>
> 所有路径仍属于设计/计划/验收输入，不是实现代码落点。

#### 4.9.1 活路径（全局契约 + v2 入口）

| 路径                                                         | 用途                                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `docs/implementation_tasks/README.md`                        | **活工单入口**；v2 模块票队列摘要                                         |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                          | 活规划 SSOT（§3 模块闭环队列 v2）                                         |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`      | Plan 阶段上下文桥；原始任务、设计/契约与 `.trellis/tasks/**` 冻结计划追溯 |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`        | 全局执行规则                                                              |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`        | 全局资源限制                                                              |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`          | 任务模板                                                                  |
| `rules/GLOBAL_TESTING_POLICY.md`                             | 全局测试政策                                                              |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | 未解决项与任务卡覆盖映射（活）                                            |

#### 4.9.2 历史归档索引（`legacy-pre-module-v2-20260702/`）

| 路径                                                                                                                                                                                  | 用途                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/README.md`                                                                                                           | 归档说明；活 SSOT 指针                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                  | **历史归档** Round3 六批次切分、Batch 2.5 bridge、Batch 2.75 pilot gate（根目录无 stub） |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`                                                                        | 生产补齐**覆盖地图**（非 standalone 工单）                                               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/BATCH_FOLDER_REHOME_PLAN.md`                                                                                         | 任务包目录重组计划（历史）                                                               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_EARLY_CLOSE_PLAN.md`                                                                                          | Round3 early close 计划（历史）                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_PASS_EXECUTION_PLAN.archived-20260702.md` | Tier A 逐源表只读索引；M-DATA-03 设计输入                                                |

#### 4.9.3 历史任务卡明细（Round 0–5 · 只读）

| 路径                                                                                                                                                                                    | 用途                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/000_global_execution_rules.md`                                                                | Round 0 全局执行规则任务                                                                                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/001_create_project_scaffold.md`                                                               | 创建项目脚手架任务                                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/002_create_config_and_env_templates.md`                                                       | 创建配置与 env 模板任务                                                                                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/003_create_testing_baseline.md`                                                               | 创建测试基线任务                                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/004_create_documentation_index.md`                                                            | 创建文档索引任务；本地图是其强制输入                                                                     |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_0_PROJECT_SCAFFOLD/README.md`                                                                                    | Round 0 入口                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/005_create_schema_sql.md`                                                                      | 创建 schema SQL 任务                                                                                     |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/006_implement_resource_guard.md`                                                               | ResourceGuard 实施任务                                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/007_implement_duckdb_connection_manager.md`                                                    | DuckDB connection manager 实施任务                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/008_implement_write_manager.md`                                                                | WriteManager 实施任务                                                                                    |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/009_implement_file_registry_and_raw_store.md`                                                  | file registry / raw store 实施任务                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/010_foundation_smoke_tests.md`                                                                 | foundation smoke tests 任务                                                                              |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/DECISIONS.md`                                                                                  | Round 1 决策记录                                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/README.md`                                                                                     | Round 1 入口                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/005_schema.plan.md`                                                                      | 005 schema 计划                                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/006_resource_guard.plan.md`                                                              | 006 resource guard 计划                                                                                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/007_connection.plan.md`                                                                  | 007 connection 计划                                                                                      |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/008_write_manager.plan.md`                                                               | 008 write manager 计划                                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/009_raw_store.plan.md`                                                                   | 009 raw store 计划                                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_1_DATA_FOUNDATION/plans/010_smoke.plan.md`                                                                       | 010 smoke 计划                                                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/011_implement_source_registry.md`                                                    | source registry 实施任务                                                                                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/012_implement_data_adapter_contract.md`                                              | data adapter contract 实施任务                                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md`                                             | core adapter skeletons 实施任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md`                                             | data sync orchestrator 实施任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md`                                             | data quality validator 实施任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md`                                          | source conflict validator 实施任务                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md`                                                            | Batch B 修复状态                                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md`                                                                   | Batch C 台账                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_REPAIR_STATUS.md`                                                            | Batch C 修复状态                                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_D_STATUS.md`                                                                   | Batch D 状态                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md`                                                                        | Round 2 决策记录                                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/README.md`                                                                           | Round 2 入口                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/ROUND2_GAPS_AND_DEVIATIONS.md`                                                       | Round 2 gaps / deviations 台账                                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/plans/011_012_batch_a.plan.md`                                                       | Batch A 计划                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/plans/013_batch_b.plan.md`                                                           | Batch B 计划                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/plans/014_batch_d.plan.md`                                                           | Batch D 计划                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_DATA_INGESTION_VALIDATION/plans/015_016_batch_c.plan.md`                                                       | Batch C 计划                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md`                                  | Source Capability Registry 设计任务                                                                      |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md`                    | SourceRoutePlan 与 DataSourceService 设计任务                                                            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016C_define_module_boundary_contract.md`                                    | 模块边界契约设计任务                                                                                     |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md`                  | data sync quick reference 与 error guide 设计任务                                                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016E_define_platform_source_matrix_and_qmt_xqshare.md`                      | platform source matrix 与 qmt_xqshare 设计任务                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md`                             | production-equivalent scale benchmark 设计任务                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/README.md`                                                                  | Round2.6 入口                                                                                            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`                                                           | Layer 1 axis loader 实施任务                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md`                                               | Layer 1 interpretation snapshot 实施任务                                                                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`                                                   | Round3 Batch 2.5 Layer 1 observation ingestion bridge；五阶段 Gate 与逐阶段审计                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`                                                            | Round3 Batch 2.75 受控生产/live 数据试点门禁；正式实现前的任务卡与验收边界                               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`                                                    | Layer 2 cross-asset sensor 实施任务                                                                      |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md`                                                 | Layer 3 industry chain loader 实施任务                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md`                                                      | Layer 3 snapshot builder 实施任务                                                                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md`                                                      | Layer 4 market structure 实施任务                                                                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`                                                        | Layer 5 evidence chain 实施任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/README.md`                                                                                     | Round 3 入口                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md`                                   | **历史归档** Batch 3F-R；参考采纳 refactor（CLOSED 证据）                                                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_01_REFERENCE_RULES_AND_LICENSE_GATE.md` | R3FR-01 护栏与 license gate 重跑任务卡                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_03_TDX_PROVIDER_REFACTOR.md`            | R3FR-03 TDX provider port；`backend/app/datasources/fetch_ports/tdx_pytdx_port.py`、`normalizers/tdx.py` |
| `.trellis/tasks/archive/2026-06/06-26-round3fr-tdx-provider/`                                                                                                                           | R3FR-03 Trellis 执行计划（历史归档；`EXECUTION_INDEX.md` + frozen）                                      |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/README.md`                                                    | Batch 3G sandbox clean-write（3F-R 后）                                                                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/README.md`                                      | Batch 3H 真实源生产入口（3G 后）                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`      | Wave 1 串行门控索引（R3H-10 → R3H-07）                                                                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_10_DATASOURCE_SERVICE_SSOT.md`              | **历史归档** R3H-10 DataSourceService SSOT（C2+E4）；活票见 **M-DATA-03**                                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_07_US_TRADING_CALENDAR.md`                  | **历史归档** R3H-07 US 交易日历（G4+C3 · CLOSED）                                                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_DATA_PRODUCTION_READINESS/README.md`                                                                           | **历史归档** Batch 01 模型/源就绪（R3E/R3F 前身）                                                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`                                              | **历史归档** Batch 3F/6 数据治理                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md`                                                   | FastAPI routes 实施任务                                                                                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/025_implement_agent_tool_layer.md`                                                 | Agent tool layer 实施任务                                                                                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md`                                                   | Frontend shell 实施任务                                                                                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md`                                             | Frontend layer pages 实施任务                                                                            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md`                                        | Reports and notifications 实施任务                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md`                                              | Backtest and review 实施任务                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/030_implement_no_action_semantics_guard.md`                                        | no-action semantics guard 实施任务                                                                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/README.md`                                                                         | Round 4 入口                                                                                             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md`                                                  | integration smoke tests 实施任务                                                                         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/032_implement_resource_limit_tests.md`                                                     | resource limit tests 实施任务                                                                            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md`                                              | security and boundary tests 实施任务                                                                     |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md`                                                   | docs consistency check 实施任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md`                                                    | final package cleanup 实施任务                                                                           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md`                                                      | final release manifest 创建任务                                                                          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/README.md`                                                                                 | Round 5 入口                                                                                             |

### 4.10 Round 3 扩展任务包（对抗性审计 / 并行 prompt / 参考落地 / 评审）

> 下列路径均为**历史归档**（`legacy-pre-module-v2-20260702/`）。`UNRESOLVED_ITEM_TASK_COVERAGE.md` 为活路径，见 §4.9.1。

| 路径                                                                                                                                                          | 用途                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                                  | 未解决项与任务卡覆盖映射               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`                                    | 018C TDX 低成本 probe 任务卡           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/023A_layer5_evidence_foundation.md`                                  | 023A Layer5 evidence foundation 任务卡 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_contract_architecture_adversarial_audit.md`           | R3X 契约架构对抗审计                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md`                      | R3X 数据源路由 blocker                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_db_write_validation_blockers.md`                      | R3X DB 写入校验 blocker                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_low_touch_bucket_c.md`                       | R3X ponytail bucket C                  |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_ponytail_pilot_prep_bucket_a.md`                      | R3X ponytail pilot prep bucket A       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`                            | R3X 真实数据 staged pilot              |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_residual_open_items_closure.md`                       | R3X 残余 open items 关闭               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_execution_discipline_addendum.md`                     | R3Y 执行纪律附录                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`                 | R3Y post-R3X 严格对抗审计              |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`                           | R3Y 只读数据健康 v1                    |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`                         | R3Y staged pilot v2                    |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md`                | R3Y staged pilot v2 执行附录           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_00_integration_round3_merge_coordinator.md`                  | PROMPT_00 merge coordinator            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_01_feature_round3_batch3_staged_gate.md`                     | PROMPT_01 Batch3 staged gate           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_02_debt_r3b275_018c_low_cost_probe.md`                       | PROMPT_02 018C low cost probe          |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_03_debt_r3b275_perf_hyg_registry.md`                         | PROMPT_03 perf hygiene registry        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_04_debt_r3b275_fred_staged_semantics.md`                     | PROMPT_04 FRED staged semantics        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_05_chore_round3_ci_gate_hardening.md`                        | PROMPT_05 CI gate hardening            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_06_debt_r3_ops_inspect_data_health_references.md`            | PROMPT_06 ops inspect references       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_07_feature_round3_019_layer2_sensor.md`                      | PROMPT_07 Layer2 sensor                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_08_feature_round3_023a_evidence_foundation.md`               | PROMPT_08 023A evidence                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_09_review_round3_019_plan_audit.md`                          | PROMPT_09 019 plan audit               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_10_debt_r3b275_018c_live_manual_probe_plan.md`               | PROMPT_10 018C live manual probe       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_11_review_round3_contract_architecture_adversarial_audit.md` | PROMPT_11 contract adversarial audit   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_12_fix_round3_data_source_routing_blockers.md`               | PROMPT_12 routing blockers             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_13_fix_round3_db_write_validation_blockers.md`               | PROMPT_13 DB write blockers            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_14_feature_round3_real_data_staged_pilot.md`                 | PROMPT_14 staged pilot                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_15_fix_round3_r3x_residual_open_items_closure.md`            | PROMPT_15 residual closure             |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_16_fix_round3_ponytail_pilot_prep_bucket_a.md`               | PROMPT_16 ponytail bucket A            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_17_debt_round3_ponytail_low_touch.md`                        | PROMPT_17 ponytail low touch           |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_18_review_round3_post_r3x_strict_adversarial_audit.md`       | PROMPT_18 post-R3X audit               |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_19_feature_round3_real_data_staged_pilot_v2.md`              | PROMPT_19 staged pilot v2              |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_PARALLEL_PROMPTS/PROMPT_20_feature_round3_readonly_data_health_v1.md`                | PROMPT_20 readonly data health         |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_LANDING/README.md`                                                         | Round 3 参考落地入口                   |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md`                                | R3D 018C live manual probe plan        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`                                 | R3D 018C low cost probe                |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`                               | R3D ops DB data health 参考            |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REFERENCE_LANDING/R4D_readonly_sql_assistant_reference.md`                           | R4D readonly SQL assistant 参考        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REVIEW/019_plan_audit_report.md`                                                     | 019 plan 审计报告                      |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_REVIEW/019_plan_audit_review.md`                                                     | 019 plan 审计评审                      |

### 4.11 Round 3V verified audit cleanup（Batch 3V）

| 路径                                                                                                                                                              | 用途                                     |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`                        | **历史归档** Batch 3V 协调入口（CLOSED） |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md` | 六路主会话协调手册                       |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_TASK_CARD_MANIFEST.md`   | 任务卡清单与分支归属                     |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_HARDENING_RULES.md`      | Batch 3V 硬化规则                        |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_SELF_CHECK.md`           | 静态自检与 dispatch 门禁                 |
| `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_ADVERSARIAL_AUDIT.md`    | 任务卡对抗审计                           |

### 4.12 模块闭环队列 v2（活票 · Plan 冻结时建目录）

> **SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · `docs/implementation_tasks/README.md`。下列目录 **待建**（Plan 冻结时创建 canonical 文件夹 + Trellis complex 票）。

| 票 ID         | 优先级 | 任务卡目录（待建）                                 | `/to-issues` 索引（待建）          | 设计权威                                                                      |
| ------------- | ------ | -------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------- |
| **M-DATA-03** | P0     | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/` | `.../M_DATA_03_TO_ISSUES_INDEX.md` | 归档 `R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1 Tier A · 路线图 §3.1 |
| **M-G1-03**   | P0     | `docs/implementation_tasks/M_G1_03_LAYER1_FULL/`   | `.../M_G1_03_TO_ISSUES_INDEX.md`   | `specs/layer1_axes/` · `docs/modules/layer1_global_regime_panel.md`           |
| **M-G2-FULL** | P1     | `docs/implementation_tasks/M_G2_FULL/`             | `.../M_G2_FULL_TO_ISSUES_INDEX.md` | `docs/modules/layer2_cross_asset_sensor.md` §2                                |
| **M-G4-FULL** | P1     | `docs/implementation_tasks/M_G4_FULL/`             | `.../M_G4_FULL_TO_ISSUES_INDEX.md` | `docs/modules/layer4_market_structure.md` §2                                  |
| **M-G5-FULL** | P1     | `docs/implementation_tasks/M_G5_FULL/`             | `.../M_G5_FULL_TO_ISSUES_INDEX.md` | `docs/modules/layer5_security_evidence.md` §2–3                               |
| **M-PASS-01** | P0     | `docs/implementation_tasks/M_PASS_01/`             | `.../M_PASS_01_TO_ISSUES_INDEX.md` | 路线图 §6.1.1 `PASS_ROUND4_REAL_DATA_READY` 门禁清单                          |

## 5. `specs/` 契约与定义目录地图

### 5.1 API、schema、frontend

| 路径                                 | 用途                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------- |
| `specs/api/openapi_contract.md`      | OpenAPI 契约                                                                          |
| `specs/schema/schema.sql`            | 设计 schema SQL；注意与实际 migrations 覆盖关系见 `docs/schema/MIGRATION_COVERAGE.md` |
| `specs/frontend/page_contracts.yaml` | 前端页面契约                                                                          |

### 5.2 数据源 registry

| 路径                                                 | 用途                                                     |
| ---------------------------------------------------- | -------------------------------------------------------- |
| `specs/datasource_registry/source_registry.yaml`     | 数据源注册表；Primary / Validation / FallbackPolicy 权威 |
| `specs/datasource_registry/source_capabilities.yaml` | Round2.6 source capability matrix                        |

### 5.3 通用 contracts `specs/contracts/`

| 路径                                                     | 用途                                                |
| -------------------------------------------------------- | --------------------------------------------------- |
| `specs/contracts/agent_contract.yaml`                    | Agent 契约                                          |
| `specs/contracts/api_security_contract.yaml`             | API 安全、分页、查询预算权威                        |
| `specs/contracts/backtest_contract.yaml`                 | 回测契约                                            |
| `specs/contracts/backtest_metric_contract.yaml`          | 回测指标契约                                        |
| `specs/contracts/backtest_reproducibility_contract.yaml` | 回测可复现契约                                      |
| `specs/contracts/backup_recovery_contract.yaml`          | 备份恢复契约                                        |
| `specs/contracts/data_adapter_contract.md`               | 数据 adapter 契约                                   |
| `specs/contracts/data_cli_contract.yaml`                 | 数据 CLI 契约                                       |
| `specs/contracts/data_quality_rules.yaml`                | 数据质量规则                                        |
| `specs/contracts/datasource_service_contract.yaml`       | DataSourceService 契约                              |
| `specs/contracts/dependency_extras_contract.yaml`        | optional dependency extras 契约                     |
| `specs/contracts/diagnostics_api_contract.yaml`          | Diagnostics API 契约                                |
| `specs/contracts/layer1_axis_contract.yaml`              | Layer 1 axis 契约                                   |
| `specs/contracts/layer2_sensor_contract.yaml`            | Layer 2 sensor 契约                                 |
| `specs/contracts/layer3_loader_contract.yaml`            | Layer 3 loader 契约                                 |
| `specs/contracts/layer4_market_contract.yaml`            | Layer 4 market 契约                                 |
| `specs/contracts/layer5_evidence_contract.yaml`          | Layer 5 evidence 契约                               |
| `specs/contracts/log_audit_contract.yaml`                | 日志审计契约                                        |
| `specs/contracts/module_boundary_contract.yaml`          | 模块边界契约                                        |
| `specs/contracts/notification_report_contract.yaml`      | 通知报告契约                                        |
| `specs/contracts/ops_health_check_contract.yaml`         | 运维健康检查契约                                    |
| `specs/contracts/ops_db_inspect_contract.yaml`           | QMD 本地只读 DB inspect CLI 契约                    |
| `specs/contracts/platform_source_matrix.yaml`            | 平台数据源矩阵                                      |
| `specs/contracts/reference_adoption_guardrails.yaml`     | 外部参考采纳红线                                    |
| `specs/contracts/release_cleanup_allowlist.yaml`         | 发布清理 allowlist                                  |
| `specs/contracts/resource_limits.yaml`                   | 资源限制契约                                        |
| `specs/contracts/review_sandbox_contract.yaml`           | Review Sandbox 契约                                 |
| `specs/contracts/runtime_flow_contract.yaml`             | 运行链路契约                                        |
| `specs/contracts/runtime_versions.md`                    | Python / frontend runtime、`uv.lock` 与验收命令契约 |
| `specs/contracts/snapshot_lineage_contract.yaml`         | 快照 lineage 契约                                   |
| `specs/contracts/source_capability_contract.yaml`        | Source Capability 契约                              |
| `specs/contracts/source_conflict_rules.yaml`             | 多源冲突规则                                        |
| `specs/contracts/source_route_contract.yaml`             | Source Route 契约                                   |
| `specs/contracts/spec_migrator_contract.yaml`            | spec migrator 契约                                  |
| `specs/contracts/sync_job_contract.yaml`                 | sync job 契约                                       |
| `specs/contracts/user_input_privacy_contract.yaml`       | 用户输入隐私契约                                    |
| `specs/contracts/write_contract.yaml`                    | 写入契约                                            |

### 5.4 Layer 1 axis specs

| 路径                                                                                                  | 用途                    |
| ----------------------------------------------------------------------------------------------------- | ----------------------- |
| `specs/layer1_axes/restructured_axes_v1_1/README.md`                                                  | Layer 1 axes specs 入口 |
| `specs/layer1_axes/restructured_axes_v1_1/common/common_axis_rules.md`                                | Layer 1 通用 axis 规则  |
| `specs/layer1_axes/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_engineering_rules.md` | credit stress 工程规则  |
| `specs/layer1_axes/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_indicator_spec.yaml`  | credit stress 指标 spec |
| `specs/layer1_axes/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_user_guide.md`        | credit stress 用户指南  |
| `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_engineering_rules.md`     | environment 工程规则    |
| `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml`      | environment 指标 spec   |
| `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_user_guide.md`            | environment 用户指南    |
| `specs/layer1_axes/restructured_axes_v1_1/liquidity_axis/liquidity_axis_engineering_rules.md`         | liquidity 工程规则      |
| `specs/layer1_axes/restructured_axes_v1_1/liquidity_axis/liquidity_axis_indicator_spec.yaml`          | liquidity 指标 spec     |
| `specs/layer1_axes/restructured_axes_v1_1/liquidity_axis/liquidity_axis_user_guide.md`                | liquidity 用户指南      |
| `specs/layer1_axes/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_engineering_rules.md` | risk appetite 工程规则  |
| `specs/layer1_axes/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_indicator_spec.yaml`  | risk appetite 指标 spec |
| `specs/layer1_axes/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_user_guide.md`        | risk appetite 用户指南  |
| `specs/layer1_axes/restructured_axes_v1_1/sentiment_axis/sentiment_axis_engineering_rules.md`         | sentiment 工程规则      |
| `specs/layer1_axes/restructured_axes_v1_1/sentiment_axis/sentiment_axis_indicator_spec.yaml`          | sentiment 指标 spec     |
| `specs/layer1_axes/restructured_axes_v1_1/sentiment_axis/sentiment_axis_user_guide.md`                | sentiment 用户指南      |

### 5.5 Layer 3 industry chain specs

| 路径                                                                                                                | 用途                               |
| ------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/README.md`                                  | Layer 3 industry chains specs 入口 |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_anchor_registry.json`                | anchor registry                    |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_cross_chain_edge_registry.json`      | cross-chain edge registry          |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_data_dictionary.md`                  | Layer 3 数据字典                   |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_edge_registry.json`                  | edge registry                      |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_global_industry_chain_registry.yaml` | global industry chain registry     |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/layer3_node_registry.json`                  | node registry                      |
| `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/references/source_registry.md`              | Layer 3 reference source registry  |

### 5.6 契约与验收索引（活）

| 路径                          | 用途                 |
| ----------------------------- | -------------------- |
| `specs/contracts/`            | 服务/数据契约（P0）  |
| `docs/modules/`               | 模块设计叙述         |
| `MODULE_COMPLETION_RATING.md` | 模块完成度与证据指针 |

> 历史 Loop Engineering 配置（`authority_graph.yaml`、`test_catalog.yaml` 等）已移除；见 `docs/archive/trellis-loop-2026/`。

## 6. 模块 → 设计文档 / 契约 / 规则 / 实现目录映射

> 读取顺序建议：先读“设计文档”，再读“契约/定义”，然后读“规则/任务/验收”，最后进入“实现目录”。再次强调：`docs/` 与 `specs/` 是输入，不是落代码位置。

| 模块                         | 设计文档                                                                                                                                   | 契约/定义                                                                                                                                           | 规则/任务/验收                                                                                                                                                                                                                                                                                        | 实现目录入口                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 项目总体与边界               | `docs/architecture/00_project_overview.md`、`docs/architecture/01_context_and_scope.md`、`docs/architecture/02_solution_strategy.md`       | `specs/contracts/runtime_flow_contract.yaml`                                                                                                        | `docs/START_HERE.md`、`docs/INDEX.md`、`docs/quality/PENDING_USER_DECISIONS.md`                                                                                                                                                                                                                       | 全仓库；先不要改代码                                                                           |
| 目录结构与模块边界           | `docs/architecture/05_module_map.md`、`docs/architecture/07_project_directory_structure.md`、`docs/architecture/module_boundary_matrix.md` | `specs/contracts/module_boundary_contract.yaml`                                                                                                     | `scripts/check_module_boundaries.py`、`tests/test_module_boundaries.py`                                                                                                                                                                                                                               | `backend/app/**`、`frontend/src/**`                                                            |
| 数据架构 / DuckDB / Parquet  | `docs/architecture/04_data_architecture.md`、`docs/modules/duckdb_and_parquet.md`                                                          | `specs/schema/schema.sql`                                                                                                                           | `docs/schema/MIGRATION_COVERAGE.md`、`tests/test_schema_contract.py`                                                                                                                                                                                                                                  | `backend/app/db/`、`backend/app/storage/`、`data/duckdb/`、`data/parquet/`                     |
| QMD Ops DB Inspect CLI       | `docs/ops/db_inspect_cli.md`                                                                                                               | `specs/contracts/ops_db_inspect_contract.yaml`                                                                                                      | **活票 M-DATA-03**（`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1）；**历史** `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_EARLY_CLOSE_PLAN.md`、`docs/ROUND3_HANDOFF.md` | `backend/app/ops/`、`backend/app/cli/`、`scripts/`、`tests/`                                   |
| WriteManager / 写入并发      | `docs/modules/write_manager.md`                                                                                                            | `specs/contracts/write_contract.yaml`                                                                                                               | `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md`、`docs/ops/lock_and_concurrency_policy.md`                                                                                                                                                                                | `backend/app/storage/`、`backend/app/db/write_manager.py`、`backend/app/db/validation_gate.py` |
| Raw Store / 本地文件         | `docs/modules/local_file_system.md`                                                                                                        | `specs/contracts/snapshot_lineage_contract.yaml`                                                                                                    | `docs/ops/privacy_retention_policy.md`                                                                                                                                                                                                                                                                | `backend/app/storage/`、`data/raw/`、`data/files/`、`data/audit/`                              |
| ResourceGuard / 本机低占用   | `docs/modules/ops_and_performance.md`、`docs/ops/performance_limits.md`                                                                    | `specs/contracts/resource_limits.yaml`                                                                                                              | `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`、`configs/resource_limits.yaml`                                                                                                                                                                                                                 | `backend/app/core/`、`configs/`                                                                |
| 数据源 registry / adapter    | `docs/modules/data_sources.md`、`docs/modules/qmt_xtdata_adapter.md`                                                                       | `specs/datasource_registry/source_registry.yaml`、`specs/contracts/data_adapter_contract.md`                                                        | `docs/adr/ADR-0005-primary-validation-fallback-source-model.md`、`tests/test_source_registry.py`、`tests/test_adapter_skeletons.py`                                                                                                                                                                   | `backend/app/datasources/`、`configs/datasource.yml`                                           |
| Source Capability Registry   | `docs/modules/source_capability_registry.md`                                                                                               | `specs/datasource_registry/source_capabilities.yaml`、`specs/contracts/source_capability_contract.yaml`                                             | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md`、`tests/test_source_capabilities.py`                                                                                                           | `backend/app/datasources/`                                                                     |
| SourceRoutePlan              | `docs/modules/source_route_plan.md`                                                                                                        | `specs/contracts/source_route_contract.yaml`                                                                                                        | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md`、`tests/test_source_route_planner.py`                                                                                            | `backend/app/datasources/`                                                                     |
| DataSourceService            | `docs/modules/datasource_service.md`                                                                                                       | `specs/contracts/datasource_service_contract.yaml`                                                                                                  | **活票 M-DATA-03**（§3.1 11 源真网）；`tests/test_datasource_service.py`、`scripts/sync_registry.py`；**历史** 归档 `R3H_10_DATASOURCE_SERVICE_SSOT.md`                                                                                                                                               | `backend/app/datasources/`、`backend/app/sync/`                                                |
| 数据同步 orchestrator        | `docs/modules/data_sync_orchestrator.md`                                                                                                   | `specs/contracts/sync_job_contract.yaml`、`specs/contracts/data_cli_contract.yaml`                                                                  | `docs/ops/data_sync_quick_reference.md`、`docs/ops/data_sync_command_matrix.md`、`tests/test_sync_orchestrator.py`                                                                                                                                                                                    | `backend/app/sync/`、`backend/app/etl/`、`scripts/`                                            |
| 数据质量与冲突               | `docs/modules/data_validation_and_conflict.md`                                                                                             | `specs/contracts/data_quality_rules.yaml`、`specs/contracts/source_conflict_rules.yaml`                                                             | `docs/decisions/ADR-002-db-check-vs-app-validation.md`、`tests/test_data_quality_validator.py`、`tests/test_source_conflict_validator.py`                                                                                                                                                             | `backend/app/validators/`                                                                      |
| 五层模型 Layer 1             | `docs/modules/layer1_global_regime_panel.md`                                                                                               | `specs/contracts/layer1_axis_contract.yaml`、`specs/layer1_axes/restructured_axes_v1_1/**`                                                          | **活票 M-G1-03**（§3.2）；**历史** 归档 `ROUND_3_MODELING_LAYERS/017_*`、`018_*`、`018A_*`；`docs/adr/ADR-0003-layer1-standardization-only.md`                                                                                                                                                        | `backend/app/layer1_axes/`、`configs/layer1_axes.yml`                                          |
| Layer 1 observation bridge   | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`      | `specs/contracts/write_contract.yaml`、`specs/contracts/snapshot_lineage_contract.yaml`、`specs/contracts/source_route_contract.yaml`               | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2.5、`docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md`                                                                                                        | `backend/app/layer1_axes/ingestion.py`（Execute）、`backend/app/db/validation_gate.py`         |
| 五层模型 Layer 2             | `docs/modules/layer2_cross_asset_sensor.md`                                                                                                | `specs/contracts/layer2_sensor_contract.yaml`                                                                                                       | **活票 M-G2-FULL**（§3.3）；**历史** 归档 `ROUND_3_MODELING_LAYERS/019_*`、DCP-07 增量证据                                                                                                                                                                                                            | `backend/app/layer2_sensors/`                                                                  |
| 五层模型 Layer 3             | `docs/modules/layer3_industry_shock_anchor.md`                                                                                             | `specs/contracts/layer3_loader_contract.yaml`、`specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/**`                          | `docs/adr/ADR-0004-layer3-shock-anchor-model.md`、`docs/ops/layer3_config_health_check.md`、`docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md`、`021_implement_layer3_snapshot_builder.md`                       | `backend/app/layer3_chains/`                                                                   |
| 五层模型 Layer 4             | `docs/modules/layer4_market_structure.md`                                                                                                  | `specs/contracts/layer4_market_contract.yaml`                                                                                                       | **活票 M-G4-FULL**（§3.4）；**历史** 归档 `ROUND_3_MODELING_LAYERS/022_*`、DCP-08 增量证据                                                                                                                                                                                                            | `backend/app/layer4_markets/`、`configs/market_registry.yml`                                   |
| 五层模型 Layer 5             | `docs/modules/layer5_security_evidence.md`                                                                                                 | `specs/contracts/layer5_evidence_contract.yaml`                                                                                                     | **活票 M-G5-FULL**（§3.5）；**历史** 归档 `ROUND_3_MODELING_LAYERS/023_*`、DCP-10 增量证据                                                                                                                                                                                                            | `backend/app/layer5_evidence/`                                                                 |
| FastAPI 后端                 | `docs/modules/fastapi_backend.md`、`docs/api/fastapi_routes.md`                                                                            | `specs/api/openapi_contract.md`、`specs/contracts/api_security_contract.yaml`、`specs/contracts/diagnostics_api_contract.yaml`                      | `docs/ops/frontend_security_policy.md`、`tests/test_api_security_contract.py`                                                                                                                                                                                                                         | `backend/app/api/`、`backend/app/main.py`                                                      |
| 前端 Dashboard               | `docs/modules/frontend_dashboard.md`                                                                                                       | `specs/frontend/page_contracts.yaml`、`specs/contracts/api_security_contract.yaml`                                                                  | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md`、`027_implement_frontend_layer_pages.md`；正式 UI 前必须用户确认                                                                                                | `frontend/src/`                                                                                |
| Agent                        | `docs/modules/agent_module.md`、`docs/api/agent_tool_contracts.md`                                                                         | `specs/contracts/agent_contract.yaml`                                                                                                               | `docs/ops/agent_security_policy.md`、`docs/ops/agent_workflow_boundaries.md`、`docs/adr/ADR-0002-agent-readonly-boundary.md`                                                                                                                                                                          | `backend/app/agents/`                                                                          |
| 通知与报告                   | `docs/modules/notification_and_reports.md`                                                                                                 | `specs/contracts/notification_report_contract.yaml`、`specs/contracts/user_input_privacy_contract.yaml`                                             | `docs/ops/privacy_retention_policy.md`、`docs/ops/privacy_data_flow.md`                                                                                                                                                                                                                               | `backend/app/notifications/`、`data/reports/`                                                  |
| 回测与复盘                   | `docs/modules/backtest_and_review.md`、`docs/modules/backtest_review_lifecycle.md`                                                         | `specs/contracts/backtest_contract.yaml`、`specs/contracts/backtest_metric_contract.yaml`、`specs/contracts/backtest_reproducibility_contract.yaml` | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md`                                                                                                                                                            | `backend/app/` 内后续 backtest/review 模块落点                                                 |
| Review Sandbox / Diagnostics | `docs/modules/review_sandbox_api.md`                                                                                                       | `specs/contracts/review_sandbox_contract.yaml`、`specs/contracts/diagnostics_api_contract.yaml`                                                     | `docs/ops/TROUBLESHOOTING.md`、`docs/ops/ERROR_CODE_GUIDE.md`                                                                                                                                                                                                                                         | `backend/app/api/`、`backend/app/validators/`                                                  |
| QMT / xqshare 可选源         | `docs/modules/qmt_xtdata_adapter.md`                                                                                                       | `specs/contracts/platform_source_matrix.yaml`、`specs/contracts/dependency_extras_contract.yaml`                                                    | `docs/ops/qmt_xqshare_setup.md`、`configs/qmt.yml`；第一版默认禁用                                                                                                                                                                                                                                    | `backend/app/datasources/`、`configs/`                                                         |
| 发布清理 / manifest          | `docs/quality/final_package_rules.md`                                                                                                      | `specs/contracts/release_cleanup_allowlist.yaml`                                                                                                    | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md`、`036_create_final_release_manifest.md`                                                                                                                          | 发布脚本 / 后续 release 任务                                                                   |
| 参考项目采纳治理             | `docs/architecture/10_external_references.md`                                                                                              | `specs/contracts/reference_adoption_guardrails.yaml`                                                                                                | **历史** 归档 `BATCH_3FR_*` / `R3FR_01_*`、`tests/test_reference_adoption_guardrails.py`；覆盖地图 → 归档 `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`                                                                              | R3FR-01 不改 runtime；采纳细节在任务卡 `reference_project:` 块                                 |
| 日志 / 健康 / 审计           | `docs/ops/logs_health_audit.md`                                                                                                            | `specs/contracts/log_audit_contract.yaml`、`specs/contracts/ops_health_check_contract.yaml`                                                         | `docs/ops/incident_playbook.md`、`docs/ops/verification_commands.md`                                                                                                                                                                                                                                  | `backend/app/core/`、`scripts/`                                                                |

## 7. 旧设计内容 → 当前权威位置映射

| 原始内容/章节                | 当前权威位置                                                                                                                                                                           | 说明                                                       |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 总体项目定位                 | `docs/architecture/00_project_overview.md`                                                                                                                                             | 本地优先、少数人使用、监控而非自动交易                     |
| 上下文与边界                 | `docs/architecture/01_context_and_scope.md`                                                                                                                                            | 使用范围、非目标、人工确认边界                             |
| 方案策略                     | `docs/architecture/02_solution_strategy.md`                                                                                                                                            | 总体方案方法                                               |
| 运行链路                     | `docs/architecture/03_runtime_flows.md`、`specs/contracts/runtime_flow_contract.yaml`                                                                                                  | 数据抓取到前端/Agent 的主链路                              |
| 数据架构                     | `docs/architecture/04_data_architecture.md`                                                                                                                                            | DuckDB、Raw Store、Parquet、WriteManager                   |
| 模块地图                     | `docs/architecture/05_module_map.md`、`docs/architecture/module_boundary_matrix.md`                                                                                                    | 各模块职责与边界                                           |
| 目录结构                     | `docs/architecture/07_project_directory_structure.md`                                                                                                                                  | 项目目录说明；实现目录与文档目录分离                       |
| 运维与本机低占用             | `docs/ops/performance_limits.md` 与 `docs/modules/ops_and_performance.md`                                                                                                              | ResourceGuard、磁盘、内存、性能                            |
| 数据源设计                   | `docs/modules/data_sources.md` 与 `specs/datasource_registry/source_registry.yaml`                                                                                                     | Primary / Validation / FallbackPolicy                      |
| 数据源能力与路由             | `docs/modules/source_capability_registry.md`、`docs/modules/source_route_plan.md`、`docs/modules/datasource_service.md`                                                                | Round2.6 新增边界层                                        |
| 数据同步                     | `docs/modules/data_sync_orchestrator.md` 与 `specs/contracts/sync_job_contract.yaml`                                                                                                   | FullLoad、Incremental、Backfill、RevisionAudit、Reconcile  |
| 数据质量与冲突               | `docs/modules/data_validation_and_conflict.md`、`specs/contracts/data_quality_rules.yaml`、`specs/contracts/source_conflict_rules.yaml`                                                | 质量检查与多源冲突治理分离                                 |
| 五层模型                     | `docs/modules/layer1_global_regime_panel.md` 至 `docs/modules/layer5_security_evidence.md`                                                                                             | Layer 1-5 分层                                             |
| Layer 1 axis 定义            | `specs/layer1_axes/restructured_axes_v1_1/**`                                                                                                                                          | axis 工程规则、indicator specs、user guide                 |
| Layer 3 产业链定义           | `specs/layer3_global_industry_chains/layer3_global_industry_chains_v1_2/**`                                                                                                            | registry、node、edge、anchor、data dictionary              |
| API                          | `docs/api/fastapi_routes.md`、`docs/modules/fastapi_backend.md`、`specs/api/openapi_contract.md`、`specs/contracts/api_security_contract.yaml`                                         | FastAPI、分页、鉴权、查询预算                              |
| Frontend                     | `docs/modules/frontend_dashboard.md`、`specs/frontend/page_contracts.yaml`                                                                                                             | Dashboard shell 与页面契约；正式 UI 前需确认               |
| Agent                        | `docs/modules/agent_module.md`、`docs/api/agent_tool_contracts.md`、`specs/contracts/agent_contract.yaml`、`docs/ops/agent_security_policy.md`                                         | 只读、白名单、抗提示注入                                   |
| 通知与报告                   | `docs/modules/notification_and_reports.md`、`specs/contracts/notification_report_contract.yaml`、`docs/ops/privacy_retention_policy.md`                                                | 去重、冷却、隐私、留存                                     |
| 回测与复盘                   | `docs/modules/backtest_and_review.md`、`docs/modules/backtest_review_lifecycle.md`、`specs/contracts/backtest_contract.yaml`、`specs/contracts/backtest_reproducibility_contract.yaml` | 防前视偏差、冻结样本、参数快照                             |
| Review Sandbox / Diagnostics | `docs/modules/review_sandbox_api.md`、`specs/contracts/review_sandbox_contract.yaml`、`specs/contracts/diagnostics_api_contract.yaml`                                                  | Round2.6 后续 API 边界                                     |
| 最终发布                     | `docs/quality/final_package_rules.md`、`specs/contracts/release_cleanup_allowlist.yaml`                                                                                                | allowlist、dry-run、manifest                               |
| Round3 批次计划（根目录）    | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND3_BATCH_IMPLEMENTATION_MAP.md`                                                                                   | 2026-07-02 自根目录迁入；`repo_path_resolve.py` 自动路由   |
| 历史 ROUND/Wave 任务卡       | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_*`                                                                                                              | 只读证据；活 SSOT → `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 |
| 模块闭环活票（v2）           | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3 · `docs/implementation_tasks/M_*`（待建，见 §4.12）                                                                                             | M-DATA-03 → M-G\* → M-PASS-01 队列                         |
| Round4 B04 产品化            | `docs/implementation_tasks/archive/legacy-pre-module-v2-20260702/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_TASK_CARD_MANIFEST.md`            | **须 M-PASS-01 后**开工；I 组 I1–I8                        |
