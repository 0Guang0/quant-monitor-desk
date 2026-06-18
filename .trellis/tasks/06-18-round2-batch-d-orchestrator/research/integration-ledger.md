# Integration Ledger — round2-batch-d-orchestrator

> Plan 4→5c · 上下文打包地图 · v3

## 打包策略

| 策略 | 含义 |
|------|------|
| inline | 已写入 MASTER；Execute 以 MASTER 为准 |
| summary+pointer | MASTER 摘要 + 原稿对照 |
| pointer | 按 extract 精读原稿 |

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
|--------|----------|----------|---------------|-----------------|-------------|
| `research/integration-ledger.md` | rule | inline | MASTER §0.4 | v3 boot routing map（本文件） | §8.0 Boot |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` | decision | summary+pointer | MASTER §3.2 | §9 defer 台账；GPT-P2-2 tombstone API vs generation 列 | AC-10 / §8.8 |
| `docs/modules/data_sync_orchestrator.md` | business | summary+pointer | MASTER §4.2 | §13.2 happy path；§13.4 job_type 语义；**§13.4.1 resume defer §3.2** | AC-1,2 / §8.2-8.7 |
| `specs/contracts/sync_job_contract.yaml` | contract | summary+pointer | MASTER §6.2 | job_types + statuses 枚举；禁止自造 status | AC-1 / §8.2 |
| `specs/contracts/data_quality_rules.yaml` | contract | pointer | MASTER §6.6 | VALIDATING 阶段规则集（非 data_quality job 混淆） | AC-6 / §8.5 |
| `specs/contracts/source_conflict_rules.yaml` | contract | pointer | MASTER §4 | Reconcile 严重冲突策略 | AC-6 / §8.7 |
| `specs/contracts/data_adapter_contract.md` | contract | pointer | MASTER §6.5 | fetch 须 writer con + job_id | AC-6 / §8.5 |
| `specs/schema/schema.sql` | contract | pointer | MASTER §6.1 | data_sync_job / job_event_log L73-113 列 | AC-7 / §8.1 |
| `docs/architecture/04_data_architecture.md` | architecture | summary+pointer | MASTER §3.1 | clean/staging 分层；禁止直写 clean | AC-8 / §8.5 |
| `docs/architecture/03_runtime_flows.md` | architecture | pointer | MASTER §4 流水线 | ingestion 链路顺序 | AC-6 / §8.5 |
| `docs/architecture/07_project_directory_structure.md` | architecture | pointer | MASTER §3.3 | backend/app 路径归一化 | wiring / §8.3 |
| `docs/modules/data_validation_and_conflict.md` | business | pointer | MASTER §6.5 | validator/gate 模块边界 | AC-6 / §8.5 |
| `docs/modules/data_sources.md` | business | pointer | MASTER §6.5 | fetch_log + registry 权威 | AC-6 / §8.5 |
| `docs/modules/write_manager.md` | business | pointer | MASTER §6.5 | clean 写唯一路径 | AC-8 / §8.5 |
| `docs/modules/duckdb_and_parquet.md` | rule | pointer | MASTER §6.5 | 表/archive 规则 | AC-8 / §8.5 |
| `backend/app/core/resource_guard.py` | wiring | pointer | MASTER §4.4 | Decision→FAILED_RETRYABLE；每 shard FETCHING 前 check | AC-5 / §8.4, §8.6 |
| `backend/app/db/write_manager.py` | wiring | pointer | MASTER §6.5 | 唯一 clean 写；job_id 审计 | AC-8 / §8.5 |
| `backend/app/db/validation_gate.py` | wiring | pointer | MASTER §6.5 | READY_TO_WRITE 门禁 | AC-6 / §8.5 |
| `backend/app/datasources/source_registry.py` | wiring | pointer | MASTER §6.4 | sync_to_db(tombstone_missing=True) | AC-10 / §8.8 |
| `backend/app/datasources/base_adapter.py` | wiring | pointer | MASTER §6.5 | fetch 内 FetchLogWriter | AC-6 / §8.5 |
| `backend/app/datasources/fetch_log.py` | wiring | pointer | MASTER §6.5 | fetch_log 落库触点（勿 orchestrator 重复写） | AC-6 / §8.5 |
| `backend/app/db/connection.py` | wiring | pointer | MASTER §6.5 | ConnectionManager.writer 单写锁 | AC-6 / §8.5 |
| `backend/app/db/migrate.py` | wiring | pointer | MASTER §6.1 | 006 runner 注册 | AC-7 / §8.1 |
| `scripts/init_db.py` | wiring | pointer | MASTER §6.4 | init_db 幂等；**不**默认 sync registry | AC-7 / §8.1 |
| `backend/app/db/migrations/004_ingestion_sources.sql` | rule | pointer | MASTER §6.7 | 禁止 ALTER 004 fetch_log | AC-7 / §8.1 |
| `backend/app/db/migrations/005_ingestion_validation.sql` | rule | pointer | MASTER §6.5 | validation_gate 表（orchestrator 接线） | AC-6 / §8.5 |
| `tests/test_data_adapter_contract.py` | test | pointer | MASTER §6.8 | FakeAdapter 用法（**仅 tests/**） | AC-6 / §8.5 |
| `tests/test_batch_c_validation_flow.py` | test | pointer | MASTER §6.5 | con 传递 E2E 模板 | AC-6 / §8.5 |
| `scripts/production_gate.py` | gate | pointer | MASTER §9.3 | Tier C 门禁命令 | AC-11 / §8.11 |
| `scripts/ci_ingestion_smoke.py` | gate | pointer | MASTER §8.9 | 006 表 + orchestrator_smoke 断言 | AC-9 / §8.9 |

## inline 清单（Execute 以 MASTER 为准）

- §3.2 全部 defer 项（含 FullLoad §13.4.1 断点续跑、014 §11 前端 typecheck N/A）
- §4.2 AC-1/AC-2 **骨架边界**（六种 job_type 可 create；FullLoad/RevisionAudit 无完整 E2E）
- §4.4 ResourceGuard → FAILED_RETRYABLE（非 RESOURCE_GUARD_PAUSED status）；**每个 task/shard 进入 FETCHING 前**
- §6.3 backfill ≤31 天/ task；`trigger_reason` → `job_event_log.payload_json`（无独立列）
- §6.5 staging：**Batch D 仅经 adapter.fetch** 写 staging；orchestrator 不直接 INSERT staging
- §6.6 data_quality job_type ≠ VALIDATING 阶段；fixture 表 `staging_*` 由测试 seed
- §6.8 FakeAdapter import **禁止**出现在 `backend/app/sync/*`
