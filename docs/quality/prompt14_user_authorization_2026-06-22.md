# PROMPT_14 User Authorization — Round 3 Staged Real-Data Pilot

> Status: user-approved authorization record for `feature/round3-real-data-staged-pilot` (R3X staged pilot).  
> This file is **authorization evidence only**; orchestration must still pass fail-closed gates in `StagedPilotRequest` and policy tests.

## Authorization scope

| Field             | Value                                                                                          |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| Pilot ID          | `r3x-staged-pilot-20260622`                                                                    |
| Task card         | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`   |
| Policy            | `docs/quality/production_live_pilot_policy.md` + `docs/quality/staged_acceptance_policy.md`    |
| Approved by       | User (project owner)                                                                           |
| Approved on       | 2026-06-22                                                                                     |
| Run mode          | `staged_only` — sandbox raw/staging evidence; **no** production clean write                  |

## Global defaults (every micro-pilot request)

| Control                     | Approved value                                                          |
| --------------------------- | ----------------------------------------------------------------------- |
| `dry_run`                   | `true` for route preview; live fetch only after route `READY` in sandbox |
| `raw_only`                  | `true`                                                                  |
| `write_target`              | `sandbox` under `.audit-sandbox/r3x-staged-pilot/`                      |
| `allow_clean_write`         | `false`                                                                 |
| `production_clean_write`    | `false`                                                                 |
| Production DB               | `data/duckdb/quant_monitor.duckdb` — read-only inspect; no mutation     |
| `max_symbols`               | `1` (single symbol per request)                                         |
| `max_trade_days`            | `10`                                                                    |
| `max_rows_per_source_domain`| `10`                                                                    |
| `max_network_calls_per_run` | `10`                                                                    |
| Fixture/staged fallback     | **Forbidden** for real-data pilot evidence                              |

## Approved micro-pilot requests

### Request 1 — baostock primary daily bar

| Field                   | Value                  |
| ----------------------- | ---------------------- |
| `source_id`             | `baostock`             |
| `data_domain`           | `cn_equity_daily_bar`  |
| `operation`             | `fetch_daily_bar`      |
| `symbols_or_indicators` | `sh.600519`            |
| `date_window`           | recent 10 trading days |
| `max_rows`              | `10`                   |

### Request 2 — akshare validation daily bar

| Field                   | Value                        |
| ----------------------- | ---------------------------- |
| `source_id`             | `akshare`                    |
| `data_domain`           | `cn_equity_daily_bar`        |
| `operation`             | `fetch_daily_bar_validation` |
| `symbols_or_indicators` | `sh.600519`                  |
| `date_window`           | recent 10 trading days       |
| `max_rows`              | `10`                         |

**Constraint:** validation-only; must not be promoted to sole Primary fact source.

### Request 3 — cninfo announcement metadata

| Field                   | Value                     |
| ----------------------- | ------------------------- |
| `source_id`             | `cninfo`                  |
| `data_domain`           | `cn_announcements`        |
| `operation`             | `fetch_announcement_index`|
| `symbols_or_indicators` | `sh.600519`               |
| `date_window`           | recent 14 calendar days   |
| `max_rows`              | `10`                      |

**Constraint:** metadata only; no PDF body fetch or announcement backfill.

## Explicitly not authorized

- `tdx_pytdx` live fetch (route preview only if needed elsewhere)
- `qmt_xtdata`, `qmt_xqshare`, `yahoo_finance`
- `fred` primary live access (`B2.5-O-05` remains deferred)
- `akshare` `macro_supplementary` as production macro primary
- full-market / full-history / backfill / reconcile
- production clean DB write
- production-live readiness claim

## Revocation

If revoked before Execute closeout, pilot state must be `PILOT_REDEFERRED` with registry note.
