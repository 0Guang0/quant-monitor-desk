# Plan task breakdown — R3-DCP-05

## Overview

Wave 4 DCP-05 extends incremental product sync to all 11 Tier A sources with mandatory clean-table upsert (ADR-028 / migration 015). Builds on Wave 3 baostock/fred templates; fixes baostock product live mock hardcode.

## Architecture decisions

1. **ADR-028** — two new clean tables + domain alias expansion (see `docs/decisions/ADR-028-*.md`).
2. **incremental_source_registry** — table-driven canonical domain per source (avoid 11 copy-paste CLI branches).
3. **Macro family** — copy `fred_incremental_run` pattern per source into `ops/<source>_incremental_*.py` (ponytail: extract shared helper in S00 if 3rd copy hurts).
4. **Live default** — replay; live only with `QMD_ALLOW_LIVE_FETCH=1` + isolation DB guards.

## Task list

| ID      | Description                       | AC                            | Verification               | Dependencies | Files                                                       | Scope  |
| ------- | --------------------------------- | ----------------------------- | -------------------------- | ------------ | ----------------------------------------------------------- | ------ |
| T00     | Schema + registry                 | 015 green; 11 domain resolve  | migration + registry tests | —            | migrations/015\*, clean_write_targets, incremental_registry | M      |
| T01     | Baostock live                     | ACC-BAOSTOCK-NO-LIVE          | baostock sync tests        | T00          | data_commands, baostock_port                                | S      |
| T02–T06 | Macro ×5 + fred                   | 5 e2e clean                   | per-source pytest          | T00          | ops/_*incremental*_                                         | M each |
| T07–T08 | cninfo + mootdx                   | 2 e2e clean                   | pytest                     | T00          | ops, ports                                                  | M each |
| T09–T11 | sec_edgar, alpha_vantage, deribit | 3 e2e new clean tables        | pytest                     | T00          | ops, adapters, migrations                                   | M–L    |
| T12     | CLI router                        | 11-source dry-run             | router test                | T01–T11      | data_commands, main                                         | M      |
| T13     | Registry/docs                     | loop_maintain; eastmoney SSOT | scripts + docs             | T12          | registry yaml, ops doc                                      | S      |

## Checkpoints

- **CP1:** S00 merge — migration + registry tests green
- **CP2:** S01 + S02 — baostock live + fred regress
- **CP3:** All 11 e2e clean tests green
- **CP4:** Full pytest + plan-freeze validation

## Risks

| Risk                               | Mitigation                                                        |
| ---------------------------------- | ----------------------------------------------------------------- |
| `data_commands.py` merge conflicts | S00 owns router skeleton; source slices add rows only             |
| Migration drift                    | Single 015 file; MIGRATION_COVERAGE update in S00                 |
| Macro ops duplication              | Shared `macro_incremental_base.py` after S04 if needed (ponytail) |
| Live CI flake                      | Default replay; `--run-network` optional nightly (DCP-09)         |

## Open questions

- None blocking Plan freeze (user confirmed 11/11 clean).
