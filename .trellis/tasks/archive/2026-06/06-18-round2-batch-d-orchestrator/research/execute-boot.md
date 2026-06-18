# Execute Boot — round2-batch-d-orchestrator

## AC 摘要（来自 MASTER §2）

| AC | 要点 |
|----|------|
| AC-1 | 六种 job_type 可 create_job；状态转移符合 sync_job_contract.yaml |
| AC-2 | 六种 job 各有语义测试；FullLoad/RevisionAudit 仅骨架无完整 E2E |
| AC-3 | Backfill eco 分片 ≤31 天/task |
| AC-4 | data_sync_job + job_event_log 持久化 run/job/task id |
| AC-5 | FETCHING 前 ResourceGuard.check；PAUSE→FAILED_RETRYABLE + RESOURCE_GUARD_PAUSED in message |
| AC-6 | Incremental E2E: adapter→staging→validators→gate→WriteManager |
| AC-7 | migration 006 对齐 schema.sql L73–113 |
| AC-8 | Orchestrator 不直写 clean；不经 WriteManager 不写 clean |
| AC-9 | ci_ingestion_smoke 覆盖 orchestrator 路径 |
| AC-10 | sync_registry.py / bootstrap sync YAML→DB |
| AC-11 | 全库 pytest、ruff、compileall、production_gate |
| AC-12 | 不实现 Layer/API/Agent/vendor Port/全量 security CI |

## §8 执行顺序

```
§8.0 Boot（本阶段）→ §8.1 migration 006 → §8.2 jobs → §8.3 orchestrator core
→ §8.4 ResourceGuard → §8.5 incremental E2E → §8.6 backfill
→ §8.7 reconcile → §8.8 registry → §8.9 smoke → §8.10 docs → §8.11 handoff
```

执行模式：**inline** 主会话（MASTER §12 标 inline；不派发 trellis-implement）。

## Red Flags（来自 MASTER §7）

- Orchestrator 内直接 INSERT clean 表
- 新增 ad-hoc job status 不在契约 YAML
- 跳过 ResourceGuard 声称「测试简化」
- 重复实现 reconcile 逻辑
- 创建 `backend/sync/` 平行树
- 为绿而删 validator/gate 调用
- adapter.fetch 不传 writer con
- 把 RESOURCE_GUARD_PAUSED 当作 data_sync_job.status

## §10 验收命令清单

| Tier | 命令 |
|------|------|
| A | `pytest tests/test_sync_migration.py tests/test_sync_jobs.py tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py -q` |
| B | `pytest tests/test_batch_c_validation_flow.py tests/test_source_registry.py tests/test_write_manager.py tests/test_data_adapter_contract.py -q` |
| C | `pytest -q --cov=backend --cov-fail-under=75` + ruff + compileall + production_gate + check_doc_links + ci_ingestion_smoke |

## Boot 完成项

- [x] Read `research/integration-ledger.md`（v3 inline/pointer 路由）
- [x] Read `implement.jsonl` **全部 68 条**（含 MASTER + trellis-execute）；pointer 项按 extract/for 精读；记录于 `research/execute-evidence/8.0-boot-reads.txt`（66 条非 MASTER/skill 路径）
- [x] 6.pre GitNexus query + impact(upstream) + detect_changes → `gitnexus-execute-summary.md` + `context-closure.md`
- [x] Read trellis-execute SKILL + execute-skill-paths.yaml Boot 段
- [x] 创建 `execute-evidence/` 目录
- [x] §8.0 baseline 已记录 `execute-evidence/8.0-baseline.txt`（pytest 6 meta-test FAIL + ruff 5 err；compileall/production_gate PASS — 实施前基线）

## Phase 0 complete
