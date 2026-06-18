# Plan Boot — round2-batch-d-orchestrator

## 用户目标摘要

用户声明 Round 2 Batch C 已完成，要求核对进度后进入 Batch D Plan 阶段并严格执行 Trellis Plan 协议（P0→5d），产出可冻结的 `MASTER.plan.md` 全套工件。

## 原计划已读（ROUND + NNN 任务卡 + DECISIONS）

- ✅ `docs/implementation_tasks/README.md` + GLOBAL 四文件
- ✅ `ROUND_2_DATA_INGESTION_VALIDATION/README.md`
- ✅ `DECISIONS.md`（四批次边界、§9 延后台账）
- ✅ `014_implement_data_sync_orchestrator.md`
- ✅ 任务卡 §3 输入：`data_sync_orchestrator.md`、`sync_job_contract.yaml`、architecture docs
- ✅ Batch C 完成证据：`finish.md`、`audit.report.md` PASS、Repair 全关闭

## 前置依赖 / Batch 关系

```text
Batch A (011+012) → source_registry + adapter contract + fetch_log
Batch B (013)     → vendor skeletons + FetchPort
Batch C (015+016) → DataQualityValidator + SourceConflictValidator + DbValidationGate + 005
Batch D (014)     → DataSyncOrchestrator 串联上述组件 + 006 migration + ingestion smoke
```

GitNexus 确认：**无现有 orchestrator 实现**；`DbValidationGate`、`BaseDataAdapter`、`ResourceGuard` 已存在且可被编排层调用。

## 预期 AC 草稿（→ MASTER §2）

1. migration 006 创建 `data_sync_job` + `job_event_log`（对齐 `schema.sql`）
2. 六种 job_type 状态机（契约 YAML）可创建、转移、记 event
3. Incremental 路径：ResourceGuard → adapter fetch → validators → gate → WriteManager
4. Backfill 大范围自动分片；ResourceGuard 阻断时 `RESOURCE_GUARD_PAUSED`
5. Reconcile 与 Batch C `SourceConflictValidator` reconcile-first 衔接
6. Orchestrator 启动/registry bootstrap：`sync_to_db` 或 `scripts/sync_registry.py`
7. `scripts/ci_ingestion_smoke.py` 扩展覆盖 orchestrator smoke（GPT-P3-6）
8. 全库 pytest + ruff + production_gate 通过；不蔓延 Round 3/4/5 范围

## Plan Phase 顺序（1a→2→3→3.5→1b→4→5a→5b→5c→5d）

| Phase | 状态 |
|-------|------|
| P0 Boot | ✅ 本文件 |
| 1a GitNexus 轻量概览 | ✅ `project-overview.md` |
| 2a brainstorm | ✅ `prd.md` |
| 2b spec-driven-development | ✅ MASTER §2 |
| 3 grill-with-docs | ✅ `grill-with-docs-session.md` |
| 3.5 to-issues | ✅ `slice-issues.md` |
| 1b GitNexus 深度 | ✅ `gitnexus-summary.md` |
| 4 api-and-interface-design + codebase-design | ✅ MASTER §4–6 |
| 5a planning-and-task-breakdown | ✅ MASTER §5 |
| 5b writing-plans | ✅ `orchestrator-tests.md` |
| 5c trellis-before-dev | ✅ `implement.jsonl` |
| 5d doubt-driven-development | ✅ MASTER §7/§8 + AUDIT §2 修订 |

## Phase P0 complete
