# Plan spec — R3-DCP-05

## Objective

Deliver Tier A incremental product sync for 11 sources with clean-table upsert and baostock product live wiring.

## Tech stack

Python 3.11+ · DuckDB · uv · pytest · existing DataSourceService / DataSyncOrchestrator stack.

## Commands

```bash
uv run pytest tests/test_baostock_incremental_e2e.py tests/test_fred_macro_incremental_e2e.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/wave4-r3-dcp-05-tier-a
```

## Project structure (additions)

```text
backend/app/db/migrations/015_dcp05_tier_a_clean.sql
backend/app/sync/incremental_source_registry.py
backend/app/ops/{us_treasury,bis,world_bank,cftc,cninfo,sec_edgar,alpha_vantage,deribit}_incremental_*.py
backend/app/ops/sandbox_clean_write/clean_write_targets.py  # extend
backend/app/cli/data_commands.py  # router + baostock live
tests/test_baostock_incremental_watermark.py
tests/test_fred_macro_incremental_e2e.py
tests/test_schema_migration.py
```

## Migration 015 sketch (Execute implements)

- `us_disclosure_clean` PK `accession_number`; columns mirror SEC evidence normalizer
- `crypto_derivative_clean` PK `(instrument_name, as_of_timestamp, record_type)`; deribit surface rows
- Matching `stg_*_smoke` tables for promote path

## Testing strategy

- TDD per slice: watermark unit → replay e2e clean write → idempotent repeat run
- Five-field docstrings on all new `test_*`
- Default CI: replay only; live smoke manual/`--run-network`

## Boundaries

**Always:** ADR-025 fail-closed service path; isolation DB for `--no-dry-run`  
**Never:** runtime `参考项目/**`; staging-only Done for any Tier A source; close B2.5-O-05

## Success criteria

活卡 §5 + 11/11 clean e2e + `uv run pytest -q` exit 0

## ASSUMPTIONS

- Canonical domain per source per ADR-028 table (one domain per source for Done).
- alpha_vantage Done domain = `us_equity_daily_bar` only.
- mootdx uses `cn_equity_daily_bar` despite validation_only registry posture (Tier A incremental demo).
