# Context closure — B3F-MIG migration residuals

## Upstream wiring

- `apply_migrations` → `012_migration_residuals.sql` → DuckDB schema
- `SourceRegistry.sync_to_db` → `source_registry.registry_generation` / `removed_from_yaml_at`
- `DataSyncOrchestrator.bootstrap` calls `sync_to_db` (impact LOW)
- `MIGRATION_COVERAGE.md` ↔ `test_round3f_migration_residuals.py` closure tests

## Deferred (main session)

- Registry RESOLVED rows for `D2-P3-1`, `A9-P3-01`, `A9-P2-01`, `R2-RISK-4` (proposed delta in closure report)
- `source_health_snapshot` migration (B3F-SH owner)

## Slice boundary

- allowed: `backend/app/db/migrations/012_*`, `source_registry.py` sync columns, `docs/schema/*`, ADR-002, tests
- forbidden: registry三件套 direct RESOLVED, production clean write, `source_health_snapshot` DDL
