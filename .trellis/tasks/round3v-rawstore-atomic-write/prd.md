# PRD — B3V-STOR Atomic Raw Write

## 问题

审计项 `VR-STOR-001`：原始证据文件（json/csv/parquet）落盘非原子，进程崩溃或 I/O 异常可能留下**半写入**目标文件，破坏证据链完整性。

## 用户故事

作为证据流水线维护者，我希望 RawStore 写文件要么完整可见要么目标路径不变，以便下游 hash 校验与 FileRegistry 引用可信。

## 非目标

- 不改 `content_hash` 路径命名
- 不改 FileRegistry 去重/注册语义
- 不引入外部 FS 依赖
- 不做 production DB 写入
- 不实现 Round 4/5 功能

## 成功标准

- `write_bytes_atomic` 经 TDD 验证
- `tests/test_raw_store.py` 新增 crash/idempotency 用例全绿
- 既有 RawStore 测试无回归
- `VR-STOR-001` proposed registry delta（主会话闭合）
