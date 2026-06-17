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
status: SUCCESS | EMPTY_RESPONSE | NOT_PUBLISHED_YET | AUTH_FAILED | RATE_LIMITED | NETWORK_ERROR | SCHEMA_DRIFT | FAILED
raw_file_paths: list[string]
staging_table: string|null
row_count: integer
content_hash: string|null
schema_hash: string|null
as_of_timestamp: string|null
publish_timestamp: string|null
fetch_time: string
error_message: string|null
latency_ms: integer|null
retry_count: integer
```

## Rules

1. Adapter 不写 clean 表。
2. Adapter 必须写 raw 或 staging 证据（`EMPTY_RESPONSE` / `NOT_PUBLISHED_YET` 除外）。
3. Adapter 失败也必须返回 FetchResult。
4. Adapter 不负责最终主值选择。
5. Adapter 不允许 silent fallback。
6. `FetchRequest.source_id` 必须与 adapter 的 `source_id` 一致，否则 `SourceMismatchError`（pre-impl，不写 fetch_log）。

### Batch scope notes

**Batch A：** 仅交付 FetchResult 证据**字段**与 FakeAdapter/fixture；不创建真实 raw 文件、不注册 FileRegistry。

**Batch B（013，已完成 @ repair）：** vendor skeleton 经 `FetchPort` + `RawStore` 写 raw；生产路径 `create_adapter()` 必须显式注入 `fetch_port` 与 `file_registry`；`NOT_PUBLISHED_YET` 纳入 contract（cninfo 未发布语义，区别于 `EMPTY_RESPONSE`）。

**仍延后：**

- DB 层 CHECK/NOT NULL → **Batch C 前** migration `005_*`（应用层 Pydantic + `FetchLogWriter._validate_for_persist` 双保险）
- DuckDB staging 表存在性校验 → **Batch C**
- Orchestrator 级 ResourceGuard → **Batch D**（skeleton 已有 `max_payload_bytes` 前置防呆）

### FetchResult business validation (Pydantic v2)

- `row_count >= 0`
- `SUCCESS`: `row_count > 0` and (`raw_file_paths` or `staging_table`)
- `EMPTY_RESPONSE`: `row_count == 0`, no raw/staging evidence
- `NOT_PUBLISHED_YET`: `row_count == 0`, no raw/staging evidence, `error_message` 描述未发布（调度应等待发布窗口，**≠** 接口空返回）
- Failure statuses (`AUTH_FAILED`, `RATE_LIMITED`, `NETWORK_ERROR`, `SCHEMA_DRIFT`, `FAILED`): require `error_message`
- `latency_ms`: optional, `>= 0` when set
- `retry_count`: default `0`, `>= 0`

### fetch_log.error_type mapping (Batch A+)

| status | error_type |
|--------|------------|
| SUCCESS | NULL |
| EMPTY_RESPONSE | empty |
| NOT_PUBLISHED_YET | not_published |
| AUTH_FAILED | auth |
| RATE_LIMITED | rate_limit |
| NETWORK_ERROR | network |
| SCHEMA_DRIFT | schema |
| FAILED | failed |
