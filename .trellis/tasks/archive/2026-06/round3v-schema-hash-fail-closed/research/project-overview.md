# Project overview — B3V-DATA (GitNexus 1a)

- **Query**: schema_hash ValidationGate structured fetch
- **Date**: 2026-06-25

## 数据流（人话）

1. **Adapter**（`SkeletonAdapterBase._fetch_impl`）经 `FetchPort` 取 payload → `RawStore.save` → `FetchResult`，其中 `schema_hash=_infer_schema_hash(payload)`。
2. **Fetch log** 持久化 `schema_hash`（`FetchLogWriter`）。
3. **Validation** 产出 `validation_report`（含 `quality_flags` 可含 `SCHEMA_DRIFT`）。
4. **WriteManager** 调用 `DbValidationGate.assert_can_write` → `_enforce_report` → `_schema_hash_blocks_write`。

## 关键符号

| 符号                        | 文件                         | 职责                                                    |
| --------------------------- | ---------------------------- | ------------------------------------------------------- |
| `_infer_schema_hash`        | `skeleton_base.py:26-37`     | 仅 JSON 形状指纹；CSV/Parquet 返回 None                 |
| `_schema_hash_blocks_write` | `validation_gate.py:166-206` | 比较 fetch_log vs file_registry；缺失 hash 时 fail-open |
| `assert_can_write`          | `validation_gate.py:277-311` | 生产写入门前最后一道                                    |

## GitNexus impact

- `_schema_hash_blocks_write` 上游：`_enforce_report` → `assert_can_write`；风险 **LOW**；影响 `staged_pilot` 包装 gate 与 `test_db_validation_gate.py`。

## 测试基线

- `test_schemaHashDriftWithoutApproval_rejects` — 漂移路径已覆盖
- `test_inferSchemaHash_*` — JSON infer 已覆盖
- **缺口**：缺失 hash、CSV/Parquet、损坏文件
