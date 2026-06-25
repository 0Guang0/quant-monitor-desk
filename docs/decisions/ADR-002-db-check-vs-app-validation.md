# ADR-002: DB CHECK vs Application-Layer Validation

## Status

Accepted (2026-06-19)

## Context

DuckDB cannot safely `ALTER TABLE ADD CONSTRAINT` on applied tables. Round2 audit identified status fields (`fetch_log.status`, `manual_review_queue.status`, `source_conflict.reconcile_status`, `source_registry.source_type`) enforced only in Python.

## Decision

1. **Application layer** remains the primary gate: Pydantic models (`FetchResult`), `FetchLogWriter._validate_for_persist`, validators, and `SyncJobStateMachine` enforce business rules at write time.
2. **Migration 009** rebuilds affected tables with inline `CHECK` constraints as defense-in-depth against direct SQL or script bypass.
3. New enum values require both contract YAML / Python updates **and** a forward migration to extend CHECK lists.

## App-layer-only columns (R2-RISK-4 / R3F-MIG-02)

`manual_review_queue.priority` remains **application-layer only**. Writers such as
`SourceConflictValidator` supply known values (e.g. `HIGH`); the DB has **no CHECK**
on `priority` so future priority taxonomy can evolve without a migration per enum value.
See `docs/schema/MIGRATION_COVERAGE.md` §Round 3F routing.

## Consequences

- Invalid direct INSERTs fail at DB level in tests (`test_dbRejectsInvalidFetchStatus`).
- Schema migrations use table-rebuild pattern (see migration 007/009/012).
- `priority` invalid values are rejected in app code, not at DB CHECK (see
  `tests/test_round3f_migration_residuals.py`).
