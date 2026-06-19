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
