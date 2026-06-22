# Migration 008 Plan — Remaining DB CHECK Constraints

> **Status:** planned · **Target:** Round 3 ops / DB hygiene  
> **Closes audit:** A9-P1-01, A9-P2-01, A9-P2-02, A9-P3-01

## Scope

DuckDB limits `ALTER TABLE ADD CHECK` on existing tables created in migration 004/005. Migration **007** already rebuilt `data_sync_job` / `job_event_log` with status CHECKs. Migration **008** will address remaining app-layer-only enums.

## Planned changes

> **Applied 009 / 010 (2026-06-22):** Status CHECK constraints landed in **009**; lineage NOT NULL rebuild in **010** with explicit `INSERT … SELECT` column list (ADV-A1-009). Remaining rows below are still **planned** for a future **008** rebuild pass.

| Table | Column(s) | Constraint | Strategy |
|-------|-----------|------------|----------|
| `fetch_log` | `status` | Enum CHECK | Rebuild table or new `_v2` + swap (same pattern as 007) |
| `source_registry` | `role`, `license_status` | Enum CHECK | Rebuild with explicit column list |
| `manual_review_queue` | `status`, `priority` | Enum CHECK | Rebuild |
| `source_conflict` | `reconcile_status` | `OPEN/UNRESOLVED/RESOLVED/N/A` | Rebuild or ADD if DuckDB allows |

## Non-goals (008)

- Cross-table FK (evaluate separately; DuckDB FK support limited)
- `source_health_snapshot` table (separate migration; D2-P2-1)
- Full `write_audit_log` design columns (incremental ADD COLUMN where possible)

## Implementation checklist

1. Draft `008_db_check_constraints.sql` with explicit `INSERT INTO … SELECT col1, col2, …` (no `SELECT *`).
2. Add negative tests: illegal enum inserts must fail.
3. Update `MIGRATION_COVERAGE.md` statuses from PARTIAL → DONE where applied.
4. Run `pytest tests/test_schema_migration.py` on fresh + upgraded DB.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest tests/test_schema_migration.py -q
.venv\Scripts\python.exe scripts/init_db.py
```

Cross-reference: `docs/schema/MIGRATION_COVERAGE.md`, `docs/AUDIT_DEFERRED_REGISTRY.md`.
