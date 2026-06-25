# Migration 008 Plan — Remaining DB CHECK Constraints

> **Status:** partially superseded by **009** (2026-06-22); **012** closed Round 3F residuals (2026-06-25)  
> **Target:** Round 3F / future hygiene for residual gaps  
> **Closes audit:** A9-P1-01 (subset), A9-P2-01 (subset), A9-P2-02, A9-P3-01 (subset)

## Scope

DuckDB limits `ALTER TABLE ADD CHECK` on existing tables created in migration 004/005. Migration **007** rebuilt `data_sync_job` / `job_event_log` with status CHECKs. Migration **009** applied status/enum CHECKs on ingestion tables (see matrix below). Migration **008** (if retained) covers **remaining** app-layer-only enums and explicit-column rebuilds.

## Applied in migration 009 (2026-06-22)

| Table | Column(s) | Constraint | Strategy in 009 |
|-------|-----------|------------|-----------------|
| `fetch_log` | `status` | Enum CHECK | `fetch_log_v2` rebuild + `SELECT *` (A9-P3-01 residual) |
| `source_registry` | `source_type`, `license_type` | Enum CHECK | Explicit column list rebuild |
| `manual_review_queue` | `status`, `source_object_type` | Enum CHECK | `SELECT *` rebuild (A9-P3-01 residual) |
| `source_conflict` | `severity`, `reconcile_status` | Enum CHECK | Explicit column list rebuild |

**Evidence:** `backend/app/db/migrations/009_status_check_constraints.sql`; `tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints`.

## Still planned (future 008 or Round 3F)

| Table | Column(s) | Constraint | Notes |
|-------|-----------|------------|-------|
| `source_registry` | `role`, `license_status` | Enum CHECK | Not in `schema.sql` design contract today |
| `manual_review_queue` | `priority` | Enum CHECK | **Closed Round 3F:** app-layer by design (R2-RISK-4); see ADR-002 |
| `fetch_log` | rebuild hygiene | Explicit `INSERT … SELECT` | **Closed Round 3F:** migration **012** |
| `manual_review_queue` | rebuild hygiene | Explicit `INSERT … SELECT` | **Closed Round 3F:** migration **012** |
| `source_registry` | `registry_generation`, `removed_from_yaml_at` | ADD COLUMN | **Closed Round 3F:** migration **012** (D2-P3-1) |

## Non-goals (008)

- Cross-table FK (evaluate separately; DuckDB FK support limited)
- `source_health_snapshot` table (separate migration; D2-P2-1)
- Full `write_audit_log` design columns (incremental ADD COLUMN where possible)
- Re-applying CHECKs already landed in **009** (no duplicate rebuild)

## Implementation checklist

1. Draft `008_db_check_constraints.sql` with explicit `INSERT INTO … SELECT col1, col2, …` (no `SELECT *`) for residual tables only.
2. Add negative tests: illegal enum inserts must fail where DB CHECK added.
3. Update `MIGRATION_COVERAGE.md` statuses from PARTIAL → DONE where applied.
4. Run `pytest tests/test_schema_migration.py` on fresh + upgraded DB.

## Verification

```powershell
.venv\Scripts\python.exe -m pytest tests/test_schema_migration.py -q
.venv\Scripts\python.exe scripts/init_db.py
```

Cross-reference: `docs/schema/MIGRATION_COVERAGE.md`, `docs/AUDIT_DEFERRED_REGISTRY.md`.
