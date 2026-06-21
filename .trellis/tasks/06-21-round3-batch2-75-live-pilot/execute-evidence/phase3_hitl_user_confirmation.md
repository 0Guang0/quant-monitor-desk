# Phase 3 HITL User Confirmation — Batch 2.75

> **Status:** User-approved · **Approved on:** 2026-06-21  
> **Authorization:** `docs/quality/batch275_user_authorization_2026-06-21.md`  
> **Policy:** `docs/quality/production_live_pilot_policy.md`

## User confirmation

The project owner explicitly confirmed proceeding with **controlled live network fetch** for Batch 2.75 Phase 3 under the following constraints:

- Sandbox root only: `.audit-sandbox/batch275-live-pilot/`
- **Raw-only** first pass (`raw_only=true`, `allow_clean_write=false`)
- Production DB `data/duckdb/quant_monitor.duckdb` — **read-only**; no mutation
- No fixture/staged fallback (`StubFetchPort` / Batch 2.5 staged evidence)
- Row cap ≤100 total (approved requests ≤40)
- Request 3 success does **not** close FRED primary for ENV-E1-DGS10 (B2.5-O-05)

**User statement (2026-06-21):** 「确认请执行」

## Three approved micro-pilot requests (summary)

| #   | source_id | data_domain         | operation                  | symbol    | max_rows |
| --- | --------- | ------------------- | -------------------------- | --------- | -------- |
| 1   | baostock  | cn_equity_daily_bar | fetch_daily_bar            | sh.600519 | 10       |
| 2   | akshare   | cn_equity_daily_bar | fetch_daily_bar_validation | sh.600519 | 10       |
| 3   | akshare   | macro_supplementary | fetch_macro_series         | DGS10     | 20       |

## Risk acknowledgment

| Risk                                  | Mitigation                                                       |
| ------------------------------------- | ---------------------------------------------------------------- |
| External vendor availability          | Fail-closed → `PILOT_FAIL_SOURCE` + evidence; no silent fallback |
| Sandbox escape / production write     | `write_target=sandbox`; production hash proof after fetch        |
| QMT/FRED/Yahoo unauthorized access    | Explicitly disabled in `live_pilot.py`                           |
| Validation source promoted to Primary | Request 2 validation-only; registry unchanged                    |

## HITL gate outcome

O-01 **closed** — Execute may proceed to §8.5b sandbox raw-only live fetch.
