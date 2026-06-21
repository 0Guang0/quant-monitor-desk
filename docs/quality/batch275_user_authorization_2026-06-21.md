# Batch 2.75 User Authorization — Controlled Live Pilot

> Status: user-approved authorization record for Round 3 Batch 2.75 (`018B` §3.1).  
> This file is **authorization evidence only**; it does not enable network fetch or production DB mutation by itself. Execute must still pass fail-closed gates in `LivePilotRequest` and policy tests.

## Authorization scope

| Field             | Value                                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------------- |
| Batch             | Round 3 Batch 2.75                                                                                  |
| Task card         | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`              |
| Policy            | `docs/quality/production_live_pilot_policy.md`                                                      |
| Approved by       | User (project owner)                                                                                |
| Approved on       | 2026-06-21                                                                                          |
| Sprint constraint | **No** ingestion split R2b–R2d in the same sprint (`layer1_ingestion_refactor_rollback_plan.md` §6) |

## Global defaults (every micro-pilot request)

| Control                 | Approved value                                                                                                          |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `dry_run`               | `true` (route preview phases); live fetch steps set `dry_run=false` only inside sandbox orchestration after route READY |
| `raw_only`              | `true` for first live pass                                                                                              |
| `write_target`          | `sandbox` under `.audit-sandbox/batch275-live-pilot/`                                                                   |
| `allow_clean_write`     | `false` (default plan has **no** clean write)                                                                           |
| Production DB           | `data/duckdb/quant_monitor.duckdb` — **read-only inspect only**; no mutation                                            |
| Total row cap           | `<= 100` (recommended actual `<= 40`)                                                                                   |
| Fixture/staged fallback | **Forbidden** for live pilot evidence                                                                                   |

## Approved micro-pilot requests

### Request 1 — baostock primary daily bar

| Field                   | Value                 |
| ----------------------- | --------------------- |
| `source_id`             | `baostock`            |
| `data_domain`           | `cn_equity_daily_bar` |
| `operation`             | `fetch_daily_bar`     |
| `symbols_or_indicators` | `sh.600519`           |
| `date_window`           | recent 5 trading days |
| `max_rows`              | `10`                  |

### Request 2 — akshare validation daily bar

| Field                   | Value                        |
| ----------------------- | ---------------------------- |
| `source_id`             | `akshare`                    |
| `data_domain`           | `cn_equity_daily_bar`        |
| `operation`             | `fetch_daily_bar_validation` |
| `symbols_or_indicators` | `sh.600519`                  |
| `date_window`           | recent 5 trading days        |
| `max_rows`              | `10`                         |

**Constraint:** validation-only; must not be silently promoted to Primary.

### Request 3 — akshare macro supplementary (ENV-E1-DGS10 shape)

| Field                   | Value                  |
| ----------------------- | ---------------------- |
| `source_id`             | `akshare`              |
| `data_domain`           | `macro_supplementary`  |
| `operation`             | `fetch_macro_series`   |
| `symbols_or_indicators` | `DGS10`                |
| `date_window`           | recent 7 calendar days |
| `max_rows`              | `20`                   |

**Constraint:** success does **not** close FRED primary access for `ENV-E1-DGS10`.

## Explicitly not authorized

- `fred` as `source_id` (not registered; do not bypass registry gates)
- `qmt_xtdata`, `qmt_xqshare`, `yahoo_finance` unless separately authorized in a future amendment
- `cninfo` announcement pilot (optional; not in default three-request set)
- full-market / full-history / backfill / reconcile
- production clean DB write
- general-purpose `qmd data` production CLI

## Revocation

If this authorization is revoked before Execute Phase 3, closeout must be `PILOT_REDEFERRED` with registry update.
