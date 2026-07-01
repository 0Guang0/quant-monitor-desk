# Research: L3/L4/L5 designed vs implemented vs deferred

- **Query**: Build table-state matrix for `VR-MODEL-001`
- **Scope**: internal
- **Date**: 2026-06-25

## Findings

### Migration inventory

| Migration range     | Modeling tables                                                              |
| ------------------- | ---------------------------------------------------------------------------- |
| `001`–`010`         | Ingestion / sync / lineage — no L3/L4/L5 modeling                            |
| `011_layer1_tables` | L1 `axis_*` (7 tables) — **only migrated modeling layer**                    |
| (none)              | `industry_chain_*`, `market_*`, L5 `instrument_registry` / `security_bar_1d` |

Grep `backend/app/db/migrations/` for `industry_chain|market_registry|instrument_registry` → **no matches**.

### schema.sql vs module docs

| Layer | In `specs/schema/schema.sql`             | In module docs                             |
| ----- | ---------------------------------------- | ------------------------------------------ |
| L3    | **Absent**                               | 8 `industry_chain_*` tables                |
| L4    | **Absent**                               | 6 `market_*` tables                        |
| L5    | `instrument_registry`, `security_bar_1d` | 9 tables incl. `security_bar_daily` naming |

**Naming drift:** module `security_bar_daily` vs schema `security_bar_1d` — matrix must not mark either as migrated.

### Runtime (staged) evidence

| Layer | Package                        | Test module                                                      |
| ----- | ------------------------------ | ---------------------------------------------------------------- |
| L3    | `backend/app/layer3_chains/`   | `tests/test_layer3_loader.py`, `test_layer3_snapshot_builder.py` |
| L4    | `backend/app/layer4_markets/`  | `tests/test_layer4_market_structure.py`                          |
| L5    | `backend/app/layer5_evidence/` | `tests/test_layer5_evidence_*.py`                                |

Runtime proves **staged builders/loaders**, not DuckDB table existence.

### KEY_TABLES forward inventory

`backend/app/ops/db_inspector.py:34-39` lists `instrument_registry`, `security_bar_1d` in `KEY_TABLES` with `FUTURE_PHASE_KEY_TABLES` — `exists: false` until migration.

### docs/schema/MIGRATION_COVERAGE.md gaps

- Last verified 2026-06-22 @ migrations 001–011
- L5 rows: N/A until Batch 5 — **aligned**
- **Missing:** L3/L4 designed table section — Execute B03-MODEL-02

### Nearest existing test (pre-`test_migration_coverage.py`)

- `tests/test_schema_migration.py` — validates migration **files** 001–011, not L3/L4/L5 design matrix
- Plan: new `test_migration_coverage.py` encodes matrix invariants (TDD B03-MODEL-03)

## Caveats / Not Found

- `tests/test_migration_coverage.py` — **created** B03-MODEL-03 (6 tests green 2026-06-25)
- Round 3F task card for L3/L4 migration not pinned in this research — propose defer ID `R3-MODEL-L3L4-MIGRATION` in registry delta.
