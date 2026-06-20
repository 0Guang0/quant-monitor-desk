# Schema vs Migration Coverage Matrix

> **Last verified:** 2026-06-20 · **Baseline:** `master` @ migrations `001`–`011`  
> **Purpose:** Clarify which `specs/schema/schema.sql` objects are implemented vs deferred (closes audit A2-P2-01).

## Legend

| Status       | Meaning                                                                       |
| ------------ | ----------------------------------------------------------------------------- |
| **DONE**     | Table/column exists in applied migrations                                     |
| **PARTIAL**  | Table exists; some columns or CHECK constraints deferred to app layer         |
| **DEFERRED** | In design `schema.sql` but no migration yet; see `AUDIT_DEFERRED_REGISTRY.md` |
| **N/A**      | Round 3+ modeling / backtest tables; not Round 2 scope                        |

## Core ingestion (Round 2)

| Object                   | Migration | Status   | Notes                                            |
| ------------------------ | --------- | -------- | ------------------------------------------------ |
| `schema_version`         | 001       | DONE     |                                                  |
| `source_registry`        | 004       | PARTIAL  | Status/enums enforced in app; no DB CHECK on 004 |
| `fetch_log`              | 004       | PARTIAL  | Status enums app-layer                           |
| `file_registry`          | 001/004   | DONE     | `content_hash` UNIQUE                            |
| `data_sync_job`          | 006, 007  | DONE     | Status CHECK via 007 rebuild                     |
| `job_event_log`          | 006, 007  | DONE     | old/new status CHECK                             |
| `validation_report`      | 005       | DONE     | Status CHECK                                     |
| `data_quality_log`       | 005       | DONE     |                                                  |
| `source_conflict`        | 005       | PARTIAL  | `reconcile_status` CHECK deferred                |
| `write_audit_log`        | 001, 007  | PARTIAL  | Extra audit columns in design not all migrated   |
| `resource_guard_log`     | 003       | DONE     |                                                  |
| `manual_review_queue`    | 005       | PARTIAL  | status/priority CHECK deferred                   |
| `source_health_snapshot` | —         | DEFERRED | D2-P2-1                                          |

## Modeling / backtest (Round 3+)

| Object                                               | Migration | Status              | Notes                                                          |
| ---------------------------------------------------- | --------- | ------------------- | -------------------------------------------------------------- |
| `axis_registry` … `axis_snapshot_lineage` (7 tables) | 011       | DONE                | Authoritative for Layer 1; `schema.sql` sync **DEFERRED O-02** |
| `instrument_registry`, `security_bar_1d`             | —         | N/A — Layer 5 (023) | Listed in `KEY_TABLES` as `exists: false` until Batch 5        |
| `backtest_*`, `alert_event`                          | —         | N/A — Round 4/5     |                                                                |

## Round 3 Layer 1 (migration 011)

| Object                  | Status | Notes                                                                      |
| ----------------------- | ------ | -------------------------------------------------------------------------- |
| `axis_observation`      | DONE   | 17 columns; no DB CHECK (ADR-002 app-layer); see `observation_contract.py` |
| `axis_snapshot_lineage` | DONE   | `source_fetch_ids` / `source_content_hashes` as VARCHAR JSON               |

## Verification

```powershell
.venv\Scripts\python.exe -m pytest tests/test_schema_migration.py -q
.venv\Scripts\python.exe -m pytest tests/test_audit_fixes.py -q
```

Cross-reference: `docs/AUDIT_DEFERRED_REGISTRY.md`, `ROUND2_GAPS_AND_DEVIATIONS.md` §1, `docs/schema/MIGRATION_008_PLAN.md` (planned 008 CHECK constraints).
