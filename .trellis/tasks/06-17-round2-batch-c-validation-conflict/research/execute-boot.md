# Execute Boot — 06-17-round2-batch-c-validation-conflict

## AC 摘要（来自 MASTER §2）

- AC-1: migration 005 新增 validation/conflict/manual review 表，不改已应用 004。
- AC-2: DataQualityValidator 读 data_quality_rules.yaml，输出 PASSED/WARNING/FAILED。
- AC-3: 各类规则语义测试（missing/dup PK、required、timestamp、enum、schema drift、stale、insufficient history、high<low、negative price-volume）。
- AC-4: FAILED validation_report `can_write_clean=false`，不写 clean。
- AC-5: SUCCESS 必须有 raw evidence 或 staging table；不存在 staging 不进 clean。
- AC-6: SourceConflictValidator 区分 within tolerance / warning / severe / 口径差异。
- AC-7: severe conflict 写 source_conflict；必要时写 manual_review_queue。
- AC-8: DbValidationGate 用 DB validation_report 放行/拒绝 WriteManager。
- AC-9: PortErrorStatus ↔ FetchStatus 对齐；error_message 脱敏 token/password/api_key/secret/authorization/bearer。
- AC-10: 全库 pytest、ruff、compileall、production_gate、doc links 通过。
- AC-11: 不实现 Orchestrator / API/前端 / Agent sandbox / Release manifest / 真实 vendor Port。

## §8 执行顺序

§8.0 Boot → §8.1 migration 005 → §8.2 DbValidationGate → §8.3 DataQualityValidator pure →
§8.4 DataQualityValidator persistence/evidence/staging → §8.5 SourceConflictValidator pure →
§8.6 SourceConflictValidator persistence/manual review → §8.7 FetchStatus/PortErrorStatus + redaction →
§8.8 end-to-end flow → §8.9 docs → §8.10 final gates + handoff。

## Red Flags（来自 MASTER §13）

- 改已应用 migration 004 而非新增 005。
- 创建 `backend/validation/*` 平行目录（必须用 `backend/app/validators/`）。
- 恢复 WriteManager 默认 stub gate。
- 数据源 adapter import WriteManager。
- validation FAILED 仍写 clean。
- severe conflict 静默降级为 warning。
- 口径差异字段强行合并为单一事实。
- error message 泄漏 token/password/api_key/secret。
- 跳过业务断言以通过测试。
- 实现越界内容（Orchestrator/frontend/Agent/release manifest）。
- 大查询未受 ResourceGuard 约束。
- 生成临时 scratch/tmp/round report 作为最终产物。

## §10 验收命令清单

- Tier A: pytest Batch C 5 文件
- Tier B: pytest 写入/契约/registry/raw_store 回归
- Tier C: pytest -q --cov=backend --cov-fail-under=75；ruff；compileall；production_gate
- Tier D: init_db×2 幂等；ci_ingestion_smoke；ci_validation_smoke（本任务新建）；check_doc_links

## 关键发现（影响实现设计）

1. **migration 005 表是新表**：001–004 未创建 `validation_report`/`data_quality_log`/`source_conflict`/`manual_review_queue`（仅 spec schema.sql 含定义）。005 可直接 CREATE TABLE + CHECK 约束（对新表 DuckDB 支持 inline CHECK）。
2. **fetch_log/source_registry 已在 004 建表**：DuckDB 不支持对已存在表安全 ALTER ADD CHECK。回退策略 = 应用层守护（FetchResult + FetchLogWriter._validate_for_persist 已存在）+ 注释说明 + BATCH_C_REPAIR_STATUS 记录。
3. **StubValidationGate 仅测试用**：DbValidationGate 读取 DB validation_report 行做放行/拒绝决策。
4. **WriteManager 不变**：只需注入 DbValidationGate；测试经 create_test_write_manager 用 stub。

## Baseline 结果（2026-06-18）

- pytest -q → 245 passed, exit 0（见 8.0-baseline-pytest.txt）
- ruff check . → All checks passed, exit 0
- compileall -q backend scripts tests → exit 0
- production_gate.py → PASS, exit 0

## Phase 0 complete
