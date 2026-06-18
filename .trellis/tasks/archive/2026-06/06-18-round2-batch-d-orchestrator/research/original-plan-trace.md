# Original Plan Trace — round2-batch-d-orchestrator

## Round / Batch

- **Round:** `ROUND_2_DATA_INGESTION_VALIDATION`
- **Batch:** **D**（四批次最后一批）
- **Trellis slug:** `06-18-round2-batch-d-orchestrator`
- **前置：** Batch A/B/C 已完成；Batch C `finish.md` 声明 `READY_FOR_BATCH_D: yes`

## 任务卡清单（NNN → 路径）

| NNN | 路径 | Batch |
|-----|------|-------|
| 014 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md` | D |

## AC 映射（任务卡预期结果 → MASTER §2）

| 任务卡预期 | MASTER AC |
|-----------|-----------|
| FullLoad / Incremental / Backfill / RevisionAudit / Reconcile / **data_quality** 状态机 | AC-1, AC-2 |
| job_id / run_id / task_id 与 job_event_log | AC-4 |
| 重任务先过 ResourceGuard | AC-5 |
| Adapter fetch → staging → Validator → Gate → WriteManager 编排 | AC-6 |
| data_sync_job / job_event_log 表落库 | AC-7 |
| 不直接写 clean、不绕过 WriteManager | AC-8 |
| Round 2 ingestion smoke（DECISIONS §9 GPT-P3-6） | AC-9 |
| registry sync / init_db 钩子（DECISIONS §9 GPT-init_db） | AC-10 |
| pytest / ruff / compileall 验收 | AC-11 |
| 不实现 Layer 建模 / 前端 / Agent / 真实 vendor Port | AC-12 |

## 输入文件已读（specs / architecture）

> **manifest 列：** `required` = 必须列入 implement.jsonl；`inherited` = 来自前置 Batch；`deferred` = 明确延后（MASTER §3.2）

| 路径 | 类别 | manifest |
|------|------|----------|
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md` | 全局规则 | required |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | 全局规则 | required |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | 全局规则 | required |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` | 全局规则 | required |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md` | Round README | required |
| `.trellis/tasks/06-18-round2-batch-d-orchestrator/research/integration-ledger.md` | v3 打包地图 | required |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` | 决策 | required |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md` | 台账 | required |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_REPAIR_STATUS.md` | 台账 | required |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md` | 台账 | required |
| `docs/modules/data_sync_orchestrator.md` | 模块规格 | required |
| `docs/modules/data_validation_and_conflict.md` | Batch C 模块 | required |
| `docs/modules/data_sources.md` | 数据源模块 | required |
| `docs/modules/write_manager.md` | 写入模块 | required |
| `docs/modules/duckdb_and_parquet.md` | 模块引用 1-hop | required |
| `specs/contracts/sync_job_contract.yaml` | 契约 | required |
| `specs/contracts/data_adapter_contract.md` | Adapter 契约 | required |
| `specs/contracts/data_quality_rules.yaml` | 质量规则 | required |
| `specs/contracts/source_conflict_rules.yaml` | 冲突规则 | required |
| `specs/datasource_registry/source_registry.yaml` | Registry YAML | required |
| `specs/schema/schema.sql` | Schema 权威 | required |
| `docs/architecture/03_runtime_flows.md` | 运行时链路 | required |
| `docs/architecture/04_data_architecture.md` | 数据架构 | required |
| `docs/architecture/07_project_directory_structure.md` | 路径归一化 | required |
| `docs/quality/final_package_rules.md` | 最终包规则 | required |
| `scripts/ci_ingestion_smoke.py` | Smoke 基线 | required |
| `scripts/production_gate.py` | Tier C 门禁 | required |
| `scripts/check_doc_links.py` | Tier C 门禁 | required |
| `backend/app/datasources/source_registry.py` | Registry API | required |
| `backend/app/datasources/adapters/__init__.py` | Adapter 工厂 | inherited |
| `backend/app/datasources/base_adapter.py` | fetch 内 fetch_log | inherited |
| `backend/app/datasources/fetch_log.py` | Fetch 审计 | inherited |
| `backend/app/datasources/fetch_result.py` | Fetch 契约 | inherited |
| `backend/app/datasources/adapters/fetch_port.py` | Port 错误 | inherited |
| `backend/app/db/connection.py` | Writer 锁 | inherited |
| `backend/app/db/migrate.py` | Migration runner | required |
| `scripts/init_db.py` | init_db | required |
| `backend/app/db/migrations/004_ingestion_sources.sql` | 只读不可 ALTER | required |
| `backend/app/db/migrations/005_ingestion_validation.sql` | validation 表 | required |
| `backend/app/db/validation_gate.py` | Gate | inherited |
| `backend/app/db/write_manager.py` | Write 路径 | inherited |
| `backend/app/validators/data_quality.py` | Validator | inherited |
| `backend/app/validators/source_conflict.py` | Validator | inherited |
| `backend/app/core/resource_guard.py` | ResourceGuard | required |
| `backend/app/config.py` | DATA_ROOT | required |
| `backend/app/util/error_redaction.py` | 脱敏 | required |
| `tests/test_batch_c_validation_flow.py` | E2E 模板 | inherited |
| `tests/test_data_adapter_contract.py` | FakeAdapter | inherited |
| `tests/test_write_manager.py` | §9.2 回归 | required |
| `tests/test_source_registry.py` | §9.2 回归 | required |
| `tests/test_resource_guard.py` | §8.4 | required |
| `tests/test_db_validation_gate.py` | Gate 基线 | inherited |
| `tests/test_data_quality_validator.py` | Validator 基线 | inherited |
| `tests/test_source_conflict_validator.py` | Reconcile 基线 | inherited |
| `tests/conftest.py` | Fixtures | required |
| `.trellis/tasks/06-17-round2-batch-c-validation-conflict/finish.md` | Handoff | required |
| `scripts/sync_registry.py` | §8.8 新建 | deferred |
| `backend/app/sync/orchestrator.py` | §8.3 新建 | deferred |
| Layer 1–5 契约 YAML | Round 3 | deferred |

## 路径纠偏

| 任务卡字面量 | 实际仓库路径 | 处理 |
|-------------|-------------|------|
| `backend/sync/orchestrator.py` | `backend/app/sync/orchestrator.py` | DECISIONS §1 归一化 `backend/app/*` |
| `backend/sync/jobs.py` | `backend/app/sync/jobs.py` | 同上 |
| `tests/test_sync_orchestrator.py` | `tests/test_sync_orchestrator.py` | 保持不变 |
| `plans/014_*.plan.md` | **不存在** | MASTER §8 为唯一 Execute 全文；可选索引 `plans/014_batch_d.plan.md` |

## DECISIONS §9 延后台账归并（进入 Batch D）

| ID | 内容 | MASTER 切片 |
|----|------|-------------|
| GPT-init_db | init_db 不 sync registry | §8.8 |
| GPT-P3-6 | ResourceGuard + ingestion smoke | §8.9 |
| GPT-P2-2 | YAML 缺失源 disabled（`sync_to_db(tombstone_missing=True)` 已存在） | §8.8（调用 API + 测试；`registry_generation` 列 defer） |
| B-P1-6-full | fetch 前 ResourceGuard | §8.4 |
| C-C2 | fetch_log 004 DB CHECK | 文档化 + app 层（不可 ALTER 004） |

**仍延后（本批不做）：** GPT-SEC-CI 全量、真实 vendor Port、Layer 建模、API/前端生产化。
