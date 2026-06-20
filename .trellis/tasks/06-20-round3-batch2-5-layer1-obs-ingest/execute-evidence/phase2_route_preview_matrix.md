# Phase 2 — Route Preview Matrix

- **Generated at:** 2026-06-20T12:43:44Z
- **Frozen indicator:** `ENV-E1-DGS10`
- **Dry-run:** True
- **FRED live deferred:** True

## Allowlist

- `ENV-E1-DGS10`

## Route previews

### `ENV-E1-DGS10` @ 2024-06-15

- data_domain: `macro_supplementary`
- operation: `fetch_macro_series`
- series_id: `DGS10`
- declared primary: `FRED:DGS10`
- staged note: B2.5-O-05: declared primary_source FRED:DGS10 deferred; staged route macro_supplementary.fetch_macro_series used
- route_status: `READY`
- selected_source_id: `akshare`
- resource_guard: `OK`
- capability_verified: True
- intended_as_of_range: {'start': '2024-06-15', 'end': '2024-06-15'}
- stop_reason: None

| source_id | role    | enabled | skip_reason |
| --------- | ------- | ------- | ----------- |
| `akshare` | Primary | True    | None        |

## No-mutation proof

- db_path: `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/execute-evidence/.phase1-baseline-sandbox/duckdb/quant_monitor.duckdb`
- db_capture_strategy: `phase1_sandbox_copy_reused`
- db_file_hash_unchanged: True
- row_counts_unchanged: True
- before: `{'axis_observation': 0, 'fetch_log': 0, 'file_registry': 0, 'axis_feature_snapshot': 0, 'axis_interpretation_snapshot': 0, 'axis_snapshot_lineage': 0}`
- after: `{'axis_observation': 0, 'fetch_log': 0, 'file_registry': 0, 'axis_feature_snapshot': 0, 'axis_interpretation_snapshot': 0, 'axis_snapshot_lineage': 0}`
