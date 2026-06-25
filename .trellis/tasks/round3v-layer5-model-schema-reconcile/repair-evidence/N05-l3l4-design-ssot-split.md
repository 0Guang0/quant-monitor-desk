# N05 — L3/L4 design SSOT split (schema.sql vs module doc)

**Status:** CLOSED (documented in matrix)

**Finding:** `BLK-L5R-03` — L3/L4 tables not centralized in `specs/schema/schema.sql`.

**Resolution:** Matrix `design_ssot` column records split; `MIGRATION_COVERAGE.md` L3/L4 sections aligned 2026-06-25.

**Matrix rows:**

- `research/l5-reconcile-matrix.md` §3.1 — L3 tables, note: schema.sql does not define L3 tables
- `research/l5-reconcile-matrix.md` §3.2 — L4 tables, same SSOT split
- `research/model-schema-table-reconcile.md` — table-level reconcile

**Closure test:** `test_migrationCoverage_l3DesignedTables_haveNoMigration` / `l4` — no migration DDL for designed tables.
