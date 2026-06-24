# 桶 VAL — Phase A align-checklist

**分支：** `debt/test-hygiene/bucket-val-storage`  
**Agent：** agent-VAL  
**Worktree：** `quant-monitor-desk-worktrees/bucket-val-storage`

## 模块汇总（126 用例，五问全 Y）

| 模块                                | 用例数 | 1 对象 | 2 验证点 | 3 失败含义 | 4 无额外行为 | 5 复用 helper                             | Phase A 改动                                                                                  |
| ----------------------------------- | ------ | ------ | -------- | ---------- | ------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| `test_write_manager.py`             | 22     | Y      | Y        | Y          | Y            | Y (`create_test_write_manager`, `_setup`) | `_empty_clean_table`、`_patch_connect_calls`；`_setup` 改 CM.writer+migrate；顶栏 import 合并 |
| `test_db_validation_gate.py`        | 12     | Y      | Y        | Y          | Y            | Y (`_setup`, `_insert_report`)            | 已对齐，无代码改动                                                                            |
| `test_data_quality_validator.py`    | 23     | Y      | Y        | Y          | Y            | Y (`_request`, `_row`, `_cm`)             | 已对齐，无代码改动                                                                            |
| `test_source_conflict_validator.py` | 11     | Y      | Y        | Y          | Y            | Y (`_request`, `_row`, `_cm`)             | 已对齐，无代码改动                                                                            |
| `test_batch_c_validation_flow.py`   | 3      | Y      | Y        | Y          | Y            | Y                                         | `FLOW_COLUMNS` + `_validate_quality` 去重复 validate_table 块；保留 audit/clean 双路径        |
| `test_raw_store.py`                 | 20     | Y      | Y        | Y          | Y            | Y (`create_test_write_manager`, `_cm`)    | `_SAVE_KW`/`_save_default`；`_cm` 统一 CM.writer+migrate                                      |
| `test_duckdb_connection.py`         | 14     | Y      | Y        | Y          | Y            | Y (`_init`, `_assert_reader_*`)           | `_FakePsutilMem`/`_patch_psutil_mem`；`conn_mod` 顶栏 import                                  |
| `test_schema_migration.py`          | 10     | Y      | Y        | Y          | Y            | Y                                         | `ALL_MIGRATION_VERSIONS` 常量去重复                                                           |
| `test_schema_contract.py`           | 4      | Y      | Y        | Y          | Y            | Y (`_table_columns`)                      | 已对齐，无代码改动                                                                            |
| `test_sql_identifiers.py`           | 5      | Y      | Y        | Y          | Y            | Y                                         | 已对齐，无代码改动                                                                            |
| `test_path_compat.py`               | 2      | Y      | Y        | Y          | Y            | Y                                         | 已对齐，无代码改动                                                                            |

## ponytail 改动摘要

- **去重复 setup**：空 clean 表 DDL、Batch C 列元组、raw 默认 save 参数、迁移版本集合、psutil mock
- **统一 DB bootstrap**：`write_manager`/`raw_store` 的 `_setup`/`_cm` 与桶内其他文件一致（`ConnectionManager.writer` + `apply_migrations`）
- **未改**任何测试注释/docstring
- **未删/弱化**断言；未 mock 真实 DuckDB/WriteManager 写路径
- **未改** `tests/db_helpers.py`（继续复用 `create_test_write_manager`）

## 汇总

- 用例数：126
- 全 Y：是
- comment-conflicts：none
- deletion-candidates：空（authority_graph 覆盖，见 YAML）
