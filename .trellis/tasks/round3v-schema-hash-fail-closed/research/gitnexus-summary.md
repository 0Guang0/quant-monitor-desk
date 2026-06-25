# GitNexus 深度摘要 — B3V-DATA (1b)

- **Date**: 2026-06-25
- **Repo**: quant-monitor-desk

## query: schema_hash ValidationGate

- 主流程：`assert_can_write` → `_enforce_report` → `_schema_hash_blocks_write`
- 相关测试：`test_db_validation_gate.py`, `test_adapter_skeletons.py`
- 邻接：`staged_pilot._StagedPilotValidationGate` 委托 `DbValidationGate`

## context: _schema_hash_blocks_write

- **incoming**: `_enforce_report`（唯一调用方）
- **outgoing**: `_quality_flags_include_schema_drift`
- **逻辑**: `write_mode` 在 `manual_patch`/`schema_migration` 时跳过；`SCHEMA_DRIFT` flag 直接 block；否则查 `fetch_log` 最新 hash vs `file_registry` baseline

## context: _infer_schema_hash

- **incoming**: `SkeletonAdapterBase._fetch_impl`, 单元测试
- **outgoing**: `_shape`（JSON 键类型指纹）
- **缺口**: `file_type` 非 json 返回 None

## impact: _schema_hash_blocks_write (upstream)

- **risk**: LOW
- **depth-1**: `_enforce_report`
- **depth-3**: `staged_pilot` 包装 gate
- **测试**: Tests 模块间接命中

## 改码建议（Plan 级，非实现）

1. 扩展 `_infer_schema_hash`：CSV 首行/有界字节；Parquet 用 DuckDB `DESCRIBE`/`LIMIT 0`（不扫全文件）
2. `_fetch_impl`：结构化 SUCCESS 无 hash → `FAILED` 或 `SCHEMA_DRIFT`
3. `_schema_hash_blocks_write`：结构化判定下 missing current hash → block；missing baseline 且需漂移检测 → block

## codebase-memory

- MCP `search_code` 需 `pattern` 参数；本任务以 GitNexus 为主交叉，grep 补盲区。
