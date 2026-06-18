# Database Guidelines

> DuckDB schema, migrations, and write-path rules (Round 0–2).

## Overview

- Single-writer model via `ConnectionManager.writer()` file lock.
- Migrations in `backend/app/db/migrations/*.sql`, applied by `apply_migrations()`.
- Design authority: `specs/schema/schema.sql`; migrations are incremental subsets.

## Migration Rules

1. Never modify applied migration files (checksum enforced).
2. Prefer inline CHECK on CREATE; use rebuild migration when ALTER CHECK unavailable.
3. Document application-layer-only constraints in migration header comments.

## Write Path

- Clean writes only through `WriteManager` with explicit `ValidationGate`.
- `DbValidationGate.assert_can_write_with(con, ...)` must be used inside write transactions.
- `write_audit_log` persists contract fields: `source_role`, `data_domain`, `conflict_report_id`, etc.

## Constraints

- `validation_report.status`, `data_sync_job.status`, `job_event_log` statuses: DB CHECK (migration 007+).
- `fetch_log` SUCCESS evidence: application layer (`FetchResult` + FetchLogWriter) per Batch C ledger.

## Testing

- `tests/test_schema_migration.py` — migration replay + version set.
- `tests/test_audit_fixes.py` — invalid sync status rejected, default WriteManager gate path.
