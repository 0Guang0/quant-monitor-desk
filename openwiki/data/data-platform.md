# Data Platform

Quant Monitor Desk stores structured state in DuckDB, raw/audit evidence in local files, and long or partitionable history in parquet when needed. `docs/architecture/04_data_architecture.md` describes the intended lifecycle as raw/file lake -> staging -> clean -> snapshot -> API/report/agent context, with audit logs alongside every path.

## Storage layout

Runtime data is under `data/` by default, from `DATA_ROOT` in `backend/app/config.py`. The default can be overridden by `QMD_DATA_ROOT`; empty values fall back to `<repo>/data`. Important runtime subdirectories observed in the repository include:

- `data/duckdb/`: local DuckDB database path.
- `data/raw/`: raw fetched data and replayable evidence.
- `data/parquet/`: parquet exports or historical partitions.
- `data/cache/`: temporary cache.
- `data/logs/`, `data/audit/`, `data/reports/`: local operational artifacts.

Configuration roots default to `configs/`, with contracts and specs in `specs/`. Do not treat `docs/` or `specs/` as runtime code locations.

## Schema and migrations

The schema contract is `specs/schema/schema.sql`. It includes foundational tables such as:

- `schema_version`
- `source_registry`
- `file_registry`
- `data_sync_job`
- `job_event_log`
- `validation_report`
- `data_quality_log`
- `source_conflict`
- `write_audit_log`
- `resource_guard_log`

Applied implementation migrations live in `backend/app/db/migrations/`, with files currently numbered `001_foundation.sql` through `015_dcp05_tier_a_clean.sql`. `backend/app/db/migrate.py` applies pending migrations in filename order inside transactions, records checksums in `schema_version`, and raises `MigrationChecksumError` if an applied migration file no longer matches its stored checksum.

## Validation and write boundary

Clean writes should flow through `WriteManager` in `backend/app/db/write_manager.py`. It requires an explicit validation gate, reads allowed modes from `specs/contracts/write_contract.yaml`, validates target/staging table identifiers, verifies staging shape and primary-key uniqueness for relevant modes, and writes to `write_audit_log` whether the result succeeds or fails. Errors are redacted before audit logging through `backend/app/util/error_redaction.py`.

The write path is intentionally separate from datasource fetching. CI enforces this boundary with a workflow step that blocks `WriteManager` imports under `backend/app/datasources/` in `.github/workflows/ci.yml`.

## Data quality and conflict handling

`validation_report`, `data_quality_log`, and `source_conflict` are separate concepts:

- Data quality checks whether one dataset is internally usable: required fields, nulls, stale data, schema shape, duplicates, and similar rules.
- Source conflict checks whether multiple sources disagree on the same fact beyond tolerance.
- Severe conflict should block clean writes and move to reconcile/manual review instead of silently overwriting.

Source conflict code and contracts are under `backend/app/validators/`, `backend/app/validation/`, and `specs/contracts/`. Tests such as `tests/test_data_quality_validator.py`, `tests/test_source_conflict_validator.py`, and `tests/test_write_manager.py` cover this boundary.

## Resource guard

`backend/app/core/resource_guard.py` evaluates memory, disk, project size, cache size, process RSS, DuckDB temp size, and profile thresholds. Decisions are `OK`, `WARN`, `PAUSE`, and `HARD_STOP`. Runtime thresholds come from `configs/resource_limits.yaml`, while contract expectations also exist in `specs/contracts/resource_limits.yaml`. The default profile is `eco`.

`DataSourceService` and `DataSyncOrchestrator` both check `ResourceGuard` before heavy fetch/write transitions. A paused or hard-stopped guard should produce auditable blocked state rather than partial mutation.

## Change guidance

- For schema changes, update migrations, schema contracts, and tests together. Never edit an already-applied migration casually because checksum verification can fail existing DBs.
- For new clean writes, use `WriteManager` plus a real validation gate. Do not write clean tables from datasources.
- For new tables, add or update contract tests and migration coverage tests.
- For data-source fallback, include route/audit evidence; silent switching is forbidden.
- For local testing, prefer an isolated `QMD_DATA_ROOT` under `.audit-sandbox` when exercising live/sandbox acceptance paths.

## Source references

- `specs/schema/schema.sql`
- `backend/app/db/migrations/`
- `backend/app/db/migrate.py`
- `backend/app/db/write_manager.py`
- `backend/app/db/validation_gate.py`
- `backend/app/core/resource_guard.py`
- `configs/resource_limits.yaml`
- `docs/architecture/04_data_architecture.md`
