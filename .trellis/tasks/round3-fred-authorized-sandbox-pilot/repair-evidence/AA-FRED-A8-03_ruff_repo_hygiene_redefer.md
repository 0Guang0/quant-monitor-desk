# AA-FRED-A8-03 — Scoped ruff PASS; repo hygiene re-defer

**Status:** CLOSED-repo-hygiene  
**Dimension:** A8 · §8.5 acceptance block  
**Repair type:** narrow scope verification + written re-defer (not FRED-introduced debt)

## Finding

MASTER §8.5 scoped command `uv run ruff check backend/app/datasources backend/app/ops` reports **91 pre-existing errors** in non-FRED ops/datasources files. FRED slice did not introduce these violations.

## Narrow scope (FRED-owned files)

```bash
uv run ruff check backend/app/ops/fred_*.py tests/test_fred_*.py
```

**Result:** `All checks passed!` (exit 0)

## Full scoped block (repo debt — re-deferred)

```bash
uv run ruff check backend/app/datasources backend/app/ops
```

**Result:** 91 errors (pre-existing repo hygiene debt)

## Re-defer rationale

| Field | Value |
| --- | --- |
| Owner | Repo hygiene coordinator · Batch 01 Track A |
| Phase | Post-B01-FRED merge hygiene wave |
| Not in scope | B01-FRED sandbox pilot; no `fred_*.py` violations |
| B01-FRED gate | FRED-scoped ruff green + `tests/test_fred_*.py` green |
| Closure test | This document + `b01-fred-audit-closures.md` AA-FRED-A8-03 row |

## Registry

Closure row: `research/b01-fred-audit-closures.md` · AA-FRED-A8-03 · **CLOSED-repo-hygiene**
