# Research: GitNexus RawStore Impact

- **Query**: GitNexus impact on RawStore for B3V-STOR Plan
- **Scope**: internal
- **Date**: 2026-06-25

## Findings

### Impact Summary

| Field        | Value                                           |
| ------------ | ----------------------------------------------- |
| Target       | `RawStore` (`backend/app/storage/raw_store.py`) |
| Direction    | upstream                                        |
| Risk         | **MEDIUM**                                      |
| Direct (d=1) | 6                                               |
| Total        | 18                                              |

### d=1 Callers

- `tests/test_raw_store.py`
- `backend/app/layer1_axes/ingestion.py`
- `backend/app/storage/file_registry.py`
- `backend/app/datasources/adapters/__init__.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/interface_probe.py`

### Implementation Note

Atomic write belongs in `path_compat.write_bytes_atomic`; `RawStore.save` single call-site change at line 70 (`write_bytes` → `write_bytes_atomic`).

## Caveats / Not Found

- No HIGH/CRITICAL risk from impact analysis.
- Full repo regression required (`uv run pytest -q`) before branch Done.
