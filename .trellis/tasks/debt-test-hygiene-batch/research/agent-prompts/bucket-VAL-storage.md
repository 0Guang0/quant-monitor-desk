# Agent 派发 — 桶 VAL（Validation / Storage / Schema）

> **Worktree：** `debt/test-hygiene/bucket-val-storage` from `master`  
> **Bucket ID：** VAL

## Allowed files

```
tests/test_write_manager.py
tests/test_db_validation_gate.py
tests/test_data_quality_validator.py
tests/test_source_conflict_validator.py
tests/test_batch_c_validation_flow.py
tests/test_raw_store.py
tests/test_duckdb_connection.py
tests/test_schema_migration.py
tests/test_schema_contract.py
tests/test_sql_identifiers.py
tests/test_path_compat.py
```

MERGE-C 锁：`tests/db_helpers.py`（若必须改，在本桶 evidence 说明并等 merge 时协调）

## 特殊注意

- 本桶几乎全部在 authority_graph：deletion candidates 通常为空
- schema/migration 测试注意 tmp DB 生命周期；ponytail 合并重复的 `apply_migrations` + duckdb connect 块
- `test_batch_c_validation_flow.py` 是 Round2 核心 runtime-contract：对齐注释时保留 audit/clean write 双路径

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_write_manager.py tests/test_db_validation_gate.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py tests/test_batch_c_validation_flow.py tests/test_raw_store.py tests/test_duckdb_connection.py tests/test_schema_migration.py tests/test_schema_contract.py tests/test_sql_identifiers.py tests/test_path_compat.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-VAL-*`

## 公共约束

见 `_COMMON.md`。
