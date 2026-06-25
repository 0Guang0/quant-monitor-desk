# wont-fix — AA-B3V-04 (MIGRATION_COVERAGE ↔ 009 doc cross-ref test)

> **Finding:** AA-B3V-04 — optional reinforcement test linking `MIGRATION_COVERAGE.md` narrative to migration 009 file  
> **Decision:** **CLOSED via wont-fix** (ponytail minimal — no new test)

## Negative rationale

1. **Existing coverage is sufficient:** `tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints` already asserts schema.sql CHECK constraints match migration 009 semantics (REG-01 closure evidence, PASS).
2. **Docs already reconciled:** `docs/schema/MIGRATION_COVERAGE.md` and `docs/schema/MIGRATION_008_PLAN.md` were updated in REG-01 to reflect 009 applied vs residual 008/deferred gaps (`execute-evidence/REG-01-matrix.txt`).
3. **Markdown cross-ref test adds no new signal:** A test that greps `MIGRATION_COVERAGE.md` for "009" would duplicate the contract test and the matrix research artifact (`research/migration-009-coverage-matrix.md`) without catching real drift (SQL vs schema is the authoritative check).
4. **Ponytail ceiling:** New doc-only test ≈ 30+ lines for string matching; upgrade path is coordinator registry close + existing schema contract test in CI.

## Closure test reference

- `uv run pytest tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints -q` → PASS
- `research/migration-009-coverage-matrix.md` — human/audit cross-check SSOT

## Status

**AA-B3V-04 → CLOSED** (wont-fix, not OPEN)
