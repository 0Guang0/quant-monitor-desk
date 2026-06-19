# ADR-002: DB CHECK vs Application-Layer Validation

## Status

Accepted (2026-06-19)

## Context

DuckDB cannot safely `ALTER TABLE ADD CONSTRAINT` on applied tables. Round2 audit identified status fields (`fetch_log.status`, `manual_review_queue.status`, `source_conflict.reconcile_status`, `source_registry.source_type`) enforced only in Python.

## Decision

1. **Application layer** remains the primary gate: Pydantic models (`FetchResult`), `FetchLogWriter._validate_for_persist`, validators, and `SyncJobStateMachine` enforce business rules at write time.
2. **Migration 009** rebuilds affected tables with inline `CHECK` constraints as defense-in-depth against direct SQL or script bypass.
3. New enum values require both contract YAML / Python updates **and** a forward migration to extend CHECK lists.

## Consequences

- Invalid direct INSERTs fail at DB level in tests (`test_dbRejectsInvalidFetchStatus`).
- Schema migrations use table-rebuild pattern (see migration 007/009).
