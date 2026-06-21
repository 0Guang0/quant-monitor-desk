# GitNexus Execute Summary — Batch 2.75

> Phase 0 Boot · 2026-06-21

## Query

`query("live pilot datasource fetch preview route")` → DataSourceService, preview_route, route_planner.plan, production_equivalent_smoke.

## Impact (upstream · summaryOnly)

| Symbol                 | File                                     | Risk    | Direct callers | Notes                                                    |
| ---------------------- | ---------------------------------------- | ------- | -------------- | -------------------------------------------------------- |
| `DataSourceService`    | `backend/app/datasources/service.py`     | **LOW** | 1              | New caller `live_pilot` only; no semantic change planned |
| `preview_route`        | same                                     | **LOW** | 0              | Read-only Phase 2                                        |
| `fetch`                | same                                     | **LOW** | 0              | Phase 3 sandbox only                                     |
| `DbInspector`          | `backend/app/ops/db_inspector.py`        | **LOW** | 1              | Read-only baseline                                       |
| `DataQualityValidator` | `backend/app/validators/data_quality.py` | **LOW** | 2              | Phase 4 validation                                       |
| `ResourceGuard`        | `backend/app/core/resource_guard.py`     | **LOW** | 4              | Route/fetch guard                                        |

## New module

`backend/app/ops/live_pilot.py` — **new file**, no upstream dependents. Blast radius **LOW** if narrow orchestration only.

## detect_changes

Pre-Execute: no business-code edits yet (docs/task artifacts only).

## Proceed?

All targets **LOW** risk. Narrow extension of existing datasource/ops APIs; production DB write forbidden by AC.
