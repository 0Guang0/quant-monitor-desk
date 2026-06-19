# MIGRATION_MAP

本文件是最终实施文档包的迁移映射索引，供 Claude Code / Codex 在拆分文档后定位“旧设计内容 → 新文件位置”。

## 1. 文件定位

- 本文件是 `004_create_documentation_index.md` 的强制输入。
- 本文件不是运行时代码，不参与数据库 migration。
- 本文件用于防止执行角色在多个文档版本之间迷路或误用旧口径。

## 2. 主要映射

| 原始内容/章节 | 当前权威位置 | 说明 |
|---|---|---|
| 总体项目定位 | `docs/architecture/00_project_overview.md` | 本地优先、少数人使用、监控而非自动交易 |
| 上下文与边界 | `docs/architecture/01_context_and_scope.md` | 使用范围、非目标、人工确认边界 |
| 运行链路 | `docs/architecture/03_runtime_flows.md` | 数据抓取到前端/Agent 的主链路 |
| 数据架构 | `docs/architecture/04_data_architecture.md` | DuckDB、Raw Store、Parquet、WriteManager |
| 模块地图 | `docs/architecture/05_module_map.md` | 各模块职责与边界 |
| 运维与本机低占用 | `docs/ops/performance_limits.md` 与 `docs/modules/ops_and_performance.md` | ResourceGuard、磁盘、内存、性能 |
| 数据源设计 | `docs/modules/data_sources.md` 与 `specs/datasource_registry/source_registry.yaml` | Primary / Validation / FallbackPolicy |
| 数据同步 | `docs/modules/data_sync_orchestrator.md` 与 `specs/contracts/sync_job_contract.yaml` | FullLoad、Incremental、Backfill、RevisionAudit、Reconcile |
| 数据质量与冲突 | `docs/modules/data_validation_and_conflict.md`、`specs/contracts/data_quality_rules.yaml`、`specs/contracts/source_conflict_rules.yaml` | 质量检查与多源冲突治理分离 |
| 五层模型 | `docs/modules/layer1_global_regime_panel.md` 至 `docs/modules/layer5_security_evidence.md` | Layer 1-5 分层 |
| API | `docs/api/fastapi_routes.md`、`specs/api/openapi_contract.md`、`specs/contracts/api_security_contract.yaml` | FastAPI、分页、鉴权、查询预算 |
| Agent | `docs/modules/agent_module.md`、`docs/api/agent_tool_contracts.md`、`specs/contracts/agent_contract.yaml`、`docs/ops/agent_security_policy.md` | 只读、白名单、抗提示注入 |
| 通知与报告 | `docs/modules/notification_and_reports.md`、`specs/contracts/notification_report_contract.yaml`、`docs/ops/privacy_retention_policy.md` | 去重、冷却、隐私、留存 |
| 回测与复盘 | `docs/modules/backtest_and_review.md`、`specs/contracts/backtest_contract.yaml`、`specs/contracts/backtest_reproducibility_contract.yaml` | 防前视偏差、冻结样本、参数快照 |
| 最终发布 | `docs/quality/final_package_rules.md`、`specs/contracts/release_cleanup_allowlist.yaml` | allowlist、dry-run、manifest |

## 3. 旧口径禁止恢复

- 不得恢复 `Primary / Shadow / Emergency` 作为数据源角色模型。
- 当前权威模型为 `Primary / Validation / FallbackPolicy`。
- 旧数据源角色 `Shadow` / `Emergency` 不能作为 source role、default role、fallback role、API role、DB role 或前端 source-role 展示恢复。
- Layer 1 `SHADOW` 诊断标签是窄例外：允许出现在明确带诊断/旁证语义的 Layer 1 indicator 条目、`shadow_diagnostics` 分组、`schema_note` 或说明文档中；不得进入 `source_registry` 角色字段，不得接管 clean 主值。若不在 `shadow_diagnostics` 分组下，必须显式写明 `diagnostic_only` / `evidence_only` / `does_not_replace_main_indicator` 或同等约束。

## 4. MANIFEST 角色说明

- `MANIFEST.json` 是最终发布输出，不是 `036_create_final_release_manifest.md` 的必需输入。
- 如果仓库里已有旧 `MANIFEST.json`，执行角色只能把它作为对比参考，不能把它视为权威输入。
