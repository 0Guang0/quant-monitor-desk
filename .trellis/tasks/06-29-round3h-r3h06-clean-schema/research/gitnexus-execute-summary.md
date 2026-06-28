# GitNexus Execute Summary — R3H-06

> Generated: 2026-06-29 · Boot Phase 0a

## Query

**search:** `sandbox clean write promote staging security_bar market_bar_clean`

Top processes: `capture_raw_and_staging_evidence` (staged_pilot.py) — rehearsal/promote 与 staging 证据链相关。

## Impact (upstream)

| Symbol                         | File                        | Result                                                                                  |
| ------------------------------ | --------------------------- | --------------------------------------------------------------------------------------- |
| `populate_staging_from_bundle` | rehearsal_loader.py         | Index miss — manual grep: callers `limited_production_entry`, `rehearsal_runner`, tests |
| `_write_bundle_to_production`  | limited_production_entry.py | Index miss — actual symbol `_promote_bundle_to_db` region ~L520                         |
| `StagingRow`                   | rehearsal_loader.py         | Index miss — used by staging_rows_from_bundle, tests                                    |

**Manual blast radius (grep):**

- `populate_staging_from_bundle` → `limited_production_entry.py`, `rehearsal_runner.py`, `test_round3g_*`, `live_evidence_bridge`
- `StagingRow` / `staging_rows_from_bundle` → rehearsal_loader tests, limited production promote tests
- `limited_production_entry` WriteRequest ~L560–570: **HIGH** — hardcoded `append_only`, `market_bar_clean`, PK 缺 `adjustment_type`

**Risk:** MEDIUM — promote 路径集中；migration 新增表影响 `apply_migrations` 全库测试。

## Planned edits

| Step    | Symbols / files                                                       |
| ------- | --------------------------------------------------------------------- |
| 9.1–9.2 | New `013_clean_domain_tables.sql`, `schema.sql`                       |
| 9.3     | `014_stg_bar_ohlcv.sql`, `StagingRow`, `populate_staging_from_bundle` |
| 9.4     | `populate_disclosure_from_bundle`                                     |
| 9.5     | New `clean_write_targets.py`, `limited_production_entry.py`           |
| 9.6     | Remove `_cninfo_staging_rows`                                         |
| 9.8     | Fixtures/scripts/tests `market_bar_clean` → `security_bar_1d`         |
