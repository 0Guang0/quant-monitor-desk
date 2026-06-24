# Bucket DS — comment conflicts

## Resolved in code (no comment edits)

| Location                        | Issue                                                                    | Resolution                           |
| ------------------------------- | ------------------------------------------------------------------------ | ------------------------------------ |
| `test_data_adapter_contract.py` | Unused `SourceDisabledError` import (not referenced by any test comment) | Removed dead import                  |
| `test_source_route_planner.py`  | `_planner()` wrapper added indirection without comment claim             | Inlined `production_route_planner()` |

## Name vs docstring drift (code matches docstring; no comment change)

| Test                                                                     | Note                                                                                          |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `test_etfDailyBar_disabledSource_marksYahooSkipWhenAuthorizationMissing` | Renamed from `test_userAuthRequired_*` (ponytail: name matches docstring; comments unchanged) |

## None otherwise
