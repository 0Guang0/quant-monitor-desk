# ADR-001: Ingestion Validation / Write Transaction Boundary

## Status

Accepted (2026-06-19)

## Context

Round2 Batch C/D requires that validation reports, conflict reports, and clean writes form an auditable evidence chain. `WriteManager` must not commit clean rows without a passing `validation_report_id`. Orchestrator `COMPLETED` status is set after the writer transaction closes.

## Decision

1. **Validation + conflict** run inside a single writer connection transaction before `WRITING`.
2. **Clean write** uses `WriteManager.write(..., own_transaction=False)` inside the same connection scope; `DbValidationGate` enforces `can_write_clean` on the validation report.
3. **Job status `COMPLETED`** is emitted in a separate transition after the write transaction commits, so status audit does not roll back persisted clean rows.
4. **Registry sync** (`SourceRegistry.sync_to_db`) does not open its own transaction; callers wrap multi-step bootstrap in explicit transactions when atomicity is required.

## Consequences

- Partial write + COMPLETED mismatch is avoided by ordering: write commit → then COMPLETED.
- Reconcile and backfill runners reuse the same validation/write pipelines as incremental jobs.
