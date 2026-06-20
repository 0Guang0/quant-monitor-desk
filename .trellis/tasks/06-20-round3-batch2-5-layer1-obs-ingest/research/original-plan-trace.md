# Original Plan Trace — 06-20-round3-batch2-5-layer1-obs-ingest

## Round / Batch

- **Round:** 3 — Modeling Layers
- **Batch:** 2.5 — Layer 1 observation ingestion bridge
- **Local alias:** `R3-B2.5-L1-OBS-INGEST`
- **权威批次索引:** `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2.5、§4.2

## 任务卡清单（NNN / alias → 路径）

| ID                      | 路径                                                                                                | 类型                        |
| ----------------------- | --------------------------------------------------------------------------------------------------- | --------------------------- |
| `R3-B2.5-L1-OBS-INGEST` | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`     | 本批唯一正式 alias 执行文件 |
| `017`（上游）           | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`             | Batch 2 依赖                |
| `018`（上游）           | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md` | Batch 2 依赖                |

## AC 映射（任务卡预期结果 → MASTER §2）

| 018A 预期                                                    | MASTER AC                            |
| ------------------------------------------------------------ | ------------------------------------ |
| §3 端到端 trace                                              | AC-TRACE-1                           |
| §8 Phase 0：契约/DB gate + 指定 pytest 全绿                  | AC-P0-1..4                           |
| §8 Phase 1：只读 inventory 证据                              | AC-P1-1..2                           |
| §8 Phase 2：route preview 无 mutation                        | AC-P2-0..3                           |
| §8 Phase 3：micro-fetch 无 clean write                       | AC-P3-1..3                           |
| §8 Phase 4：clean write + snapshots + lineage + post-inspect | AC-P4-1..5                           |
| §9 整批 pass/fail 18 条                                      | AC-GATE（§10 Tier A/B 子检查清单）   |
| §10 阶段审计 artifact                                        | AUDIT PH-A0–PH-A5（非 MASTER AC ID） |
| §12 registry closeout                                        | AC-REG-1                             |
| §13 Batch 3 handoff 字段                                     | AC-HANDOFF-1                         |
| BATCH_MAP：五阶段 gate + 逐阶段 audit                        | MASTER §8 Audit 列 + AUDIT §2.1      |

## 输入文件已读（specs / architecture / wiring）

### 5.1 根与协议（018A §5.1）

| 路径                                                     | 类别             | manifest                      |
| -------------------------------------------------------- | ---------------- | ----------------------------- |
| `README.md`                                              | root boundary    | 可总结                        |
| `MIGRATION_MAP.md`                                       | project map      | Plan + omission-check         |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                     | batch map        | Plan only                     |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`  | context bridge   | Plan only                     |
| `.trellis/spec/guides/complex-task-planning-protocol.md` | Trellis protocol | Plan only                     |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`    | rule             | 可总结 → MASTER               |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`     | rule             | 可总结 → MASTER/AUDIT         |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`    | rule             | 可总结 → MASTER §10           |
| `docs/quality/staged_acceptance_policy.md`               | rule             | 可总结                        |
| `docs/quality/PENDING_USER_DECISIONS.md`                 | user decisions   | 可总结（禁止重开 D-01..D-12） |

### 5.2 架构与模块（018A §5.2）

| 路径                                                                        | 类别         | manifest                                         |
| --------------------------------------------------------------------------- | ------------ | ------------------------------------------------ |
| `docs/architecture/03_runtime_flows.md`                                     | architecture | **Execute must-read**（摄取主链）                |
| `docs/architecture/04_data_architecture.md`                                 | architecture | **Execute must-read**（raw/clean 分区）          |
| `docs/architecture/module_boundary_matrix.md`                               | architecture | **Execute must-read**（Layer1 不得直调 adapter） |
| `docs/modules/layer1_global_regime_panel.md`                                | module       | **Execute must-read**                            |
| `docs/modules/data_sources.md`                                              | module       | **Execute must-read**                            |
| `docs/modules/source_capability_registry.md`                                | module       | Execute must-read（Phase 2+）                    |
| `docs/modules/source_route_plan.md`                                         | module       | Execute must-read                                |
| `docs/modules/datasource_service.md`                                        | module       | **Execute must-read**                            |
| `docs/modules/data_sync_orchestrator.md`                                    | module       | Execute must-read                                |
| `docs/modules/data_validation_and_conflict.md`                              | module       | Execute must-read                                |
| `docs/modules/write_manager.md`                                             | module       | **Execute must-read**                            |
| `docs/modules/duckdb_and_parquet.md`                                        | module       | 可总结 + pointer                                 |
| `docs/modules/local_file_system.md`                                         | module       | 可总结                                           |
| `docs/ops/data_sync_quick_reference.md`                                     | ops          | 可总结                                           |
| `docs/ops/data_sync_command_matrix.md`                                      | ops          | 可总结                                           |
| `docs/ops/db_inspect_cli.md`                                                | ops          | **Execute must-read**（Phase 1/4 inspect）       |
| `docs/ops/qmt_xqshare_setup.md`                                             | ops          | pointer（授权边界）                              |
| `docs/ops/privacy_data_flow.md`                                             | ops          | 可总结                                           |
| `docs/ops/performance_limits.md`                                            | ops          | 可总结 → §10                                     |
| `docs/ops/lock_and_concurrency_policy.md`                                   | ops          | 可总结                                           |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | ADR          | **Execute must-read**                            |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`                      | ADR          | 可总结                                           |
| `docs/adr/ADR-0001-use-duckdb-local-first.md`                               | ADR          | 可总结                                           |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                          | ADR          | 可总结                                           |

### 5.3 契约 / schema / registry（018A §5.3）

| 路径                                                       | 类别            | manifest                                |
| ---------------------------------------------------------- | --------------- | --------------------------------------- |
| `specs/schema/schema.sql`                                  | schema contract | **Execute must-read**（对照 migration） |
| `backend/app/db/migrations/004_ingestion_sources.sql`      | migration       | pointer                                 |
| `backend/app/db/migrations/005_ingestion_validation.sql`   | migration       | pointer                                 |
| `backend/app/db/migrations/006_ingestion_sync.sql`         | migration       | pointer                                 |
| `backend/app/db/migrations/008_lineage_version_fields.sql` | migration       | pointer                                 |
| `backend/app/db/migrations/010_lineage_not_null.sql`       | migration       | pointer                                 |
| `backend/app/db/migrations/011_layer1_tables.sql`          | migration       | **Execute must-read**                   |
| `specs/datasource_registry/source_registry.yaml`           | registry        | Execute must-read                       |
| `specs/datasource_registry/source_capabilities.yaml`       | registry        | Execute must-read                       |
| `specs/contracts/source_capability_contract.yaml`          | contract        | Execute must-read                       |
| `specs/contracts/source_route_contract.yaml`               | contract        | **Execute must-read**                   |
| `specs/contracts/datasource_service_contract.yaml`         | contract        | **Execute must-read**                   |
| `specs/contracts/data_adapter_contract.md`                 | contract        | Execute must-read                       |
| `specs/contracts/data_cli_contract.yaml`                   | contract        | Execute must-read                       |
| `specs/contracts/data_quality_rules.yaml`                  | contract        | Execute must-read                       |
| `specs/contracts/source_conflict_rules.yaml`               | contract        | Execute must-read                       |
| `specs/contracts/write_contract.yaml`                      | contract        | **Execute must-read**                   |
| `specs/contracts/snapshot_lineage_contract.yaml`           | contract        | **Execute must-read**                   |
| `specs/contracts/runtime_flow_contract.yaml`               | contract        | 可总结                                  |
| `specs/contracts/resource_limits.yaml`                     | contract        | 可总结 → §10                            |
| `specs/contracts/ops_db_inspect_contract.yaml`             | contract        | Execute must-read                       |
| `specs/contracts/platform_source_matrix.yaml`              | contract        | pointer                                 |
| `specs/contracts/reference_adoption_guardrails.yaml`       | contract        | filtered-out（本批不引入外部参考）      |

### 5.4 原始任务与 registry（018A §5.4）

| 路径                                             | 类别       | manifest                |
| ------------------------------------------------ | ---------- | ----------------------- |
| Round 2 `011`–`016` 任务卡                       | 历史任务   | Plan only（边界追溯）   |
| Round 2.6 `016A`–`016F`                          | 设计任务   | Plan only               |
| `ROUND2_GAPS_AND_DEVIATIONS.md`                  | gap ledger | 可总结                  |
| `ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` | decisions  | pointer                 |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                | registry   | Plan + closeout pointer |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`             | registry   | Plan                    |
| `docs/RESOLVED_ISSUES_REGISTRY.md`               | registry   | Plan                    |

### 5.5 代码参考（018A §5.5 — Plan 已 spot-check）

| 路径                                         | 类别         | manifest                                         |
| -------------------------------------------- | ------------ | ------------------------------------------------ |
| `backend/app/config.py`                      | wiring       | pointer                                          |
| `backend/app/db/connection.py`               | wiring       | Execute must-read                                |
| `backend/app/db/write_manager.py`            | wiring       | **Execute must-read**                            |
| `backend/app/db/validation_gate.py`          | wiring       | Execute must-read                                |
| `backend/app/core/resource_guard.py`         | wiring       | Execute must-read                                |
| `backend/app/storage/raw_store.py`           | wiring       | Phase 3 pointer                                  |
| `backend/app/storage/file_registry.py`       | wiring       | Phase 3 pointer                                  |
| `backend/app/datasources/service.py`         | wiring       | **Execute must-read**（`create_adapter` 仅此处） |
| `backend/app/datasources/route_planner.py`   | wiring       | Execute must-read                                |
| `backend/app/sync/orchestrator.py`           | wiring       | pointer                                          |
| `backend/app/sync/pipeline.py`               | wiring       | Execute must-read                                |
| `backend/app/validators/data_quality.py`     | wiring       | Execute must-read                                |
| `backend/app/validators/source_conflict.py`  | wiring       | Execute must-read                                |
| `backend/app/layer1_axes/*.py`               | wiring       | **Execute must-read**（Batch 2 产出）            |
| `backend/app/ops/db_inspector.py`            | wiring       | **Execute must-read**                            |
| `scripts/qmd_ops.py`                         | ops script   | pointer（inspect only）                          |
| `scripts/init_db.py`                         | ops script   | pointer                                          |
| `backend/app/layer1_axes/ingestion.py`       | Execute 新建 | deferred → §8                                    |
| `tests/test_layer1_observation_ingestion.py` | Execute 新建 | deferred                                         |

## 路径纠偏

| 声明                                    | 实际                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| `specs/schema/schema.sql` 含 Layer 1 表 | **无** `axis_*` DDL — 以 migration `011` + `layer1_global_regime_panel.md` 为准 |
| Layer 1 生产 fetch                      | Batch 2 未实现；本批新增窄桥，不得从 `layer1_axes` import `create_adapter`      |

## 已过滤 / 本批排除

| 来源                               | 原因                       |
| ---------------------------------- | -------------------------- |
| Batch 3 `019`–Batch 5 `023`        | 下游建模                   |
| Batch 6 CLI/backfill/migration 008 | 018A §4 非目标             |
| QMT/Yahoo/live 默认启用            | 须用户逐阶段授权           |
| `source_health_snapshot`           | `D2-P2-1` deferred Batch 6 |
| FastAPI / Agent / frontend         | Round 4                    |
