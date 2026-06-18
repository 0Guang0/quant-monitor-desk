# Grill-with-docs Session — Batch D DataSyncOrchestrator

> Phase 3 · 锚点：`DECISIONS.md` + `sync_job_contract.yaml` + `data_sync_orchestrator.md`  
> 模式：对抗性自问自答（Plan 阶段无用户逐问；结论已写入 MASTER）

## Q1: Orchestrator 是否直接写 clean 表？

**挑战：** `data_sync_orchestrator.md` §13.1 说「不直接写 clean」，但状态含 `WRITING`。

**推荐：** `WRITING` 状态仅表示 Orchestrator **调用** `DuckDBWriteManager.write()`；SQL 只在 WriteManager 内。  
**决议：** MASTER §4 冻结；Audit A2 检查无 orchestrator 内 raw SQL INSERT clean。

## Q2: ReconcileJob 与 Batch C reconcile-first 谁权威？

**挑战：** Batch C 已在 `SourceConflictValidator` 实现 reconcile-first；§13.4.5 又描述独立 ReconcileJob。

**推荐：** Batch D ReconcileJob **委托** `SourceConflictValidator` + 可选 adapter 重抓；不重复冲突比较逻辑。  
**决议：** MASTER §8.7；避免双实现。

## Q3: `job_type=data_quality` 是否在本批全量实现？

**挑战：** 契约列六种类型；014 任务目标列五种 + DataQualityJob 在模块 doc。

**推荐：** Batch D 交付 **可运行骨架**：`data_quality` job 可创建/转移/event，但逻辑可委托已有 `DataQualityValidator`（抽样审计路径），不做 Layer 3 全量审计。  
**决议：** MASTER §3.2 显式 defer Layer 建模；AC-2 覆盖六种 type 的 **状态机**，非六种全生产调度。

## Q4: init_db 是否必须自动 sync registry？

**挑战：** DECISIONS GPT-init_db 登记为 Batch D；但生产可能需显式 CLI。

**推荐：** 提供 `scripts/sync_registry.py` + Orchestrator `bootstrap()` 可选调用；`init_db.py` **追加**文档化钩子或 `--sync-registry` flag，默认行为不变以免破坏 Round 1 测试。  
**决议：** MASTER §8.8。

## Q5: Backfill 「自动拆分」阈值？

**挑战：** 未在 DECISIONS 冻结具体天数。

**推荐：** eco 模式下单 task `date_end - date_start ≤ 31` 天；超出则按 31 天分片生成多个 `task_id`。  
**决议：** MASTER §6.3 + §8.6 测试断言分片数。

## Q6: 路径 `backend/sync` vs `backend/app/sync`？

**挑战：** 任务卡 §4 写 `backend/sync/`；DECISIONS §1 写 `backend/app/*`。

**推荐：** 以 DECISIONS 为准 → `backend/app/sync/`。  
**决议：** `original-plan-trace.md` 路径纠偏；禁止创建 `backend/sync/` 平行树。

## 会话产出

- §7 Red Flags 增补：状态 ad-hoc、双 reconcile 实现、orchestrator 直写 clean
- §8 切片顺序确认：migration → 状态机 → orchestrator 核心 → ResourceGuard → incremental E2E → backfill → reconcile → registry → smoke → docs
