# ADR-001：接入校验与写入事务边界

## 状态

已接受（2026-06-19）

## 背景

Round2 Batch C/D 要求：校验报告、冲突报告与 clean 写入形成可审计证据链。`WriteManager` 不得在缺少已通过校验的 `validation_report_id` 时提交 clean 行。编排器上的 `COMPLETED` 状态须在写入事务**提交之后**再发出。

## 决策

1. **校验 + 冲突：** 在单一 writer 连接事务内、进入 `WRITING` 之前完成。
2. **Clean 写入：** 在同一连接作用域内调用 `WriteManager.write(..., own_transaction=False)`；`DbValidationGate` 根据校验报告强制执行 `can_write_clean`。
3. **任务状态 `COMPLETED`：** 在写入事务 commit 之后单独过渡发出，避免「状态审计回滚」误伤已持久化的 clean 行。
4. **Registry 同步：** `SourceRegistry.sync_to_db` 不自行开启事务；需要原子性的多步引导由调用方显式包事务。

## 后果

- 通过顺序「先 commit 写入 → 再 COMPLETED」避免「部分写入却已标完成」。
- reconcile 与 backfill runner 与增量任务复用同一套校验/写入管线。
