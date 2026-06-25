# Project overview — B3F-BR

> Phase 1a · ≤1 page

## 模块

`backend/app/sync/orchestrator.py` 是 sync job 编排门面；`runners.py` 承载 incremental/backfill/reconcile runner。B3V-SYNC 已冻结 implemented/reserved 矩阵与 deferred 错误。

## 本任务焦点

1. **Parity 叙事**：证明 backfill 不绕过 validator（R3F-BR-01）；reconcile re-fetch 有 pytest 锚点（R3F-BR-02）。
2. **Regression guard**：`R3-PARTIAL-5` 不得重开为 DEFERRED 实现项（R3F-BR-03）。
3. **Handler registry**：`OrchestratorJobHandler` 映射 job_type → entrypoint/runner_attr（R3F-BR-04）。
4. **Registry 链**：ADR-023 与 UNRESOLVED `R3-PARTIAL-4` honest DEFERRED（R3F-BR-05）。

## 风险

- 与 B3V crash-window 实现重复
- production write 误触
- registry 无证据关账

## 验证入口

Playbook §8.5：`pytest tests/test_sync_orchestrator.py tests/test_sync_runners.py` + 全量 pytest。
