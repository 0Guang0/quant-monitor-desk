# DuckDB Lock, Concurrency, and Crash Recovery Policy

## 1. 目的

修复 QM-AUD-009：单写多读必须有文件锁、隔离和崩溃恢复策略。

## 2. 并发模型

- DuckDB 允许本地嵌入式读写，但本项目统一采用“单写、多读、短事务”。
- 所有 clean table 写入必须经过 `DuckDBWriteManager`。
- 写任务必须获取跨进程文件锁，例如 `data/duckdb/.write.lock`。
- 读连接必须设置 `read_only=True`，并应用与 writer 一致的 `memory_limit/threads/temp_directory`。

## 3. 崩溃恢复

- 写任务开始前写 `write_audit_log(status='STARTED')`。
- 成功后写 `COMMITTED`。
- 失败后写 `FAILED` 和错误摘要。
- 启动时扫描长时间停留 `STARTED` 的写任务，标记为 `ABANDONED_NEEDS_REVIEW`，不得自动重放。

## 4. 测试要求

- `test_concurrentWriters_secondWriterBlocked`
- `test_readerUsesReadOnlyConnection`
- `test_abandonedStartedWrite_markedNeedsReview`
