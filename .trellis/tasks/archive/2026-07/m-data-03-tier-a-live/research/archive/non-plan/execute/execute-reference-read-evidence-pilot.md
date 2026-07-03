# Execute reference read evidence — Pilot (`feature/m-data-03-pilot`)

> **⚠️ R1 切片名作废：** 只读参考。R2 切片为 `S-R2-*`；完整验收见 `S-R2-ACCEPT` · `plan-revision-r2.md` §2（禁止 defer / SKIP）。

> Per `parallel-dispatch-protocol.md` §3 · RED before live e2e · 2026-07-03

## Agent scope

| Field  | Value                         |
| ------ | ----------------------------- |
| Agent  | Execute Agent 2 (Pilot)       |
| Slices | S-LIVE-FRED · S-LIVE-BAOSTOCK |
| Branch | `feature/m-data-03-pilot`     |

## FRED — L3 (OpenBB architecture + SDD)

**Read:** `reference-adoption-m-data-03.md` §2.1 OpenBB three-phase · §3 fred row

| OpenBB stage      | QMD pilot alignment                                                    |
| ----------------- | ---------------------------------------------------------------------- |
| `transform_query` | `read_since_dates_for_series` → `FredIncrementalFetchProxy` start_time |
| `extract_data`    | `FredLiveFetchPort._live_observations` HTTP                            |
| `transform_data`  | `macro_staging_rows_from_bundle` → `axis_observation`                  |

**SDD (RED 前必读):** `plan-spec.md` Official API — FRED series observations:

- URL: `https://api.stlouisfed.org/fred/series/observations`
- Params: `series_id`, `api_key`, `file_type=json`, `observation_start`, `sort_order`, `limit`
- Implement: `backend/app/datasources/fetch_ports/fred_port.py` `FredLiveFetchPort` (仓内直接复用)

**Harness action:** `@pytest.mark.network` live e2e via `bootstrap_fred_live_e2e_ctx` + `use_mock=False`; no OpenBB code copy.

## BAOSTOCK — L3 + forbidden (EasyXT)

**Read:** `reference-adoption-m-data-03.md` §2.3 EasyXT forbidden · §3 baostock row

**L3 concept:** incremental window → port fetch → `security_bar_1d` clean (DCP-01 先例)

**forbidden:** EasyXT `unified_data_interface` silent fallback — `create_baostock_fetch_port(use_mock=False)` without `QMD_ALLOW_LIVE_FETCH` must raise `ProductLiveGateError`, never return `BaostockMockFetchPort`.

**SDD:** `plan-spec.md` — baostock Python API 文档（仓内 `BaostockProductLiveFetchPort` replay-first product path）

**Harness action:**

- Negative: `test_baostockLive_noSilentFallbackWhenGateClosed`
- Live: `build_baostock_incremental_service(use_mock=False)` + `run_baostock_bar_incremental` under `isolated_live_data_root`

## Reused in-repo patterns (direct reuse)

| Pattern                  | Path                                                     |
| ------------------------ | -------------------------------------------------------- |
| Isolated sandbox         | `tests/conftest.py` `isolated_live_data_root`            |
| Product live gate        | `product_live_gate.py`                                   |
| Fred incremental ops     | `fred_incremental_run.py`                                |
| Baostock incremental ops | `baostock_incremental_run.py`                            |
| Post-write inspect smoke | `DbInspector.inspect()` (full health profile → S-ACCEPT) |

## S-ACCEPT deferral note

Pilot slice verifies `DbInspector` table existence + row counts. Full `qmd data inspect` + `data_health` P0 gate per source is **S-ACCEPT** scope (`tier_a_live_acceptance.py` 11/11).
