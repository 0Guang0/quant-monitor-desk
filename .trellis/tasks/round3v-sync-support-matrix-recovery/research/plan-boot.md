# Plan Boot — B3V-SYNC

- **Phase P0 complete**
- **原计划已读**：`B02_04_sync_job_support_and_recovery.md` · Playbook §3.1+§3.5+§4 · `ROUND3_BATCH_IMPLEMENTATION_MAP.md` Round 3V · GLOBAL×3
- **用户目标**：显式区分 sync job 已实现 vs 预留类型；reserved 返回稳定 deferred 错误；关闭或精确交接 VR-SYNC-001 crash-window。
- **Batch map**：`ROUND3_BATCH_IMPLEMENTATION_MAP.md` Round 3V · `R3V-B02-SYNC-01/02`
- **任务卡**：`B02_04_sync_job_support_and_recovery.md`
- **Playbook**：`BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.5 + §4
- **Worktree**：`../quant-monitor-desk-wt-b3v-sync` · `fix/round3v-sync-support-matrix-recovery`
- **依赖（只读）**：B3V-OPS `write_contract.yaml` / `WriteManager` 写模式语义；**建议 B3V-OPS 之后合并**
- **禁止**：改 write 模式契约、CLI 发布、production clean write、裸 `NotImplementedError` 泄漏到边界
- **VR 所有权**：`VR-SYNC-002`（support matrix）、`VR-SYNC-001`（crash-window pytest **或** `research/sync-001-handoff.md`）
- **现状摘要**：
  - `sync_job_contract.yaml` 仅扁平 `job_types` 列表，无 implemented/reserved 分裂
  - `run_full_load` / `run_data_quality` 抛 `NotImplementedError`（`orchestrator.py:225-235`）
  - `revision_audit` 可建 job 达 STAGED，无 runner 入口
  - 已实现 runner：`run_incremental` / `run_backfill` / `run_reconcile`
  - `IncrementalJobRunner` 在 `with cm.writer()` 提交写后、事务外再 `transition(COMPLETED)`（`runners.py:437-510`），与 ADR-001 一致，存在 R3-PARTIAL-5 crash-window
  - `tests/test_sync_runners.py` **不存在**；基线为 `tests/test_sync_orchestrator.py`
  - `test_advA3_016_orchestratorDeferredRunners` 仍断言 `NotImplementedError`，Execute 须改 purpose 对齐 deferred 语义
