# Context Closure — Batch 2.75 Execute (E16 L2)

> Upstream/wiring closure for MASTER §4/§6 touch points.

## Wiring symbols (impact upstream)

| Symbol                    | Risk | Upstream closure                                                                     |
| ------------------------- | ---- | ------------------------------------------------------------------------------------ |
| `DataSourceService`       | LOW  | 1 direct caller; live_pilot adds new caller without changing fetch/preview semantics |
| `DbInspector`             | LOW  | 1 direct caller; pilot uses read-only inventory only                                 |
| `DataQualityValidator`    | LOW  | 2 direct callers; Phase 4 reads sandbox raw                                          |
| `ResourceGuard`           | LOW  | 4 direct callers; guard snapshot in route preview                                    |
| `SourceRoutePlanner.plan` | LOW  | Used via preview_route; no planner edits planned                                     |
| `source_conflict` inspect | LOW  | Phase 4 conflict report only                                                         |

## New orchestration

`live_pilot.py` — greenfield; calls existing services; no WriteManager on production path.

## Filtered (do NOT touch)

- `backend/app/layer1_axes/ingestion.py`
- `backend/app/layer1_axes/ingestion_evidence.py`
- `build_staged_fixture_service` / `StubFetchPort`

## Sprint mutex

No ingestion R2b–R2d in same sprint (AC-PM4).

## Conclusion

Upstream closure complete. All wiring targets LOW risk. Proceed §8.1+ with narrow `live_pilot` + gate tests.
