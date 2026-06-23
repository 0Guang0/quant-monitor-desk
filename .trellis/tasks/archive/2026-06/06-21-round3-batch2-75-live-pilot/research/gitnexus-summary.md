# GitNexus Summary — Batch 2.75 (Plan 1b)

> analysis_waiver: false · symbols queried via codebase read (GitNexus MCP optional refresh before Execute)

## Impact targets (pre-edit)

| Symbol / area                         | Upstream risk                         | Plan note                                                          |
| ------------------------------------- | ------------------------------------- | ------------------------------------------------------------------ |
| `DataSourceService.fetch`             | sync pipeline, layer1 ingestion tests | New caller `live_pilot` only; no change to default fetch semantics |
| `DataSourceService.preview_route`     | route tests                           | Read-only Phase 2                                                  |
| `DbInspector` / `capture_*_inventory` | ops db inspect tests                  | Extend for pilot baseline evidence                                 |
| **New** `live_pilot` module           | ops + datasource                      | LOW if narrow; no WriteManager on production path                  |

## Execution flows touched

1. Authorization gate → sandbox `QMD_DATA_ROOT`
2. Route preview → ResourceGuard → adapter fetch → raw_store + fetch_log + file_registry
3. Optional validation read on sandbox raw files (no clean write default)

## Blast radius

- **LOW** for Phase 0–2 (read-only + tests)
- **MEDIUM** for Phase 3 live network (bounded rows; sandbox only)
- **HIGH** if production DB path writable — **forbidden by AC**

Execute must run `impact()` before editing `DataSourceService`, `route_planner`, or `db_inspector`.
