# ADR-026: US equity trading calendar SSOT (R3H-07 CAL-US)

- **Status:** Accepted
- **Date:** 2026-06-29
- **Context:** US/global equity sources (`yahoo_finance`, `stooq`, `alpha_vantage`) still use natural-day windows (`window_kind: calendar_days`) and `fetch_window.recent_window_start(calendar_days=…)`. CN calendar closed @ R3H-03 (`cn_trading_calendar.py`). R3H-10 closed C2 SSOT so window semantics must be verifiable via `DataSourceService` fetch/evidence path. No new clean DDL in R3H-06 scope.

## Decision

1. **Authority module:** Add `backend/app/ops/data_health_profiles/us_trading_calendar.py` as QMD-owned L2 SSOT, mirroring `cn_trading_calendar.py` shape (`is_trading_day`, `get_trading_days`, `get_missing_trading_days`).
2. **Coverage:** NYSE/Nasdaq **combined** US equity holiday set as bounded `frozenset` for `2000-01-01` … `2030-12-31` (weekends + US federal market holidays). ponytail ceiling: beyond 2030 requires exchange-authoritative feed or ADR extension (same pattern as CN `CAL-CN-TAIL`).
3. **Window kind:** US equity bar domains (`us_equity_daily_bar`, related market_bar fetch plans) emit `window_kind: trading_sessions` in evidence bundles; span caps count **trading sessions**, not calendar days.
4. **Shared helper:** Extend `backend/app/datasources/fetch_window.py` with trading-session window helpers consumed by US fetch ports (not ops-only shim).
5. **Layer4 G4:** `MarketStructureBuilder` / US adapter path uses the **same** `us_trading_calendar` for non-trading-day rejection on `US_EQ` (bounded fixture rows; no full-market scan).
6. **Explicit exclusions:** `deribit`, `coingecko`, crypto domains remain `calendar_days` ponytail per `R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md` §CAL-US scope.

## Alternatives considered

| Alt                                               | Rejected because                                                    |
| ------------------------------------------------- | ------------------------------------------------------------------- |
| pandas_market_calendars / exchange API at runtime | New dependency + network; violates ponytail + offline replay-first  |
| DB table + migration                              | Out of scope unless Batch6 ADR; CN precedent is in-memory frozenset |
| Mon–Fri weekday proxy only                        | Fails CAL-US AC (Thanksgiving etc.); INDEX §2 negative test S07-04  |
| Per-source holiday tables                         | Violates SSOT; C3 + G4 must share one module                        |

## Consequences

- **Positive:** CAL-US closable; C3/G4 share one module; CN regression isolated to `cn_trading_calendar` tests.
- **Negative:** Holiday table maintenance ponytail to 2030; evidence contract tests from R3H-02 must flip from `calendar_days` → `trading_sessions` for US sources.
- **Wave 2 carry:** R3H-10 deferred reconcile/probe items unchanged (see ENTRY §2 Wave 2 承接表).

## Binding slices

- **S07-01** — data plane (`us_trading_calendar.py`)
- **S07-02** — C3 fetch ports + `window_kind`
- **S07-03** — G4 loader
- **S07-04** — holiday negative tests
