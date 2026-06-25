# Plan Boot — B3F-BR

- **Phase P0 complete**
- **原计划已读**：`PROJECT_IMPLEMENTATION_ROADMAP.md` Batch 3F.4 · `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.6+§8.5 · `BATCH_3F_TASK_CARD_MANIFEST.md` · GLOBAL×3 · `016_implement_source_conflict_validator.md`（reconcile 邻接）
- **用户目标**：关闭 `R3F-BR-01..05` — backfill/reconcile parity 叙事、handler registry、R3-PARTIAL-4/5 关账链；Playbook §8.5 40 tests 绿。
- **Batch map**：Round 3F · Segment 3F.4 · Playbook ID `B3F-BR`
- **Worktree**：`../quant-monitor-desk-wt-b3f-br` · `feature/round3-backfill-reconcile-parity`
- **前置**：B3V-SYNC 已交付 deferred matrix + crash-window handoff（`R3F-BR-03` regression guard only）
- **禁止**：重开 B3V crash-window 实现；production write；改 WriteManager 写模式语义
- **现状摘要（Execute 已落地，本 Plan 为补冻结）**：
  - `backend/app/sync/orchestrator.py`：`OrchestratorJobHandler` + `ORCHESTRATOR_HANDLER_REGISTRY` + `handler_registry()`
  - `tests/test_r3f_br_backfill_reconcile_closure.py`：R3F-BR-01..05 closure guards
  - `tests/test_sync_runners.py`：runner 接线 + backfill 分片规划
  - §8.5 命令子集 40 tests 已绿（未 commit）
