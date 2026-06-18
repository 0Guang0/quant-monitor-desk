# Quality Guidelines

> Code quality standards for backend development (Round 0–2 baseline).

## Overview

- Python 3.11+, `ruff check` + `ruff format --check` must pass before merge.
- Full pytest suite must pass with project basetemp: `python -m pytest -q`.
- Backend coverage gate: **85%** (`pyproject.toml`).
- Production gate: `python scripts/production_gate.py`.

## Forbidden Patterns

- Direct clean-table writes outside `WriteManager`.
- Production use of `StubValidationGate`.
- Adapter imports of `WriteManager`.
- Broad `except Exception` without rollback/audit justification.

## Required Patterns

- Staging → validator → `DbValidationGate` → `WriteManager` for clean writes.
- Explicit `FetchPort` injection in production adapter factory.
- ResourceGuard check before heavy FETCHING jobs.
- Migration idempotency via `schema_version` checksum verification.

## Testing Requirements

- RED→GREEN for new behavior; assert business outcomes (row counts, statuses, audit rows).
- Use tmp_path / `.audit-sandbox` basetemp; do not rely on system Temp on Windows.
- Integration tests use real DuckDB + migrations, not mocked business rules.

## Code Review Checklist

- [ ] Ruff lint + format pass
- [ ] Pytest pass (full suite)
- [ ] Write path uses ValidationGate on same connection when in transaction
- [ ] New migrations include CHECK constraints where contract enumerates statuses
- [ ] Deferred scope documented in `docs/AUDIT_DEFERRED_REGISTRY.md` if not implemented
