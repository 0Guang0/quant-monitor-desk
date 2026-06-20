# MASTER 计划 — Round 3 Batch 2.5 Layer 1 Observation Ingestion Bridge

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`。Audit 见 `AUDIT.plan.md`（Execute 不读）。  
> **Gate：** 本任务五阶段 Audit PH-A0–PH-A4 全 PASS 后，Batch 3 方可将 Layer 1 标为 real-data-ready（见 §11 handoff）。

---

## 0. 元信息

| 字段                      | 值                                                                       |
| ------------------------- | ------------------------------------------------------------------------ |
| 任务 slug                 | `06-20-round3-batch2-5-layer1-obs-ingest`                                |
| 原计划来源                | `018A_layer1_observation_ingestion_bridge.md`（`R3-B2.5-L1-OBS-INGEST`） |
| 批次索引                  | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3 Batch 2.5、§4.2                  |
| 前置 gate                 | Batch 2 `06-20-round3-batch2-layer1` archived PASS                       |
| Audit 计划                | `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/AUDIT.plan.md`   |
| 分析豁免                  | `analysis_waiver: false`                                                 |
| manifest_protocol_version | `3`                                                                      |
| 默认 ingestion 类型       | **staged/fixture**（非 live production）                                 |

### 0.1 原计划任务

| 字段     | 值                                                                                          |
| -------- | ------------------------------------------------------------------------------------------- |
| Round    | Round 3 Batch 2.5                                                                           |
| 原始任务 | `018A_layer1_observation_ingestion_bridge.md`                                               |
| 上游     | `017`、`018`（Batch 2 archived PASS）                                                       |
| Item IDs | `R3-B2.5-L1-OBS-INGEST`                                                                     |
| 排除     | Batch 3+ 建模、`qmd data` 生产 CLI、全市场/全历史、默认 live QMT/Yahoo、Migration 008 CHECK |

### 0.2 门控速查

- 实现目录：`backend/app/layer1_axes/`、`backend/app/sync/`（窄扩展）、`tests/`、可选 `scripts/`（须批准）— **不得**在 `docs/`/`specs/` 写运行时代码。
- clean `axis_observation` **仅**经 `DataSourceService` 取数 + `DataQualityValidator` + `SourceConflictValidator`（如适用）+ `DbValidationGate` + `DuckDBWriteManager`。
- Layer 1 模块 **禁止** `from backend.app.datasources.adapters import create_adapter`。
- 五阶段 Execute：**Audit 当前阶段 PASS 前不得进入下一阶段**（PH-A0→PH-A4）。
- 默认 **eco**；微窗口单指标单 as_of 日（或最小有效响应）。
- 依赖与验收：`specs/contracts/runtime_versions.md`（`uv sync --locked`）。

### 0.7 GLOBAL 与已拍板决策摘要（inline）

**GLOBAL_EXECUTION_RULES：** 无 drive-by；Primary/Validation/FallbackPolicy；禁止 Shadow/Emergency；禁止 Agent 直写 clean；禁止静默 fallback。

**GLOBAL_TESTING_POLICY：** RED→GREEN；断言 DB 行、route 字段、evidence hash、lineage；禁止仅 `assert called`。

**GLOBAL_RESOURCE_LIMITS：** eco 默认；禁止默认全市场全历史。

**已知对齐 gap（Phase 0 必分类）：** Layer1 指标 `primary_source`（FRED 等）≠ 全部 `source_registry` 已启用源 → 本批默认 **staged fixture** 映射 `macro_supplementary`，不声称 live FRED PASS。

**前置 gate（AC-PRE）：** Batch 1 + Batch 2 + R2.6 gates archived PASS。

### 0.8 项目边界（README 摘要）

- 三层追溯：设计/契约 → 原始任务 → Trellis 冻结计划 → 代码。
- Execute 只读 MASTER + `implement.jsonl`。

### 0.3 Execute 强制必读清单

Phase 0 Boot **必须 Read `implement.jsonl` 每一条**；记录 `execute-evidence/8.0-boot-reads.txt`。先读 `research/integration-ledger.md`。

### 0.4 上下文打包（协议 v3）

Execute 以 MASTER inline 为准；ledger 规定 pointer 原稿 extract/for。**完整 018A §5.1–5.5 路径清单**以 `research/original-plan-trace.md` 为 normative annex；§0.6 为 Execute 高优先级子集。

### 0.5 Execute 开场白

**Phase 0–4 已闭合（2026-06-20）：** 下一会话直接从 §8.6 Final gates 开始；见 `research/execute-handoff.md`。

### 0.9 Execute 进度（会话交接）

| 步                    | 状态     | 日期       | 证据                                                                                   |
| --------------------- | -------- | ---------- | -------------------------------------------------------------------------------------- |
| §8.0 Boot             | **DONE** | 2026-06-20 | `execute-boot.md`, `8.0-*.txt`                                                         |
| §8.1 Phase 0          | **DONE** | 2026-06-20 | `phase0_*`, PH-A0 PASS                                                                 |
| §8.2 Phase 1          | **DONE** | 2026-06-20 | `phase1_before_ingestion_inventory.*`, PH-A1 PASS                                      |
| §8.3 Phase 2          | **DONE** | 2026-06-20 | `phase2_route_preview.*`, `phase2_no_mutation_proof.md`, PH-A2 PASS                    |
| §8.4 Phase 3          | **DONE** | 2026-06-20 | `phase3_micro_fetch_evidence.json`, `phase3_no_clean_write_proof.md`, PH-A3 PASS       |
| §8.5 Phase 4          | **DONE** | 2026-06-20 | `phase4_clean_write_and_snapshot_evidence.json`, PH-A4 PASS（adversarial remediation） |
| §8.6 Final regression | **DONE** | 2026-06-20 | `final_pytest_output.txt`, `final_registry_update.md`, PH-A5 待 Audit                  |

**Handoff 权威文件：** `research/execute-handoff.md`

### 0.10 Post–PH-A3 开放项登记（2026-06-20 对抗性审计后追加 · 勿覆盖 §0.9）

> **目的：** 下一会话进入 §8.5 前必读；下列项 **不阻塞 PH-A3**，但 **禁止静默遗忘**。关闭时在本节追加行（保留历史），并更新 `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md`。

| ID / AC          | 状态         | 关闭阶段                | 说明                                                                                        | 权威引用                                                                                    |
| ---------------- | ------------ | ----------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **AC-TRACE-1**   | **CLOSED**   | §8.5 PH-A4              | 端到端 trace 已闭合                                                                         | `audit-ph-a4-clean-write.md` · `phase4_clean_write_and_snapshot_evidence.json`              |
| **AC-REG-1**     | **CLOSED**   | §8.6                    | `final_registry_update.md` 已产出                                                           | MASTER §8.6 · `AUDIT_DEFERRED_REGISTRY.md`                                                  |
| **AC-HANDOFF-1** | **CLOSED**   | §8.6                    | Batch 3 handoff 字段于 `final_registry_update.md`                                           | MASTER §8.6                                                                                 |
| **B2.5-O-04**    | **CLOSED**   | §8.5                    | `commit_clean_observation_and_snapshots` + `Layer1ObservationWriter` 已实现                 | `test_layer1Observation_cleanWrite_usesWriteManager`                                        |
| **B2.5-O-07**    | **CLOSED**   | audit repair 2026-06-20 | 单条 `fetch_log`：`record_fetch_log=False` + service 唯一写入                               | `base_adapter.py` · `service.py` · `test_layer1MicroIngestion_writesFetchLogAndRawEvidence` |
| **B2.5-O-05**    | **DEFERRED** | 用户授权 live FRED      | 冻结指标 `ENV-E1-DGS10` 使用 staged `macro_supplementary` + fixture                         | `AUDIT_DEFERRED_REGISTRY.md`                                                                |
| **B2.5-O-02**    | **DEFERRED** | §8.6 或窄 PR            | `schema.sql` 滞后 migration 011                                                             | `AUDIT_DEFERRED_REGISTRY.md`                                                                |
| **B2.5-O-03**    | **DEFERRED** | §8.5 / migration 012    | `axis_observation` 无 DB CHECK                                                              | `AUDIT_DEFERRED_REGISTRY.md`                                                                |
| **B2.5-O-06**    | **DEFERRED** | migration 008           | 广义 CHECK（A9-P1-01）                                                                      | `AUDIT_DEFERRED_REGISTRY.md`                                                                |
| **EVID-P3-01**   | **CLOSED**   | —                       | Phase 3 任务证据须 `evidence_baseline_strategy=fresh_phase3_sandbox` + `before_counts` 全零 | `phase3_micro_fetch_evidence.json` · `staged_acceptance_policy.md` §6                       |
| **EVID-P3-02**   | **CLOSED**   | —                       | `8.4-green.txt` 字段须与 `phase3_micro_fetch_evidence.json` 的 `no_clean_write_proof` 一致  | `8.4-green.txt` · 对抗审计 A1-02/B25-A2-01                                                  |
| **A1-08**        | **WAIVED**   | —                       | Phase 1 自动分类 vs operator memo 噪声；operator gate 已闭合，不阻塞 §8.5                   | `adversarial-audit-phase3-remediation.md`                                                   |
| **G-07**         | **WAIVED**   | —                       | 证据 transcript 可用 `.venv` python；MASTER §10 优先 `uv run`                               | `8.2-green.txt` 注释                                                                        |
| **GIT-P3-01**    | **CLOSED**   | audit repair 2026-06-20 | Phase 3–4 代码+证据已入 git baseline                                                        | git status / execute-evidence                                                               |

**对抗审计闭合矩阵：** `research/adversarial-audit-phase4-remediation.md`（Phase 0–4 · 0 开放阻断）。

### 0.6 Source Context Index

| 路径                                                                        | 类型          | 已总结？ | Execute must-read? | 原因                                 |
| --------------------------------------------------------------------------- | ------------- | -------- | ------------------ | ------------------------------------ |
| `018A_layer1_observation_ingestion_bridge.md`                               | original-task | 是 §2/§8 | 否                 | Plan only                            |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2                                   | index         | 是       | 否                 | Plan 已归并                          |
| `MIGRATION_MAP.md`                                                          | map           | 是       | 否                 | omission-check 已做                  |
| `docs/architecture/03_runtime_flows.md`                                     | architecture  | 部分     | **是**             | 摄取主链                             |
| `docs/architecture/04_data_architecture.md`                                 | architecture  | 部分     | **是**             | raw/clean 分区                       |
| `docs/architecture/module_boundary_matrix.md`                               | architecture  | 部分     | **是**             | 禁止 Layer1→adapter                  |
| `docs/modules/layer1_global_regime_panel.md`                                | design        | 部分     | **是**             | observation/snapshot 语义            |
| `docs/modules/datasource_service.md`                                        | design        | 部分     | **是**             | fetch 门面                           |
| `docs/modules/source_route_plan.md`                                         | design        | 部分     | **是**             | Phase 2 dry-run                      |
| `docs/modules/source_capability_registry.md`                                | design        | 部分     | **是**             | capability gate                      |
| `docs/modules/data_sync_orchestrator.md`                                    | design        | 部分     | pointer            | runner 关系                          |
| `docs/modules/data_validation_and_conflict.md`                              | design        | 部分     | **是**             | Phase 4                              |
| `docs/modules/data_sources.md`                                              | design        | 部分     | **是**             | 源角色与 fetch 证据                  |
| `docs/modules/duckdb_and_parquet.md`                                        | design        | 是       | pointer            | clean/staging 分区                   |
| `docs/modules/local_file_system.md`                                         | design        | 是       | pointer            | data root 路径                       |
| `docs/ops/data_sync_quick_reference.md`                                     | ops           | 是       | 否                 | dry-run 摘要 inline                  |
| `docs/ops/data_sync_command_matrix.md`                                      | ops           | 是       | pointer            | Phase 2 dry-run 命令矩阵             |
| `docs/ops/privacy_data_flow.md`                                             | ops           | 是       | 否                 | 本地隐私 inline                      |
| `docs/ops/performance_limits.md`                                            | ops           | 是       | pointer            | §10 eco 上限                         |
| `docs/ops/lock_and_concurrency_policy.md`                                   | ops           | 是       | pointer            | WriteManager 并发                    |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`                      | ADR           | 是       | pointer            | CHECK vs app 分工                    |
| `docs/adr/ADR-0001-use-duckdb-local-first.md`                               | ADR           | 是       | pointer            | 本地优先                             |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                          | ADR           | 是       | pointer            | Layer1 标准化                        |
| `docs/quality/staged_acceptance_policy.md`                                  | rule          | 是       | pointer            | staged 标注                          |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                        | registry      | 部分     | pointer            | AC-REG-1 closeout                    |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                          | registry      | 部分     | pointer            | closeout 对照                        |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                     | index         | 是       | 否                 | Plan trace only                      |
| `docs/modules/write_manager.md`                                             | rule          | 部分     | **是**             | clean write                          |
| `docs/ops/db_inspect_cli.md`                                                | ops           | 部分     | **是**             | Phase 1/4 inspect                    |
| `docs/ops/qmt_xqshare_setup.md`                                             | ops           | 是       | pointer            | live 授权边界                        |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | ADR           | 部分     | **是**             | validation/write 边界                |
| `specs/schema/schema.sql`                                                   | schema        | 过滤     | **是**             | 对照 migration；axis 滞后            |
| `backend/app/db/migrations/011_layer1_tables.sql`                           | migration     | 否       | **是**             | axis_observation DDL                 |
| `specs/contracts/source_route_contract.yaml`                                | contract      | 否       | **是**             | 无静默 fallback                      |
| `specs/contracts/datasource_service_contract.yaml`                          | contract      | 否       | **是**             | factory 边界                         |
| `specs/contracts/write_contract.yaml`                                       | contract      | 否       | **是**             | WriteRequest                         |
| `specs/contracts/snapshot_lineage_contract.yaml`                            | contract      | 否       | **是**             | Phase 4 lineage                      |
| `specs/contracts/data_quality_rules.yaml`                                   | contract      | 否       | **是**             | validator                            |
| `specs/contracts/source_conflict_rules.yaml`                                | contract      | 否       | **是**             | conflict                             |
| `specs/contracts/ops_db_inspect_contract.yaml`                              | contract      | 否       | **是**             | inventory 字段                       |
| `specs/contracts/data_adapter_contract.md`                                  | contract      | 否       | pointer            | FetchResult                          |
| `specs/contracts/data_cli_contract.yaml`                                    | contract      | 否       | pointer            | dry-run                              |
| `specs/contracts/runtime_flow_contract.yaml`                                | contract      | 是       | 否                 | 序列摘要                             |
| `specs/contracts/resource_limits.yaml`                                      | contract      | 否       | **是**             | eco                                  |
| `specs/contracts/source_capability_contract.yaml`                           | contract      | 否       | **是**             | capability gate                      |
| `specs/contracts/platform_source_matrix.yaml`                               | contract      | 否       | pointer            | QMT 可选源                           |
| `specs/datasource_registry/source_registry.yaml`                            | registry      | 否       | **是**             | 源角色                               |
| `specs/datasource_registry/source_capabilities.yaml`                        | registry      | 否       | **是**             | macro_supplementary                  |
| `backend/app/datasources/service.py`                                        | code          | 否       | **是**             | 唯一 factory 路径                    |
| `backend/app/datasources/route_planner.py`                                  | code          | 否       | **是**             | SourceRoutePlan                      |
| `backend/app/sync/pipeline.py`                                              | code          | 否       | **是**             | validate/write 管道（既有；见 §3.4） |
| `backend/app/db/write_manager.py`                                           | code          | 否       | **是**             | clean write                          |
| `backend/app/db/validation_gate.py`                                         | code          | 否       | **是**             | gate                                 |
| `backend/app/core/resource_guard.py`                                        | code          | 否       | **是**             | fetch 前检查                         |
| `backend/app/validators/data_quality.py`                                    | code          | 否       | **是**             | validation_report                    |
| `backend/app/validators/source_conflict.py`                                 | code          | 否       | **是**             | conflict                             |
| `backend/app/layer1_axes/*.py`                                              | code          | 否       | **是**             | Batch 2 引擎                         |
| `backend/app/config.py`                                                     | code          | 否       | pointer            | DATA_ROOT/DB path                    |
| `backend/app/ops/db_inspector.py`                                           | code          | 否       | pointer            | inspect 实现                         |
| `backend/app/db/connection.py`                                              | code          | 否       | pointer            | 只读 DB open                         |
| `backend/app/sync/orchestrator.py`                                          | code          | 否       | pointer            | runner 关系                          |
| `backend/app/sync/runners.py`                                               | code          | 否       | pointer            | 候选窄扩展（O-04）                   |
| `specs/contracts/sync_job_contract.yaml`                                    | contract      | 是       | 否                 | job 语义摘要                         |
| `backend/app/storage/raw_store.py`                                          | code          | 否       | pointer            | Phase 3                              |
| `backend/app/storage/file_registry.py`                                      | code          | 否       | pointer            | Phase 3                              |
| `configs/layer1_axes.yml`                                                   | config        | 否       | **是**             | allowlist 来源                       |
| `GLOBAL_*.md`                                                               | rule          | 是 §0.7  | **是**             | 对照                                 |
| `docs/quality/PENDING_USER_DECISIONS.md`                                    | decision      | 是       | **是**             | D-01..D-12                           |
| `specs/contracts/runtime_versions.md`                                       | rule          | 是       | **是**             | §10                                  |
| Batch 2 `audit.report.md`                                                   | gate          | 是       | pointer            | AC-PRE                               |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                           | registry      | 部分     | pointer            | closeout §8.6                        |

### 0.6.1 过滤指针附录（完整 018A §5 见 `original-plan-trace.md`）

| 路径                                         | 过滤原因                                 |
| -------------------------------------------- | ---------------------------------------- |
| `backend/app/db/migrations/004`–`010`        | 摄取邻域历史；Phase 0 对照 011 即可      |
| `backend/app/datasources/fetch_log.py`       | 经 `service.py` 间接；Phase 3 证据抽检   |
| `backend/app/datasources/route_models.py`    | 经 `route_planner.py` 覆盖               |
| `backend/app/datasources/evidence_ports.py`  | FixtureFetchPort；§4 staged 默认         |
| `backend/app/sync/jobs.py`                   | job 语义；非 Layer1 窄摄取主路径         |
| `backend/app/ops/qmd_ops.py`                 | 可选 CLI 邻域；本批 OUT_OF_SCOPE         |
| `scripts/production_equivalent_smoke.py`     | Tier B 门禁；非摄取核心                  |
| `backend/app/datasources/source_registry.py` | YAML 权威在 `specs/datasource_registry/` |

---

## 1. 目标

### 1.1 一句话目标

交付受控五阶段 Layer 1 `axis_observation` 摄取桥：从 staged/授权源经 DataSourceService 产生 fetch/raw 证据，经 validation/conflict 与 WriteManager 写入 clean observation，并重建 feature/interpretation snapshot 与可审计 lineage。

### 1.2 非目标

- Layer 2+（`019`–`023`）、Batch 6 生产 CLI/backfill、`source_health_snapshot`、Migration 008 CHECK、FastAPI/Agent/frontend。
- 全市场/全历史、默认 live 外部源。

### 1.3 子交付物表（Item ID → AC）

| Item ID                 | MASTER AC                                                                                         | 类型              |
| ----------------------- | ------------------------------------------------------------------------------------------------- | ----------------- |
| `R3-B2.5-L1-OBS-INGEST` | AC-PRE, AC-P0-_, AC-P1-_, AC-P2-_, AC-P3-_, AC-P4-\*, AC-TRACE-1, AC-HANDOFF-1, AC-REG-1, AC-GATE | 五阶段实现 + 证据 |

---

## 2. 预期结果（A5 trace-ac）

| ID           | 预期结果                                                                                                    | 验证链                        |
| ------------ | ----------------------------------------------------------------------------------------------------------- | ----------------------------- |
| AC-PRE       | Batch 1/2 + R2.6 gates PASS；基线 pytest green                                                              | §8.0; archived audits         |
| AC-P0-1      | `phase0_source_context_matrix.md` 覆盖 018A §5.1–5.5                                                        | §8.1 证据                     |
| AC-P0-2      | `phase0_db_contract_gate.md` 分类 schema/migration/契约偏差（含 schema.sql 滞后）                           | §8.1                          |
| AC-P0-3      | Phase 0 指定 pytest 集全绿                                                                                  | §8.1 `phase0_test_output.txt` |
| AC-P0-4      | `layer1_axes` 无 `create_adapter` import                                                                    | §8.1 静态测试                 |
| AC-P1-1      | 只读 DB inspect 产出 `phase1_before_ingestion_inventory.json/.md`（含 sandbox copy source/checksum 若适用） | §8.2                          |
| AC-P1-2      | Phase 1 零 mutation（前后 hash/行数）                                                                       | §8.2; Audit PH-A1             |
| AC-P2-0      | 冻结指标 `ENV-E1-DGS10`：staged 路由 `macro_supplementary.fetch_macro_series`；FRED 声明 **DEFERRED**       | §4, §8.3                      |
| AC-P2-1      | 冻结指标 route preview `READY` 或文档化停止原因                                                             | §8.3                          |
| AC-P2-2      | Phase 2 前后 `axis_observation`/fetch_log 行数不变                                                          | §8.3                          |
| AC-P2-3      | forbidden/blindspot/disabled 源行为符合契约                                                                 | §8.3 pipeline tests           |
| AC-P3-1      | micro-fetch 经 DataSourceService；route 证据先于 fetch                                                      | §8.4                          |
| AC-P3-2      | fetch_log/file_registry 预期 delta；**无** clean observation 写入                                           | §8.4                          |
| AC-P3-3      | ResourceGuard 在 fetch 前检查                                                                               | §8.4                          |
| AC-P4-1      | validation_report 通过；severe conflict/manual review 阻断 clean write                                      | §8.5                          |
| AC-P4-2      | `axis_observation` 经 WriteManager 写入；write_audit_log 可追溯                                             | §8.5                          |
| AC-P4-3      | feature + interpretation snapshot 从 clean observation 重建                                                 | §8.5                          |
| AC-P4-4      | `axis_snapshot_lineage` 含非空 `source_fetch_ids`/`source_content_hashes`（staged 须标注）                  | §8.5                          |
| AC-P4-5      | post-inspect `phase4_inventory_delta.md` 仅预期表变化                                                       | §8.5                          |
| AC-TRACE-1   | 端到端 trace：indicator→route→fetch→evidence→validation→write→snapshots→lineage                             | §8.1–8.5 证据链               |
| AC-HANDOFF-1 | `final_registry_update.md` + Batch 3 handoff 字段（ingestion type/scope/window）                            | §11                           |
| AC-REG-1     | 未闭合项写入 `AUDIT_DEFERRED_REGISTRY` / `UNRESOLVED_ISSUES_REGISTRY`                                       | §8.6                          |
| AC-GATE      | 全量 §9–§10 green                                                                                           | §8.6                          |

---

## 3. 范围与边界

### 3.1 允许修改/创建

- `backend/app/layer1_axes/ingestion_inventory.py`（**新建** — Phase 1 只读 inventory）
- `backend/app/layer1_axes/ingestion.py`（**新建**，首选；§8.3+）
- 可选 `backend/app/layer1_axes/observation_mapper.py`、`observation_writer.py`
- 窄扩展 `backend/app/sync/runners.py`（仅 Layer1 runner hook，须 impact LOW）
- `tests/test_layer1_observation_ingestion.py`、`tests/test_layer1_ingestion_gates.py`
- `tests/fixtures/layer1_macro_observation_fixture.json`
- 可选 `scripts/qmd_layer1_ingest.py`（**HITL 批准前 OUT_OF_SCOPE**；默认 dry-run）
- `execute-evidence/phase*.md|json|txt`

### 3.2 Out of scope · defer

| 项                                 | 批次      | 说明                             |
| ---------------------------------- | --------- | -------------------------------- |
| `019` Layer 2                      | Batch 3   | handoff 后才可标 real-data-ready |
| `R2.6-IMPL-6` / `D2-P1-3` 生产 CLI | Batch 6   | —                                |
| `D2-P2-1` source_health_snapshot   | Batch 6   | —                                |
| live FRED/QMT 默认验证             | —         | 须用户授权证据                   |
| `specs/schema/schema.sql` 全量同步 | 可选窄 PR | Phase 0 须分类，非 silent        |

### 3.3 禁止

- Layer1 import `create_adapter` 或具体 vendor adapter
- 绕过 WriteManager / DataQualityValidator 写 clean observation
- Phase 1/2 任何 DB/raw/clean mutation
- docs/specs 下落 .py

### 3.4 摄取 / 写入边界

```text
indicator allowlist
  → SourceRoutePlan (dry-run / preview)
  → ResourceGuard.check
  → DataSourceService.fetch (staged fixture default)
  → raw_store + fetch_log + file_registry
  → map to axis_observation staging shape
  → DataQualityValidator → validation_report
  → SourceConflictValidator (if applicable)
  → DbValidationGate → DuckDBWriteManager → axis_observation
  → AxisFeatureEngine → AxisInterpretationEngine
  → SnapshotLineageBuilder → axis_snapshot_lineage
```

**接线决策：** `Layer1ObservationIngestionService.commit_*` **直接调用**既有 `DataQualityValidator` / `SourceConflictValidator` / `DbValidationGate` / `DuckDBWriteManager`；**不**经 `SyncValidationPipeline` 全量 job 路径。Execute Phase 0 须在 `phase0_db_contract_gate.md` 记录与 `backend/app/sync/pipeline.py` 的差异及复用边界（只读对照，非 manifest 条目 — E11）。

---

## 4. 代码地图

| 路径                                                   | 操作                                                    |
| ------------------------------------------------------ | ------------------------------------------------------- |
| `backend/app/layer1_axes/ingestion_inventory.py`       | **创建** — Phase 1 read-only inventory + Phase 2 gate   |
| `backend/app/layer1_axes/ingestion.py`                 | **创建** — `Layer1ObservationIngestionService`          |
| `tests/test_layer1_ingestion_gates.py`                 | **创建** — Phase 0 静态/契约 gate                       |
| `tests/test_layer1_observation_ingestion.py`           | **创建** — Phase 2–4 管道语义                           |
| `tests/fixtures/layer1_macro_observation_fixture.json` | **创建** — staged payload                               |
| `backend/app/db/validation_gate.py`                    | **调用** — Phase 4 clean write 前置                     |
| `backend/app/db/connection.py`                         | **只读** — inspect / sandbox                            |
| `backend/app/sync/pipeline.py`                         | **只读对照** — 与 §3.4 接线差异；非 `commit_*` 委托目标 |
| `backend/app/sync/orchestrator.py`                     | **只读** — runner 关系                                  |
| `backend/app/sync/runners.py`                          | **可选窄改** — 仅 Phase 0 证明 runner gap 时启用        |

**接线默认（F-02）：** `ingestion.py` **直接**调用 `DataSourceService` + validators + `DbValidationGate` + `WriteManager`；**不**默认扩展 `runners.py`。若 Phase 0 发现 runner gap，须在 `phase0_db_contract_gate.md` 记录并获 Audit PH-A0 批准后方可窄改。

**设计决策：** 默认 ingestion 类型 = `staged/fixture`。

**冻结摄取指标（AC-P2-0）：** `ENV-E1-DGS10`（environment 轴，`Layer1_State`，非 diagnostic/blindspot/forbidden）

| 字段                  | 值                                                                       |
| --------------------- | ------------------------------------------------------------------------ |
| 声明 `primary_source` | `FRED:DGS10`（与 registry 不对齐 → **DEFERRED**，不声称 live FRED PASS） |
| Staged 路由           | `macro_supplementary.fetch_macro_series`，`series_id=DGS10`              |
| Fixture               | `tests/fixtures/layer1_macro_observation_fixture.json`（Execute 新建）   |
| `as_of`               | fixture 内固定单日（Execute 在 evidence 中文档化）                       |

Phase 2–4 **仅**使用上表指标，除非用户 HITL 授权更换。

---

## 5. 实现切片（§8 顺序 · to-issues）

见 `research/vertical-slices.md`（7 个 AFK 垂直切片 + HITL 门控说明）：

1. **8.0** Slice 1 — Boot
2. **8.1** Slice 2 — Phase 0 gate（A0）
3. **8.2** Slice 3 — Phase 1 inventory（A1）
4. **8.3** Slice 4 — Phase 2 route dry-run（A2）
5. **8.4** Slice 5 — Phase 3 micro-fetch（A3）
6. **8.5** Slice 6 — Phase 4 clean write（A4）
7. **8.6** Slice 7 — Final regression（A5）

测试设计：`research/layer1-ingestion-gate-tests.md`、`research/layer1-ingestion-pipeline-tests.md`。

---

## 6. 接口/契约（示意）

```python
# ingestion.py
class Layer1ObservationIngestionService:
    def preview_routes(self, *, indicators: list[str], as_of: date) -> RoutePreviewResult: ...
    def micro_fetch_staging(self, *, indicator_id: str, as_of: date) -> MicroFetchResult: ...
    def commit_clean_observation_and_snapshots(self, *, indicator_id: str, as_of: date) -> IngestionCommitResult: ...
```

契约锚点：`source_route_contract.yaml`、`datasource_service_contract.yaml`、`write_contract.yaml`、`snapshot_lineage_contract.yaml`、`ops_db_inspect_contract.yaml`。

---

## 7. Red Flags

| Red Flag               | 预防                                                   |
| ---------------------- | ------------------------------------------------------ |
| Layer1 直调 adapter    | AC-P0-4; A3 static                                     |
| Phase 1/2 mutation     | AC-P1-2, AC-P2-2; inspect 对比                         |
| 无 validation 写 clean | AC-P4-1                                                |
| 合成 lineage 冒充生产  | AC-P4-4 标注 staged；复用 Batch 2 A4-09 合成 hash 门控 |
| live 源无授权          | §3.2; Audit A3/A4                                      |
| schema.sql 滞后 silent | AC-P0-2 BLOCKER/DEFERRED                               |
| merge 五阶段           | Audit PH-A0–PH-A4 阻断                                 |

---

## 8. 实现步骤（RED/GREEN）

> **证据命名：** RED 统一 `execute-evidence/8.x-red.txt`；GREEN 用 `phaseN_*` 或 `8.x-green.txt` 二选一，本任务采用 **phase 前缀**（与 018A §11 artifact 名对齐）。

### 8.0 Boot gate

| 字段       | 内容                                                                                                                                                                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 按 **§0.3** 读 `implement.jsonl` 全表 + `research/integration-ledger.md`（v3）；6.pre GitNexus；`uv sync --locked`；基线 pytest                                                         |
| RED 命令   | `uv run python -c "import sys; from pathlib import Path; p=Path('.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/research/execute-boot.md'); sys.exit(0 if p.is_file() else 1)"` |
| GREEN 命令 | 创建 `research/execute-boot.md` + `uv sync --locked` + `uv run pytest -q --co -q`                                                                                                       |
| RED 证据   | `execute-evidence/8.0-red.txt`                                                                                                                                                          |
| GREEN 证据 | `execute-evidence/8.0-boot-reads.txt`, `execute-evidence/8.0-baseline.txt`                                                                                                              |
| Skill      | trellis-execute Phase 0（**artifact-gate RED**，非 pytest）                                                                                                                             |

### 8.1 Execute Phase 0 — DB/contract gate

| 字段       | 内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 以 `research/input-inventory.md` + `original-plan-trace.md` §5 为矩阵模板，产出 `phase0_source_context_matrix.md`（标注 §0.6.1 过滤项）与 `phase0_db_contract_gate.md`（**须含** §3.4 与 `pipeline.py` 差异节）；跑 018A Phase 0 pytest 集；新增 gate 测试                                                                                                                                                                                                                                                        |
| RED 命令   | `uv run pytest tests/test_layer1_ingestion_gates.py -q`（文件/测试不存在则 fail）                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| GREEN 命令 | `uv run pytest tests/test_schema_migration.py tests/test_schema_contract.py tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_cli_contract.py tests/test_ops_db_inspector.py tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py tests/test_layer1_ingestion_gates.py tests/test_write_manager.py tests/test_audit_remediation.py -q` |
| RED 证据   | `execute-evidence/8.1-red.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| GREEN 证据 | `execute-evidence/phase0_test_output.txt`, `execute-evidence/phase0_source_context_matrix.md`, `execute-evidence/phase0_db_contract_gate.md`                                                                                                                                                                                                                                                                                                                                                                      |
| 通过条件   | AC-P0-1..4                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Skill      | test-driven-development, spec-driven-development, GitNexus impact                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 测试设计   | `research/layer1-ingestion-gate-tests.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Audit**  | **PH-A0 PASS 后才能 §8.2**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

**Phase 0 延后登记（对抗审计修补 · 见 `AUDIT_DEFERRED_REGISTRY.md` Batch 2.5 段）：**

| ID        | 项                                               | 关闭阶段              | 证据/测试                                                                   |
| --------- | ------------------------------------------------ | --------------------- | --------------------------------------------------------------------------- |
| B2.5-O-02 | `schema.sql` 缺 7×`axis_*`（migration 011 权威） | §8.6 或窄 PR          | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`                      |
| B2.5-O-03 | `axis_observation` 无 DB CHECK                   | §8.5 / migration 012  | `test_layer1Ingestion_phase0_axisObservation_noDbCheck_classified`          |
| B2.5-O-04 | `ingestion.py` / WriteManager 写 observation     | §8.2–8.5              | `test_layer1Observation_cleanWrite_usesWriteManager`                        |
| B2.5-O-05 | FRED live vs staged `macro_supplementary`        | 用户授权或保持 staged | `test_layer1Ingestion_phase0_frozenIndicator_stagedRouteCapabilityDeclared` |
| B2.5-O-06 | Migration 008 广义 CHECK                         | 既有 A9-P1-01         | `MIGRATION_008_PLAN.md`                                                     |

### 8.2 Execute Phase 1 — read-only inventory

| 字段       | 内容                                                                                                               |
| ---------- | ------------------------------------------------------------------------------------------------------------------ |
| 做什么     | 只读 inspect；`phase1_before_ingestion_inventory.json/.md`；018A §8 Phase 1 关键表行数                             |
| RED 命令   | `uv run pytest tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_phase1_inventory_readOnly -q`      |
| GREEN 命令 | 实现 inventory + 上项测试绿                                                                                        |
| RED 证据   | `execute-evidence/8.2-red.txt`                                                                                     |
| GREEN 证据 | `execute-evidence/phase1_before_ingestion_inventory.json`, `execute-evidence/phase1_before_ingestion_inventory.md` |
| 通过条件   | AC-P1-1, AC-P1-2                                                                                                   |
| Skill      | test-driven-development, testing-guidelines                                                                        |
| 测试设计   | `research/layer1-ingestion-pipeline-tests.md` §Phase 1                                                             |
| **Audit**  | **PH-A1 PASS 后才能 §8.3**                                                                                         |

### 8.3 Execute Phase 2 — route dry-run

| 字段       | 内容                                                                                                                                                                                          |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | allowlist + `phase2_route_preview.json/.md`；无 fetch/write                                                                                                                                   |
| RED 命令   | `uv run pytest tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_routePreview_noMutation tests/test_layer1_observation_ingestion.py::test_layer1Ingestion_noSilentFallback -q` |
| GREEN 命令 | `uv run pytest tests/test_layer1_observation_ingestion.py -k "routePreview or forbidden or blindspot or disabledSource or noSilentFallback" -q`                                               |
| RED 证据   | `execute-evidence/8.3-red.txt`                                                                                                                                                                |
| GREEN 证据 | `execute-evidence/phase2_route_preview.json`, `execute-evidence/phase2_route_preview_matrix.md`, `execute-evidence/phase2_no_mutation_proof.md`                                               |
| 通过条件   | AC-P2-1..3                                                                                                                                                                                    |
| Skill      | test-driven-development, api-and-interface-design                                                                                                                                             |
| 测试设计   | `research/layer1-ingestion-pipeline-tests.md` §Phase 2                                                                                                                                        |
| **Audit**  | **PH-A2 PASS 后才能 §8.4**                                                                                                                                                                    |

### 8.4 Execute Phase 3 — micro-fetch staging

| 字段       | 内容                                                                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | DataSourceService micro-fetch；raw/fetch_log/file_registry；**不写** clean observation                                                            |
| RED 命令   | `uv run pytest tests/test_layer1_observation_ingestion.py::test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation -q`                   |
| GREEN 命令 | `uv run pytest tests/test_layer1_observation_ingestion.py -k MicroIngestion -q`                                                                   |
| RED 证据   | `execute-evidence/8.4-red.txt`                                                                                                                    |
| GREEN 证据 | `execute-evidence/phase3_micro_fetch_evidence.json`, `execute-evidence/phase3_no_clean_write_proof.md`, `execute-evidence/phase3_test_output.txt` |
| 通过条件   | AC-P3-1..3                                                                                                                                        |
| Skill      | test-driven-development, security-and-hardening（live 路径时）                                                                                    |
| 测试设计   | `research/layer1-ingestion-pipeline-tests.md` §Phase 3                                                                                            |
| **Audit**  | **PH-A3 PASS 后才能 §8.5**                                                                                                                        |

**Phase 3 对抗性审计后追加约束（2026-06-20 · 勿删）：**

| 约束         | 说明                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| 证据沙箱     | `capture_task_phase3_evidence` 必须 wipe+recreate `.phase3-micro-fetch-sandbox/`；禁止写项目 `DATA_ROOT` |
| staging 例外 | `file_registry` 仅经 `backend/app/storage/staged_evidence.py`；Phase 4 改 `FileRegistry`+`WriteManager`  |
| 开放登记     | 见 MASTER **§0.10**（AC-TRACE-1、B2.5-O-04、B2.5-O-07 等）                                               |

### 8.5 Execute Phase 4 — clean write + snapshots

| 字段       | 内容                                                                                                                                                                                                                  |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | validation/conflict → WriteManager → observation → snapshots → lineage → post-inspect                                                                                                                                 |
| RED 命令   | `uv run pytest tests/test_layer1_observation_ingestion.py::test_layer1Observation_cleanWrite_usesWriteManager tests/test_layer1_observation_ingestion.py::test_layer1Observation_lineageIncludesFetchIdsAndHashes -q` |
| GREEN 命令 | `uv run pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_layer1_observation_ingestion.py -k Observation -q`                                 |
| RED 证据   | `execute-evidence/8.5-red.txt`                                                                                                                                                                                        |
| GREEN 证据 | `execute-evidence/phase4_clean_write_and_snapshot_evidence.json`, `execute-evidence/phase4_inventory_delta.md`, `execute-evidence/phase4_test_output.txt`                                                             |
| 通过条件   | AC-P4-1..5, AC-TRACE-1                                                                                                                                                                                                |
| Skill      | test-driven-development, incremental-implementation, spec-driven-development                                                                                                                                          |
| 测试设计   | `research/layer1-ingestion-pipeline-tests.md` §Phase 4                                                                                                                                                                |
| **Audit**  | **PH-A4 PASS 后才能 §8.6**                                                                                                                                                                                            |

### 8.6 Final gates + closeout

| 字段       | 内容                                                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| 做什么     | 全量 pytest；registry 更新；handoff 字段                                                                                    |
| RED 命令   | `uv run pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q`（§8.5 前须 fail 项清零） |
| GREEN 命令 | 见 §10 Tier A/B                                                                                                             |
| RED 证据   | `execute-evidence/8.6-red.txt`                                                                                              |
| GREEN 证据 | `execute-evidence/final_pytest_output.txt`, `execute-evidence/final_registry_update.md`                                     |
| 通过条件   | AC-GATE, AC-REG-1, AC-HANDOFF-1                                                                                             |
| Skill      | trellis-execute, incremental-implementation                                                                                 |
| **Audit**  | **PH-A5 跨阶段回归**                                                                                                        |

---

## 9. 四层测试

| 层  | 范围                          | 命令                                                                                               |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------- |
| A   | ingestion gates + pipeline    | `uv run pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q` |
| B   | Phase 0 契约集 + vendor e2e   | 018A §8 Phase 0 命令块                                                                             |
| C   | 全量 pytest + production_gate | `uv run pytest -q`                                                                                 |
| D   | live 源                       | N/A 默认；授权时 Audit 另记                                                                        |

---

## 10. Tier 验收

### Tier A（每步 GREEN 后）

```bash
uv sync --locked
uv run pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py -q
uv run ruff check backend/app/layer1_axes tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py
```

### AC-GATE 子检查清单（映射 018A §9）

| #     | 018A §9 规则                      | 验证                        |
| ----- | --------------------------------- | --------------------------- |
| 1     | 五阶段独立证据 + PH-A0–PH-A4 签字 | §8.1–8.5 证据 + AUDIT §3    |
| 2     | 无未索引来源                      | AC-P0-1 矩阵                |
| 3     | 完整 Source Context Index         | §0.6 + §0.6.1 + trace annex |
| 4     | 完整 Audit Source Trace           | AUDIT §5                    |
| 5     | jsonl 精选非 dump                 | plan-manifest E9            |
| 6     | 摄取范围微小且 staged/授权        | AC-P2-0, §4                 |
| 7     | Route preview 只读                | AC-P2-2                     |
| 8     | SourceRoutePlan 先于 fetch        | AC-P3-1                     |
| 9     | DataSourceService 生产 fetch      | AC-P3-1                     |
| 10    | ResourceGuard 先于 fetch/write    | AC-P3-3, AC-P4-1            |
| 11    | raw/staged 证据先于 clean write   | AC-P3-2, AC-P4-1            |
| 12–13 | validation + WriteManager         | AC-P4-1, AC-P4-2            |
| 14    | snapshot 消费 clean obs           | AC-P4-3                     |
| 15    | lineage 含 fetch ids/hashes       | AC-P4-4                     |
| 16    | inspect 仅预期 delta              | AC-P4-5                     |
| 17    | `pytest -q` 绿                    | §10 Tier B                  |
| 18    | registry closeout                 | AC-REG-1                    |

### Tier B（§8.6）

```bash
uv sync --locked
uv run pytest -q
uv run pytest -q --cov=backend --cov-fail-under=85
uv run ruff check .
uv run ruff format --check .
uv run python scripts/production_gate.py
uv run python scripts/check_doc_links.py
uv run python -m compileall -q backend scripts tests
```

### Tier C

N/A — 无 frontend。

---

## 11. Audit 交接

- 每完成 §8.1–8.5 **必须先** Audit PH-A0–PH-A4 对应阶段 PASS，再进入下一步。
- §8.6 完成后 `validate-execute-handoff`；交接 `AUDIT.plan.md` + `audit.jsonl`。
- Batch 3 handoff 模板（写入 `final_registry_update.md`）：

```text
Layer 1 observation ingestion bridge: PASS|FAIL
Ingestion type: staged | user-authorized live | production live
Allowed downstream use: yes/no
Allowed indicator scope: <list>
Allowed as_of window: <window>
Remaining data limitations: <list>
```

---

## 12. Execute Skill 冻结清单

| Skill                      | 触发            | `@` 指令                   | 本任务 | 绑定 §8                | 已执行      |
| -------------------------- | --------------- | -------------------------- | ------ | ---------------------- | ----------- |
| trellis-execute            | Execute 入口    | trellis-execute            | 必做   | 8.0                    | [x]         |
| test-driven-development    | 每 §8.x RED     | tdd                        | 必做   | 8.1–8.5                | [x] 8.1–8.4 |
| incremental-implementation | 每 GREEN 后     | incremental-implementation | 必做   | 每 GREEN 后全量 pytest | [x] 8.0–8.4 |
| karpathy-guidelines        | RED 后 GREEN 前 | karpathy-guidelines        | 必做   | 8.1–8.5（8.0 exempt）  | [x] 8.1–8.4 |
| testing-guidelines         | 写测试时        | testing-guidelines         | 必做   | 8.1–8.5                | [x] 8.1–8.4 |
| spec-driven-development    | 契约步          | spec-driven-development    | 必做   | 契约步                 | [x] 8.1     |
| gitnexus-impact-analysis   | 改符号前        | gitnexus-impact-analysis   | 必做   | 改符号前 impact        | [x] 8.0     |
| security-and-hardening     | live 授权路径   | security-and-hardening     | 条件   | 8.4 live 授权路径      | [ ]         |

---

## 13. 原计划归并表

| 原始来源                               | MASTER 归并                          | manifest               |
| -------------------------------------- | ------------------------------------ | ---------------------- |
| `018A` §3 trace                        | AC-TRACE-1; §3.4                     | Plan only              |
| `018A` §8 Phase 0–4                    | AC-P0..P4; §8.1–8.5                  | Plan only              |
| `018A` §9–13                           | AC-GATE, AC-REG-1, AC-HANDOFF-1; §11 | 摘要 inline            |
| `017`/`018`                            | 上游依赖；Batch 2 PASS               | pointer archived audit |
| `ROUND3_BATCH_IMPLEMENTATION_MAP` §4.2 | §0.6 Source Context Index            | Plan only              |
| `project-map-omission-check` O-02      | AC-P0-2                              | inline                 |
