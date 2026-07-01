# N02 — authority_graph test_migration_coverage mapping

**Status:** CLOSED

**Action:** `specs/context/authority_graph.yaml` → `db_platform.tests` adds `tests/test_migration_coverage.py`; `db_platform.docs` adds `docs/schema/MIGRATION_COVERAGE.md`.

**Verification:**

```text
uv run python scripts/loop_maintain.py --fix  → OK
```

**Note:** `loop_maintain` checks backend package mapping; test pointer is explicit graph entry per `DEBT.plan.md` QC-L5R-04 / Execute boot.
