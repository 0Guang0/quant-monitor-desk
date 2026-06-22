# R3X_db_write_validation_blockers — DB / WriteManager / ValidationGate blocker 修复任务

## 1. 任务性质

本任务是最小修复任务，目标是解除真实数据 staged pilot 与后续 clean write gate 前的 DB、写入、校验、冲突、审计链路 blocker。

本任务不是 production DB 数据回填任务，不做真实数据 fetch，不执行生产 clean write，不证明 production-live readiness。

## 2. 分支与工作方式

- 建议分支：`fix/round3-db-write-validation-blockers`
- 基准分支：用户指定的最新 `master` 或 `integration/round3`
- 目标合并：`integration/round3`
- 工作方式：先 RED tests，再最小修复，再定向 gate

## 3. 背景与目的

真实数据 staged pilot 会暴露 schema、quality、conflict、audit 与 write gate 问题。进入 pilot 前，必须确保：

1. clean table 写入仍只能通过 WriteManager。
2. ValidationGate 完整执行 `write_contract.yaml` 的拒绝条件。
3. severe conflict 必须阻断 clean write。
4. audit evidence 在失败、rollback、异常路径仍可追踪。
5. staged evidence / file registry 不得出现路径逃逸或绕过写入协议。
6. backfill 与 incremental 路径执行同等级别的 validation / conflict gate。

## 4. 优先修复范围

必须优先核实并处理以下问题；如果某项已由其他分支修复，必须记录证据而不是重复修改。

### 4.1 HIGH / blocker

- `DbValidationGate` 未执行 `schema_hash_changed == true and schema_change_approved != true` 的拒绝条件。
- `staged_evidence.py` 绕过 WriteManager 直接 INSERT `file_registry`，并且未验证 raw/staged path 是否位于允许 data root / sandbox root 下。
- `WriteManager` 在 `own_transaction=False` 且外部 rollback 时可能丢失 FAILED audit evidence。
- `BackfillShardRunner` 获取 conflict report 后未检查 `SEVERE_CONFLICT`，可能继续 clean write。
- Backfill 路径未持久化 `conflict_report_id` 到 `data_sync_job`，审计链路断裂。

### 4.2 MEDIUM / pilot blocker candidate

- validation / conflict 范围按 run_id 过宽或 job_id 过窄时是否符合 contract。
- staging row count verification 是否缺失。
- `CONTENT_CHANGED` / `SCHEMA_DRIFT` 规则是否只是 contract 字段而无 runtime path。
- ResourceGuard 与 write locks / transaction 的交互是否会导致锁泄漏或嵌套事务风险。

## 5. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据项目地图、contract authority、migration references、import/call graph、测试失败信息继续追溯相关文件。

### 5.1 协议与项目地图

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

### 5.2 DB / write / validation / conflict 设计与契约

- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/data_sync_orchestrator.md` if present
- `docs/modules/local_file_system.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/runtime_versions.md`

### 5.3 Schema / migration / implementation / tests

- `docs/schema/`
- schema migration files directory if present
- `backend/app/db/`
- `backend/app/storage/`
- `backend/app/sync/`
- `backend/app/validation/` if present
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/live_pilot.py`
- `tests/test_db_validation_gate.py`
- `tests/test_write_manager.py`
- `tests/test_sync_orchestrator.py`
- `tests/test_sync_jobs.py`
- `tests/test_raw_store.py`
- `tests/test_ops_db_inspector.py`
- `tests/test_schema_contract.py`
- `tests/test_schema_migration.py`

### 5.4 最新审计材料

如果存在，必须读取：

- `docs/quality/adversarial_audit_report.md`
- 相关 `.trellis/tasks/**/execute-evidence/*mutation*`
- 相关 `.trellis/tasks/**/execute-evidence/*validation*`
- 相关 `.trellis/tasks/**/execute-evidence/*gate*`

### 5.5 当前批次完成物与审计检查

用户已确认当前批次四个分支已经完成。执行者必须纳入这些完成物中与 DB、write gate、validation gate、snapshot lineage、evidence identity、no-mutation proof 相关的检查结果。

必须追溯：

- `feature/round3-019-layer2-sensor`：snapshot write/staging path、ResourceGuard、WriteManager、no-future-data、lineage fields。
- `feature/round3-023a-evidence-foundation`：evidence identity、source fetch/content hashes、manual-review flags、Agent text not fact source。
- `review/round3-019-plan-audit`：关于 WriteManager / ResourceGuard / DB mutation / lineage 的 PASS/BLOCK/WARN。
- `debt/r3b275-018c-live-manual-probe-plan`：no-mutation proof 方法、sandbox path、authorization checklist、DB write prohibition。
- integration/coordinator artifacts：若存在 merge report、post-merge gate 或当前批次审计报告，必须读取；若不可见，记录 `MISSING_CURRENT_BATCH_EVIDENCE`。

## 6. 允许修改范围

只在计划明确后修改最小必要文件。候选范围：

- `backend/app/db/validation_gate.py`
- `backend/app/db/write_manager.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/storage/raw_store.py` only if path root validation requires it
- `backend/app/sync/`
- `specs/contracts/write_contract.yaml` only if implementation reveals contract ambiguity
- `specs/contracts/data_quality_rules.yaml` only if machine contract is missing required rule metadata
- `tests/test_db_validation_gate.py`
- `tests/test_write_manager.py`
- `tests/test_sync_orchestrator.py`
- `tests/test_sync_jobs.py`
- `tests/test_raw_store.py`
- task-local Trellis plan/evidence files

## 7. 禁止事项

禁止：

- 写 production DB
- 运行 production migration
- 做真实 source fetch
- 启用 production clean write
- 为了通过测试删除 gate 或放宽 gate
- 绕过 WriteManager 修复 staged/file registry
- 把 validation-only source 写入 clean table
- 改动与 DB/write/validation blocker 无关的大范围代码
- 将本任务扩大为 data-health CLI 完整实现
- 声称 production-live readiness

## 8. 修复规则

1. 先写或补 RED tests，证明当前 blocker。
2. ValidationGate 必须完整覆盖 `write_contract.yaml` 的拒绝条件。
3. schema drift / schema hash 相关行为必须有明确 report 来源；如果当前 schema 无字段，必须选择安全拒绝、contract amend 或 explicit deferred，不得静默忽略。
4. clean write path 必须保留 WriteManager 权威地位。
5. staged evidence 或 file registry 写入必须验证 path containment 与 raw/staging/sandbox boundary。
6. backfill / incremental / reconcile 等所有写入路径必须遵循同级 validation/conflict gate。
7. FAILED audit evidence 必须在 rollback/exception 场景可追踪；若无法落 DB，必须有独立 append-only evidence path 或明确 contract。
8. no-mutation proof 必须能区分 schema-only / row-count unchanged / hash unchanged。

## 9. 验证命令

最低命令：

```bash
pytest tests/test_db_validation_gate.py -q
pytest tests/test_write_manager.py -q
pytest tests/test_sync_orchestrator.py -q
pytest tests/test_sync_jobs.py -q
pytest tests/test_raw_store.py -q
pytest tests/test_ops_db_inspector.py -q
```

若改动 schema/migration 契约：

```bash
pytest tests/test_schema_contract.py -q
pytest tests/test_schema_migration.py -q
```

若改动 docs/specs 链接：

```bash
python scripts/check_doc_links.py
```

## 10. 完成标准

- ValidationGate 完整覆盖 write contract 拒绝条件或记录明确 deferred
- backfill severe conflict 不能 clean write
- conflict_report_id 可从 backfill job 追溯
- staged evidence / file registry 不允许路径逃逸
- FAILED audit evidence 在失败路径可追踪
- 没有 production DB mutation
- 合并报告列出改动文件、测试结果、仍 deferred 的 DB/data-health 问题
