# ADR-009：Tier A clean 域扩展（migration 015）

**Status:** Accepted (Plan freeze)  
**Date:** 2026-07-02  
**Context:** User mandated **11/11 Tier A sources** must complete incremental sync with **clean table upsert** (not staging-only). Current R3H-06 clean targets (`013_clean_domain_tables.sql`) only cover bar (`security_bar_1d`), CN metadata (`cn_announcement_clean`), and macro (`axis_observation`). `sec_edgar` and `deribit` lack clean targets; several official-macro domains are not registered in `resolve_clean_write_target`.

## Decision

1. Add **migration 015** with:
   - `us_disclosure_clean` + `stg_us_disclosure_smoke` — SEC filings / Form 4 (`sec_edgar`)
   - `crypto_derivative_clean` + `stg_crypto_derivative_smoke` — Deribit options surface / term structure snapshots
2. Extend `clean_write_targets.py` domain routing (no new clean tables beyond 015):
   - **BAR_DOMAINS** += `us_equity_daily_bar`, `etf_daily_bar`, `fx_daily_bar`, `commodity_daily_bar` → `security_bar_1d`
   - **MACRO_DOMAINS** alias += `us_treasury_yield_curve`, `inflation_expectation`, `central_bank_policy`, `credit_gap`, `development_indicator`, `global_macro_reference`, `cot_positioning` → `axis_observation`
3. **Canonical incremental domain per Tier A source** (one row per source for DCP-05 Done):

| source_id     | canonical_domain        | clean_table             |
| ------------- | ----------------------- | ----------------------- |
| baostock      | cn_equity_daily_bar     | security_bar_1d         |
| mootdx        | cn_equity_daily_bar     | security_bar_1d         |
| fred          | macro_series            | axis_observation        |
| us_treasury   | us_treasury_yield_curve | axis_observation        |
| bis           | central_bank_policy     | axis_observation        |
| world_bank    | development_indicator   | axis_observation        |
| cftc_cot      | cot_positioning         | axis_observation        |
| cninfo        | cn_announcements        | cn_announcement_clean   |
| sec_edgar     | us_filings              | us_disclosure_clean     |
| alpha_vantage | us_equity_daily_bar     | security_bar_1d         |
| deribit       | crypto_options_surface  | crypto_derivative_clean |

4. Watermark readers: bar → `sync/watermark.py`; macro → `ops/*_incremental_watermark.py` (fred precedent); metadata → `publish_timestamp` on `cn_announcement_clean`; US disclosure → `filing_date` on `us_disclosure_clean`; crypto → `as_of_timestamp` on `crypto_derivative_clean`.

## Alternatives considered

- **Staging-only for sec_edgar/deribit:** Rejected per user 2026-07-02.
- **Single generic `vendor_clean` JSON table:** Rejected — breaks R3H-06 typed clean contracts and DQ profiles.
- **Map deribit to axis_observation:** Rejected — options surface rows are not scalar macro observations; dedicated table preserves domain semantics.

## Consequences

- DCP-05 **requires migration** → not pure Phase 8D debt-lite; Plan v4.1 complex track.
- `docs/schema/MIGRATION_COVERAGE.md` and `test_migration_coverage` must be updated in slice S00.
- DCP-06 can consume Tier A clean inputs once all 11 e2e tests green.
- Additional alpha_vantage domains (option chain, macro_series) remain **out of DCP-05** canonical row; future waves may add second domains per source.
