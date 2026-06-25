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
status: SUCCESS | EMPTY_RESPONSE | NOT_PUBLISHED_YET | DISABLED_SOURCE | AUTH_FAILED | RATE_LIMITED | NETWORK_ERROR | SCHEMA_DRIFT | FAILED
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
6. Adapter 可以借鉴 `参考项目/` 中成熟 provider 的连接管理、字段映射、错误分类、schema 识别和报告形态，但落地代码必须是 QMD-owned module，不得在运行时 import `参考项目/**`。
7. 参考项目中的交易、下单、自动登录、验证码、账户控制、全市场默认扫描、silent fallback 语义不得进入 Adapter contract。
8. OpenBB 只能作为 provider/package/catalog 架构参考；不得复制 AGPL runtime source 或 provider fetcher class。

## Structured schema_hash (VR-DATA-001)

Structured file types: `json`, `csv`, `parquet`.

When `status == SUCCESS` and `row_count > 0` for a structured fetch:

- `schema_hash` **must** be non-null (port-supplied or adapter-inferred).
- Adapter **must not** return `SUCCESS` with a null `schema_hash` for structured payloads.
- If bounded schema inference fails (corrupt file, unreadable header/columns), adapter returns
  `SCHEMA_DRIFT` or `FAILED` — never `SUCCESS` with a missing hash.

Schemaless exemptions (no `schema_hash` required): sources explicitly registered as schemaless
(e.g. opaque binary evidence). Registry field closure is out of scope for adapter-only slices;
gate may still use `raw_file_paths` suffix or `file_registry.file_type` to classify structured
fetches.

Inference bounds (no full-file scan):

- JSON: shape fingerprint via canonical JSON structure (existing).
- CSV: first header line only, max 64 KiB prefix, stdlib `csv`.
- Parquet: DuckDB `DESCRIBE SELECT * FROM read_parquet(?)` column names (LIMIT 0 semantics).
