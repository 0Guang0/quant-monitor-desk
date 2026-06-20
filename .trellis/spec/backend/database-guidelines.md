# Database Guidelines

> DuckDB schema, migrations, and write-path rules (Round 0–3).

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

## Layer 1 axis snapshots (Round 3 Batch 2)

- Migration `011_layer1_tables.sql`: `axis_registry`, `axis_feature_snapshot`, `axis_interpretation_snapshot`, `axis_snapshot_lineage`, and related registry tables.
- Clean writes only through `Layer1SnapshotWriter` (`backend/app/layer1_axes/lineage.py`) → `WriteManager` with `validation_report_id`.
- `guard_layer2_writeback()` lives in `lineage.py` and rejects Layer 2 writeback into Layer 1 tables.
- Lineage completeness is enforced via `LINEAGE_REQUIRED_FIELDS` in `SnapshotLineageBuilder.build()`.

## Testing

- `tests/test_schema_migration.py` — migration replay + version set.
- `tests/test_audit_fixes.py` — invalid sync status rejected, default WriteManager gate path.
- `tests/test_layer1_axis_loader.py` / `tests/test_layer1_interpretation.py` — Layer 1 loader, features, interpretation, lineage, WriteManager integration.
- `scripts/init_db.py` exposes `main(argv: list[str] | None = None)` so tests call `main([])`; CLI uses default `sys.argv`.
