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

## Applied migration ladder (001–011)

| Version | File | Scope |
| ------- | ---- | ----- |
| 001–003 | foundation / registry hardening / resource guard | Core tables |
| 004–006 | ingestion sources / validation / sync | `fetch_log`, `source_registry`, sync jobs |
| 007 | `007_sync_constraints_audit` | Sync job + audit CHECK rebuild |
| 008 | `008_lineage_version_fields` | Lineage version columns |
| 009 | `009_status_check_constraints` | `fetch_log` / ingestion table **status enum CHECK** (rebuild `_v2` swap) |
| 010 | `010_lineage_not_null` | Lineage `rule_set_id` / `rule_version` NOT NULL (explicit-column rebuild) |
| 011 | `011_layer1_tables` | Layer 1 axis registry + snapshot tables |

Planned enum/CHECK closeout for remaining tables: `docs/schema/MIGRATION_008_PLAN.md` (narrative id **008**; applied status CHECK is **009** per `MIGRATION_COVERAGE.md`).

## Write Path

- Clean writes only through `WriteManager` with explicit `ValidationGate`.
- `DbValidationGate.assert_can_write_with(con, ...)` must be used inside write transactions.
- `write_audit_log` persists contract fields: `source_role`, `data_domain`, `conflict_report_id`, etc.

## Constraints

- `validation_report.status`, `data_sync_job.status`, `job_event_log` statuses: DB CHECK (migration 007+).
- `fetch_log.status` enum: DB CHECK after migration **009** (`009_status_check_constraints`).
- `fetch_log` SUCCESS evidence (staging row existence, raw path sanity): still **application layer** (`FetchResult` + `FetchLogWriter._validate_for_persist`) per Batch C ledger — DB CHECK does not replace evidence guards.

## Layer 1 axis snapshots (Round 3 Batch 2)

- Migration `011_layer1_tables.sql`: `axis_registry`, `axis_feature_snapshot`, `axis_interpretation_snapshot`, `axis_snapshot_lineage`, and related registry tables.
- Clean writes only through `Layer1SnapshotWriter` (`backend/app/layer1_axes/lineage.py`) → `WriteManager` with `validation_report_id`.
- `guard_layer2_writeback()` lives in `lineage.py` and rejects Layer 2 writeback into Layer 1 tables.
- Lineage completeness is enforced via `LINEAGE_REQUIRED_FIELDS` in `SnapshotLineageBuilder.build()`.

## Testing

- `tests/test_schema_migration.py` — migration replay + version set (expects 001–011).
- `tests/test_audit_fixes.py` — invalid sync status rejected, default WriteManager gate path.
- `tests/test_layer1_axis_loader.py` / `tests/test_layer1_interpretation.py` — Layer 1 loader, features, interpretation, lineage, WriteManager integration.
- `scripts/init_db.py` exposes `main(argv: list[str] | None = None)` so tests call `main([])`; CLI uses default `sys.argv`.
