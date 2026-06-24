# Bucket DS — Phase A align-ponytail checklist

**Branch:** `debt/test-hygiene/bucket-ds-sync`  
**Worktree:** `quant-monitor-desk-worktrees/bucket-ds-sync`  
**Verify:** 211 passed, 0 failed

## Module summary

| Module                                        | Tests | Align | Ponytail | Notes                                                                                                  |
| --------------------------------------------- | ----- | ----- | -------- | ------------------------------------------------------------------------------------------------------ |
| `test_datasource_service.py`                  | 13    | Y     | Y        | `_patch_probe_adapter_factory`; `write_bar_fixture`/`make_fixture_port`; drop `_load_service_contract` |
| `test_source_registry.py`                     | 32    | Y     | —        | Already clean; no changes                                                                              |
| `test_source_route_planner.py`                | 6     | Y     | Y        | Inline `production_route_planner()`; remove `_planner()`                                               |
| `test_source_capabilities.py`                 | 12    | Y     | Y        | Reuse `contract_gate_support.load_yaml`; drop dead `ADAPTERS_PKG`                                      |
| `test_platform_source_matrix.py`              | 4     | Y     | —        | Already uses `plan_route`                                                                              |
| `test_r3x_data_source_routing_blockers.py`    | 7     | Y     | —        | Already clean                                                                                          |
| `test_data_adapter_contract.py`               | 32    | Y     | Y        | Module `_EmptyResponseAdapter`; remove unused import                                                   |
| `test_adapter_skeletons.py`                   | 26+   | Y     | Y        | 10 inline `BaostockSkeleton` → `baostock_skeleton_market_only_class`                                   |
| `test_sync_orchestrator.py`                   | 24    | Y     | Y        | `ensure_bar_staging_tables` in route-plan test                                                         |
| `test_sync_jobs.py`                           | 8     | Y     | —        | Already clean                                                                                          |
| `test_sync_pipeline_contract.py`              | 1     | Y     | —        | Single test, self-contained                                                                            |
| `test_sync_migration.py`                      | 3     | Y     | —        | Already clean                                                                                          |
| `test_batch_d_orchestration_flow.py`          | 3     | Y     | Y        | Remove duplicate `ResourceGuard` monkeypatch                                                           |
| `test_vendor_fetch_e2e.py`                    | 2     | Y     | Y        | Align test 1 with `service_path_support` (fixture port + staging adapter)                              |
| `test_tdx_live_manual_probe_authorization.py` | 5     | Y     | —        | Offline gate; no network marker (intentional)                                                          |
| `service_path_support.py`                     | —     | Y     | Y        | `ensure_bar_staging_tables`; optional `supported_domains` on staging adapter                           |

## Shared helper changes (`service_path_support.py`)

| Helper                                                         | Purpose                                 | Callers                                                |
| -------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------ |
| `ensure_bar_staging_tables(con, stg, clean_name=...)`          | 6-column bar staging + empty clean copy | `test_vendor_fetch_e2e` (×2), `test_sync_orchestrator` |
| `make_staging_baostock_adapter_class(..., supported_domains=)` | Staging-writing baostock skeleton       | `test_vendor_fetch_e2e` test 1 (`market_bar_1d`)       |

## Network / live preservation

| File                                          | Marker                                 | Phase A action                                             |
| --------------------------------------------- | -------------------------------------- | ---------------------------------------------------------- |
| All 15 bucket modules                         | None                                   | No mock substitution for live paths; fixture E2E unchanged |
| `test_vendor_fetch_e2e.py`                    | None (offline `LocalFixtureFetchPort`) | Kept real orchestrator/service paths; no network mock      |
| `test_tdx_live_manual_probe_authorization.py` | None (docstring: 纯本地)               | Untouched                                                  |

## Ponytail (value conserved)

| Change                                        | Rationale                                                                  |
| --------------------------------------------- | -------------------------------------------------------------------------- |
| `_patch_probe_adapter_factory`                | Dedup ProbeAdapter monkeypatch in 2 service tests; same gate order asserts |
| `baostock_skeleton_market_only_class` fixture | conftest ladder #2; identical `cn_equity_daily_bar` domain                 |
| `_EmptyResponseAdapter`                       | Single EMPTY_RESPONSE stub for 2 fetch_log tests                           |
| `ensure_bar_staging_tables`                   | Same DDL; 3 call sites → 1 helper                                          |
| Vendor E2E test 1 → support helpers           | Same fixture JSON, staging insert, orchestrator path                       |
| Remove dead imports / duplicate monkeypatch   | No assertion or coverage loss                                              |

## Per-module 五问 (all Y)

### test_datasource_service.py — Y

1. 被测对象 = `DataSourceService` / contract scan — **Y**
2. 路由顺序、ROUTE_PLAN、fetch_log 验证点 — **Y**
3. ProbeAdapter 仅用于注释声明的 gate-order 注入 — **Y**
4. 删 `_load_service_contract` 一层包装 — **Y**
5. `contract_gate_support` + `service_path_support` — **Y**

### test_source_registry.py — Y (no edits)

### test_source_route_planner.py — Y

### test_source_capabilities.py — Y

### test_platform_source_matrix.py — Y (no edits)

### test_r3x_data_source_routing_blockers.py — Y (no edits)

### test_data_adapter_contract.py — Y

### test_adapter_skeletons.py — Y

### test*sync_orchestrator.py — Y (incl. `test_r3ySync001*\*` production profile guards untouched)

### test_sync_jobs.py — Y (no edits)

### test_sync_pipeline_contract.py — Y (no edits)

### test_sync_migration.py — Y (no edits)

### test_batch_d_orchestration_flow.py — Y

### test_vendor_fetch_e2e.py — Y

### test_tdx_live_manual_probe_authorization.py — Y (no edits)

## Diff scope

9 files changed, 134 insertions(+), 240 deletions(-)  
Touches only allowed files + `tests/service_path_support.py`

## Phase B perf notes (no changes in Phase A)

Slow candidates for Phase B profiling (value must stay): `test_sync_orchestrator.py` backfill shards, `test_source_registry.py` YAML variant loops.
