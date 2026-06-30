# GitNexus Summary — B3V-SYNC (Plan 1b)

## query: sync job orchestrator runners job types deferred

- **orchestrator.py**：`run_full_load` / `run_data_quality` 为 deferred stub（NotImplementedError）
- **runners.py**：`_finalize_staged` 同事务写 clean；`IncrementalJobRunner.run` 在 writer 块外 `transition(COMPLETED)`（crash-window）
- **jobs.py**：`create_job` 接受六种 job_type；状态机按 job_type 扩展转移
- **write_manager.py**：`UNSUPPORTED_MODES` 抛稳定 `ValueError` — **deferred 错误模式参考**（B3V-OPS 独占写模式契约，SYNC 只读对齐）

## impact 预判（Execute 前必跑）

| 符号                                    | 风险                |
| --------------------------------------- | ------------------- |
| `DataSyncOrchestrator.run_full_load`    | LOW — 测试 + 契约   |
| `DataSyncOrchestrator.run_data_quality` | LOW                 |
| `IncrementalJobRunner.run`              | MEDIUM — crash hook |
| 新增 `run_revision_audit`               | LOW                 |
