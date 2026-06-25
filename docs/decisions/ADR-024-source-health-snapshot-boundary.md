# ADR-024: source_health_snapshot Boundary (Batch 3F B3F-SH)

## Status

Accepted (2026-06-25) — Execute R3F-SH-01

## Context

`source_health_snapshot` is deferred in `MIGRATION_COVERAGE.md` (D2-P2-1). Batch 01 / DH2 read-only data health (`round3-readonly-data-health-v2`) must not create this table. Batch 6 source health needs a dedicated writer and isolated pytest path while **B3F-MIG** owns `backend/app/db/migrations/**` SQL.

## Decision

1. **DDL location:** `SourceHealthSnapshotWriter.ensure_schema()` embeds the table DDL from `docs/modules/data_sources.md` §5.8 for **isolated test DB only**. Production migration SQL remains **B3F-MIG** lock.
2. **Writer module:** `backend/app/ops/source_health_writer.py` is the only Batch6 persist entry for snapshot rows.
3. **DH2 boundary:** `backend/app/ops/data_health.py` exposes `DH2_FORBIDS_SNAPSHOT_DDL = True` and must not import the writer or emit `CREATE TABLE source_health_snapshot`.
4. **Rollup persist:** `persist_readiness_rollup()` lives in `source_health_writer.py`; callers pass an open DuckDB connection (non-DH2 orchestration path).

## Consequences

- SH-01 pytest can PASS without MIG migration files on this branch.
- SH-05 grep + constant guard prevents DH2 regression.
- MIG worktree merges migration SQL later; writer DDL string must stay aligned with merged migration.
