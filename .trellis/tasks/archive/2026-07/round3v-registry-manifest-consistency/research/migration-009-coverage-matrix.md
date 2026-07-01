# Research: migration 009 coverage matrix

- **Query**: VR-REG-001 — reconcile migration 009 CHECK coverage vs schema.sql, MIGRATION_COVERAGE.md, registries
- **Scope**: internal (GitNexus `query` + file reads; codebase-memory MCP project not indexed for this worktree — used GitNexus + direct reads)
- **Date**: 2026-06-25

## Findings

### Files Found

| File Path                                                    | Description                                                                      |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `backend/app/db/migrations/009_status_check_constraints.sql` | Migration 009 — rebuilds 4 tables with inline CHECK                              |
| `specs/schema/schema.sql`                                    | Design contract; CHECK on same status/enum columns                               |
| `docs/schema/MIGRATION_COVERAGE.md`                          | Coverage matrix — **stale PARTIAL** rows for 009-covered tables                  |
| `docs/schema/MIGRATION_008_PLAN.md`                          | Notes 009 applied status CHECKs; still lists some rows as planned 008            |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                            | A9-P1-01 / A9-P2-01 / A9-P2-02 still → migration 008                             |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                         | Same A9-\* rows DEFERRED to migration 008                                        |
| `tests/test_schema_contract.py`                              | `test_schemaContract_includesStatusCheckConstraints` — schema.sql CHECK presence |
| `tests/test_round3_audit_registry_alignment.py`              | `test_post14DatabaseGuidelines_listsMigration009StatusCheck`                     |

### Migration 009 vs schema.sql (column-level)

| Table                 | Column / concern     | `schema.sql` CHECK | `009_status_check_constraints.sql` | Gap                                     |
| --------------------- | -------------------- | ------------------ | ---------------------------------- | --------------------------------------- |
| `fetch_log`           | `status`             | Yes                | Yes (`fetch_log_v2` rebuild)       | None for CHECK                          |
| `source_registry`     | `source_type`        | Yes                | Yes                                | None                                    |
| `source_registry`     | `license_type`       | Yes                | Yes                                | None                                    |
| `manual_review_queue` | `source_object_type` | Yes                | Yes                                | None                                    |
| `manual_review_queue` | `status`             | Yes                | Yes                                | None                                    |
| `manual_review_queue` | `priority`           | **No**             | **No**                             | Remains app-layer (R2-RISK-4)           |
| `source_conflict`     | `severity`           | Yes                | Yes                                | None                                    |
| `source_conflict`     | `reconcile_status`   | Yes                | Yes                                | None                                    |
| `data_sync_job`       | `status`             | Yes                | **007** (not 009)                  | MIGRATION_COVERAGE already DONE via 007 |

### INSERT strategy (A9-P3-01)

| Table in 009          | INSERT pattern       | A9-P3-01 status |
| --------------------- | -------------------- | --------------- |
| `source_registry`     | Explicit column list | Closed in 009   |
| `source_conflict`     | Explicit column list | Closed in 009   |
| `fetch_log`           | `SELECT *`           | **Still open**  |
| `manual_review_queue` | `SELECT *`           | **Still open**  |

### Stale documentation / registry drift

- `MIGRATION_COVERAGE.md` lines 20–30 still mark `source_registry`, `fetch_log`, `source_conflict`, `manual_review_queue` as **PARTIAL** with “CHECK deferred” — contradicts 009 file on disk.
- `AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md` route A9-P1-01, A9-P2-01, A9-P2-02 to **migration 008** — 009 already landed most CHECKs (2026-06-22 per MIGRATION_008_PLAN header).
- `MIGRATION_008_PLAN.md` §Planned changes still lists `fetch_log.status`, `source_conflict.reconcile_status` as future 008 — header says applied in 009; body table not fully reconciled.

### Distinction: file vs production DB

- This research confirms **migration file + schema.sql** alignment only.
- **No** read-only production DuckDB inspect was run (forbidden without explicit evidence path).
- Execute must not claim “production has applied 009” without `db-inspect` / migration version evidence.

### GitNexus cross-check

- `query("migration 009 status check constraints MIGRATION_COVERAGE")` surfaced `test_schemaContract_includesStatusCheckConstraints`, `check_docs_specs_indexed.check_migration_map_coverage`, `test_post14DatabaseGuidelines_listsMigration009StatusCheck` — consistent with manual matrix above.

### Related Specs

- `.trellis/spec/backend/database-guidelines.md` — lists `009_status_check_constraints` (enforced by `test_post14DatabaseGuidelines_listsMigration009StatusCheck`)
- `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_05_migration_registry_and_manifest_consistency.md` — VR-REG-001 AC

## Caveats / Not Found

- No dedicated pytest asserting `MIGRATION_COVERAGE.md` rows match migration 009 (only schema contract + database-guidelines tokens). Execute may add doc-level test or extend existing registry alignment test — **only if** test purpose stays “doc/registry consistency”, not weakening.
- `tests/test_migration_coverage.py` referenced by B3V-L5R card **not present** on this branch (L5R scope, not REG).
