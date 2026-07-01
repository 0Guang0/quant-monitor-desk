# AA-FRED-A8-01 — MALFORMED health branch closure

**Status:** CLOSED  
**Dimension:** A8 · test-gap  
**Repair type:** test addition (root-cause, not stub)

## Finding

`fred_evidence_validator.validate_fred_evidence_health` implements `MALFORMED_ROW`, `MALFORMED_VALUE`, `MALFORMED_DATE`, and `MISSING_ROWS` branches, but Audit A8 found no per-code pytest binding (AA-FRED-A8-01).

## Fix

Added `test_fredEvidenceHealth_malformedBranches_failExplicitly` in `tests/test_fred_sandbox_pilot.py`:

| Mutation                         | Expected code     |
| -------------------------------- | ----------------- |
| `rows: []`                       | `MISSING_ROWS`    |
| row missing `observation_date`   | `MALFORMED_ROW`   |
| row missing `value`              | `MALFORMED_VALUE` |
| `observation_date: "not-a-date"` | `MALFORMED_DATE`  |

## Verification

```bash
uv run pytest tests/test_fred_sandbox_pilot.py -k "malformedBranches or EvidenceHealth" -q
```

Result: all passed.

## Registry

Closure row: `research/b01-fred-audit-closures.md` · AA-FRED-A8-01 · **CLOSED**
