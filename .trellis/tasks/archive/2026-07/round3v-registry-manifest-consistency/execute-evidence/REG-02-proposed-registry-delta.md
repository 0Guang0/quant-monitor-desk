# Proposed registry deltas — B3V-REG (主会话批闭合 · 勿在本分支 commit)

> **Source:** `009_status_check_constraints.sql` + `test_schemaContract_includesStatusCheckConstraints` + `research/migration-009-coverage-matrix.md`  
> **Owner:** merge coordinator / main session  
> **Branch:** `fix/round3v-registry-manifest-consistency` — evidence only

## Move toward RESOLVED

| ID          | Current                   | Proposed                                                                                         | Evidence                                                            |
| ----------- | ------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| `A9-P1-01`  | DEFERRED → migration 008  | **RESOLVED** (subset: `fetch_log.status`, `source_registry.source_type`/`license_type` DB CHECK) | `009_status_check_constraints.sql` lines 4–83; schema contract test |
| `A9-P2-02`  | DEFERRED → migration 008  | **RESOLVED** (`source_conflict.reconcile_status` + `severity` CHECK in 009)                      | `009_status_check_constraints.sql` lines 108–157                    |
| `B2.5-O-06` | DEFERRED (alias A9-P1-01) | **RESOLVED** or merge into A9-P1-01 close                                                        | Same as A9-P1-01                                                    |

**Suggested RESOLVED_ISSUES_REGISTRY.md rows:**

```markdown
| A9-P1-01 | RESOLVED | Yes | `fetch_log.status`, `source_registry.source_type`/`license_type` DB CHECK in migration 009. | `backend/app/db/migrations/009_status_check_constraints.sql`; `tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints`; `docs/schema/MIGRATION_COVERAGE.md`. | — |
| A9-P2-02 | RESOLVED | Yes | `source_conflict.severity`/`reconcile_status` CHECK in migration 009. | Same migration file; schema contract test. | — |
| B2.5-O-06 | RESOLVED | Yes | Broad ingestion CHECK closeout (alias A9-P1-01 subset). | Same as A9-P1-01. | — |
```

## Precise re-defer / narrow (remaining gaps)

| ID          | Proposed note                                                                                                                                                                                |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `A9-P2-01`  | **Narrow:** `manual_review_queue.status` + `source_object_type` → RESOLVED via 009; **`priority` CHECK** remains app-layer → keep DEFERRED with owner Round 3F / future migration            |
| `A9-P3-01`  | **Narrow:** `source_registry`/`source_conflict` explicit INSERT → RESOLVED in 009; **`fetch_log` + `manual_review_queue` `SELECT *`** in 009 → remain DEFERRED until explicit-column rebuild |
| `R2-RISK-4` | Update text: app-layer CHECK **only** for agreed columns (e.g. `manual_review_queue.priority`); link `MIGRATION_COVERAGE.md`                                                                 |

**Suggested UNRESOLVED_ISSUES_REGISTRY.md / AUDIT_DEFERRED_REGISTRY.md edits:**

- Remove or resolve `A9-P1-01`, `A9-P2-02`, `B2.5-O-06` from DEFERRED tables.
- `A9-P2-01`: change closure to "009 partial; priority deferred to Round 3F".
- `A9-P3-01`: change closure to "009 partial; fetch_log/manual_review_queue SELECT \* rebuild deferred".
- `R2-RISK-4`: replace "migration 008 for agreed subset" with "009 applied agreed subset; priority remains app-layer per MIGRATION_COVERAGE.md".

## Post-close test expectation

After main session applies deltas, update `tests/test_unresolved_item_task_coverage.py` `EXPECTED_UNRESOLVED_IDS` — remove `A9-P1-01` (and peers moved to RESOLVED).

## Production DB boundary

This delta reflects **migration file + schema.sql** alignment only. Do **not** claim production DuckDB has applied 009 without read-only `db-inspect` evidence.
