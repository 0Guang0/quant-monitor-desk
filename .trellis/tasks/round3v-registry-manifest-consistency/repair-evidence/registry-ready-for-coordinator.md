# Registry ready for coordinator — B3V-REG (AA-B3V-01)

> **Branch:** `fix/round3v-registry-manifest-consistency`  
> **Status:** Proposed delta only — **do not apply on feature branch**  
> **Evidence:** `009_status_check_constraints.sql`, `tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints`, `docs/schema/MIGRATION_COVERAGE.md`, `research/migration-009-coverage-matrix.md`

## Summary

Migration **009** applied DB CHECK constraints on ingestion tables. Docs (`MIGRATION_COVERAGE.md`, `MIGRATION_008_PLAN.md`) are aligned on this branch. Registry 三件套 still reference migration **008** as closure target — coordinator must apply the deltas below in one §7.3 batch (with OPS/Latch/L5R deltas if merging together).

## RESOLVED_ISSUES_REGISTRY.md — add rows

```markdown
| A9-P1-01 | RESOLVED | Yes | `fetch_log.status`, `source_registry.source_type`/`license_type` DB CHECK in migration 009. | `backend/app/db/migrations/009_status_check_constraints.sql`; `tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints`; `docs/schema/MIGRATION_COVERAGE.md`. | — |
| A9-P2-02 | RESOLVED | Yes | `source_conflict.severity`/`reconcile_status` CHECK in migration 009. | Same migration file; schema contract test. | — |
| B2.5-O-06 | RESOLVED | Yes | Broad ingestion CHECK closeout (alias A9-P1-01 subset). | Same as A9-P1-01. | — |
```

## UNRESOLVED_ISSUES_REGISTRY.md — edits

| ID | Action | New status / note |
|---|---|---|
| `A9-P1-01` | **Remove** from DEFERRED table | → RESOLVED (see RESOLVED rows) |
| `A9-P2-02` | **Remove** from DEFERRED table | → RESOLVED |
| `B2.5-O-06` | **Remove** from DEFERRED table | → RESOLVED |
| `A9-P2-01` | **Narrow** | Status: PARTIAL RESOLVED — `manual_review_queue.status` + `source_object_type` CHECK via 009; **`priority` CHECK** remains app-layer → keep DEFERRED, owner Round 3F / future migration |
| `A9-P3-01` | **Narrow** | Status: PARTIAL RESOLVED — `source_registry`/`source_conflict` explicit INSERT via 009; **`fetch_log` + `manual_review_queue` `SELECT *` rebuild** remains DEFERRED |
| `R2-RISK-4` | **Update text** | App-layer CHECK **only** for agreed columns (e.g. `manual_review_queue.priority`); link `MIGRATION_COVERAGE.md` §009 narrative |

## AUDIT_DEFERRED_REGISTRY.md — edits

| ID | Action |
|---|---|
| `A9-P1-01` | Remove row (RESOLVED via 009) |
| `A9-P2-02` | Remove row (RESOLVED via 009) |
| `B2.5-O-06` | Remove row (RESOLVED via 009) |
| `A9-P2-01` | Change closure from "migration 008" → "009 partial; `priority` deferred Round 3F" |
| `A9-P3-01` | Change closure from "migration 008 explicit columns" → "009 partial; fetch_log/manual_review_queue SELECT * rebuild deferred" |
| `R2-RISK-4` | Replace "migration 008 for agreed subset" → "009 applied agreed subset; priority remains app-layer per MIGRATION_COVERAGE.md" |

## Post-close test expectation

After applying registry deltas, update `tests/test_unresolved_item_task_coverage.py`:

- Remove from `EXPECTED_UNRESOLVED_IDS`: `A9-P1-01`, `A9-P2-02`, `B2.5-O-06`
- Keep: `A9-P2-01`, `A9-P3-01`, `R2-RISK-4` (narrowed, still open)

Optional: update `TASK_CARD_EXPECTATIONS` for `005_create_schema_sql.md` to drop resolved IDs from required mentions.

## Production DB boundary

Delta reflects **migration file + schema.sql + contract test** alignment only. Do **not** claim production DuckDB has applied 009 without read-only `db-inspect` evidence.

## Coordinator merge order

1. Apply registry 三件套 edits (this file)
2. Update `EXPECTED_UNRESOLVED_IDS` per above
3. Re-run `uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_manifest_files_check.py -q`
4. Index untracked Round 4/5/Batch6 task docs or remove stale `MIGRATION_MAP` refs (see `zero-open-signoff.md` coordinator-integration)
