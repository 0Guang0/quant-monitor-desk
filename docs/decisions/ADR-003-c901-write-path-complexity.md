# ADR-003: C901 Complexity Ceiling on Write Path Hot Functions

## Status

Accepted (2026-07-01)

## Context

Round2 audit item `D3-P1-2` flagged mccabe complexity on:

- `SourceRegistry._validate_domain_roles`
- `WriteManager._execute_write`

Both sit on the ingestion write hot path with many domain-specific branches (fail-closed guards, mode routing, lineage hooks).

## Decision

1. **No refactor split in Wave 4 prep** — extracting helpers would scatter transaction-boundary logic without reducing real risk.
2. **Complexity is bounded by tests** — `tests/test_write_manager.py`, `tests/test_source_registry.py`, and contract drift tests lock behavior.
3. **Future split trigger** — if either function gains a fourth distinct write domain, extract domain handlers in a dedicated Batch 6 slice (`R3F-HYG`).

## Consequences

- `D3-P1-2` closed as **wont-fix by ADR** (not silent ignore).
- Ruff C901 may still report on these symbols; CI does not gate on C901 today.
- New branches in these functions require pytest coverage per `testing-guidelines`.
