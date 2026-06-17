# Data Adapter Contract

## FetchRequest

```yaml
run_id: string
source_id: string
data_domain: string
market_id: string|null
instrument_id: string|null
start_time: string|null
end_time: string|null
cursor: string|null
force_refresh: boolean
```

## FetchResult

```yaml
run_id: string
source_id: string
data_domain: string
status: SUCCESS | EMPTY_RESPONSE | AUTH_FAILED | RATE_LIMITED | NETWORK_ERROR | SCHEMA_DRIFT | FAILED
raw_file_paths: list[string]
staging_table: string|null
row_count: integer
content_hash: string|null
schema_hash: string|null
as_of_timestamp: string|null
publish_timestamp: string|null
fetch_time: string
error_message: string|null
```

## Rules

1. Adapter 不写 clean 表。
2. Adapter 必须写 raw 或 staging 证据。
3. Adapter 失败也必须返回 FetchResult。
4. Adapter 不负责最终主值选择。
5. Adapter 不允许 silent fallback。
6. `FetchRequest.source_id` 必须与 adapter 的 `source_id` 一致，否则 `SourceMismatchError`（pre-impl，不写 fetch_log）。

### Batch A scope note

Batch A enforces FetchResult evidence **fields** and FakeAdapter/fixture evidence only.
Real raw file creation and FileRegistry linkage are deferred to Batch B vendor adapter skeletons.

### FetchResult business validation (Pydantic v2)

- `row_count >= 0`
- `SUCCESS`: `row_count > 0` and (`raw_file_paths` or `staging_table`)
- `EMPTY_RESPONSE`: `row_count == 0`, no raw/staging evidence
- Failure statuses (`AUTH_FAILED`, `RATE_LIMITED`, `NETWORK_ERROR`, `SCHEMA_DRIFT`, `FAILED`): require `error_message`
