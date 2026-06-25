# Vertical Slices — B3V-SYNC (/to-issues · Plan 3.5)

> 冻结为 MASTER §8 · 对应任务卡 §5 B02-SYNC-01..06

| 序 | ID | 垂直切片 | 交付物（完标准） | 依赖 | AC |
|----|-----|----------|------------------|------|-----|
| 0 | SYNC-BOOT | 基线 RED | 契约/runtime 现状断言 RED（parity + deferred） | — | AC-SYNC-PLAN |
| 1 | SYNC-01 | 契约 support matrix | `sync_job_contract.yaml` 含 `implemented_job_types` / `reserved_job_types` + deferred 元数据 | BOOT | AC-SYNC-002 |
| 2 | SYNC-02 | Runtime parity | 模块常量 `IMPLEMENTED_JOB_TYPES` == 契约 == 可调用 `run_*` 方法集 | SYNC-01 | AC-SYNC-002 |
| 3 | SYNC-03 | Reserved deferred | `run_full_load` / `run_data_quality` / `run_revision_audit`（新增薄入口）返回稳定 `DeferredJobTypeError`（code/owner/phase/docs_anchor） | SYNC-02 | AC-SYNC-002 |
| 4 | SYNC-04 | Registry reconcile | `D2-P1-1` proposed delta + 更新 `test_advA3_016` purpose（deferred 非 NIE） | SYNC-03 | AC-SYNC-REG |
| 5 | SYNC-05 | Crash-window 审查 | 文档化 ADR-001 窗口 + 注入 hook 点（`IncrementalJobRunner` 写提交后/COMPLETED 前） | SYNC-03 | AC-SYNC-001 |
| 6 | SYNC-06 | VR-SYNC-001 关闭 | **二选一**：(A) crash-window pytest 证明 WRITING+write_id 可恢复 COMPLETED；(B) `research/sync-001-handoff.md` → Round 3F.4 R3F-BR-03 | SYNC-05 | AC-SYNC-001 |

## 范围门控（SYNC-06）

| 条件 | 路径 |
|------|------|
| 注入测试 + 最小 `recover_stuck_writing_job`（或等价）可在不改 `write_contract` / ADR 前提下 GREEN | **路径 A**：分支内关闭 VR-SYNC-001 |
| 需同事务 COMPLETED 或改 WriteManager 写模式语义 | **路径 B**：handoff `research/sync-001-handoff.md`；本分支不关闭 VR-SYNC-001 |

## 测试文件替换

| 任务卡引用 | 实际路径 |
|------------|----------|
| `tests/test_sync_runners.py` | **不存在** → 使用 `tests/test_sync_orchestrator.py` + 可选 `tests/test_sync_job_contract.py`（新建，仅当 orchestrator 文件过大） |
