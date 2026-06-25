# Schema vs Migration Coverage Matrix

> **Last verified:** 2026-06-25 · **Baseline:** `master` @ migrations `001`–`011` · B3V-L5R reconcile  
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
| `instrument_registry`, `security_bar_1d`             | —         | DEFERRED — Layer 5  | Staged runtime only; `FUTURE_PHASE_KEY_TABLES`; Round 3F owner |
| `backtest_*`, `alert_event`                          | —         | N/A — Round 4/5     |                                                                |

## Round 3 Layer 3 — industry chain (designed, no migration)

> **SSOT:** `docs/modules/layer3_industry_shock_anchor.md` — **not** in `specs/schema/schema.sql` (design split).  
> **Closure test:** `tests/test_migration_coverage.py` · **Reconcile matrix:** `.trellis/tasks/round3v-layer5-model-schema-reconcile/research/l5-reconcile-matrix.md` §3.1

| Object | Migration | Status | Notes |
| --- | --- | --- | --- |
| `industry_chain_registry` | — | DEFERRED | Staged loader `layer3_chains/` |
| `industry_chain_anchor` | — | DEFERRED | Staged loader |
| `industry_chain_node` | — | DEFERRED | Staged loader |
| `industry_chain_edge` | — | DEFERRED | Staged loader |
| `industry_chain_cross_edge` | — | DEFERRED | Staged loader |
| `industry_chain_instrument_map` | — | DEFERRED | Staged loader |
| `industry_chain_event_anchor` | — | DEFERRED | Doc defer note |
| `industry_chain_daily_snapshot` | — | DEFERRED | Staged `snapshot_builder.py` |

**Migration ownership:** Round 3F (`R3-MODEL-L3L4-MIGRATION` proposed defer).

## Round 3 Layer 4 — market structure (designed, no migration)

> **SSOT:** `docs/modules/layer4_market_structure.md` — **not** in `specs/schema/schema.sql`.

| Object | Migration | Status | Notes |
| --- | --- | --- | --- |
| `market_registry` | — | DEFERRED | Staged `layer4_markets/` |
| `market_calendar` | — | DEFERRED | Staged adapters |
| `market_index_snapshot` | — | DEFERRED | Staged adapters |
| `market_sector_snapshot` | — | DEFERRED | Staged adapters |
| `market_breadth_snapshot` | — | DEFERRED | Staged adapters |
| `market_rule_event` | — | DEFERRED | Staged adapters |

## Round 3 Layer 5 — security evidence (partial design in schema.sql)

> **SSOT split:** `specs/schema/schema.sql` lists `instrument_registry`, `security_bar_1d`; module doc uses `security_bar_daily` naming — **neither migrated**.  
> **Staged runtime:** `backend/app/layer5_evidence/` — not production DB path.

| Object | Migration | Status | Notes |
| --- | --- | --- | --- |
| `instrument_registry` | — | DEFERRED | Staged validator; `KEY_TABLES` forward inventory |
| `security_bar_1d` (`schema.sql`) | — | DEFERRED | Design name in `schema.sql` |
| `security_bar_daily` (module doc) | — | DEFERRED | Runtime model name; naming drift vs schema |
| `futures_bar_daily`, `options_chain_snapshot` | — | DEFERRED | 023 full scope |
| `financial_statement_snapshot`, `valuation_snapshot` | — | DEFERRED | 023 full scope |
| `event_registry`, `evidence_chain`, `stock_model_evidence` | — | DEFERRED / staged | In-memory chain only for `evidence_chain` |

## Round 3 Layer 1 (migration 011)

| Object                  | Status | Notes                                                                      |
| ----------------------- | ------ | -------------------------------------------------------------------------- |
| `axis_observation`      | DONE   | 17 columns; no DB CHECK (ADR-002 app-layer); see `observation_contract.py` |
| `axis_snapshot_lineage` | DONE   | `source_fetch_ids` / `source_content_hashes` as VARCHAR JSON               |

## Verification

```powershell
.venv\Scripts\python.exe -m pytest tests/test_schema_migration.py -q
.venv\Scripts\python.exe -m pytest tests/test_audit_fixes.py -q
.venv\Scripts\python.exe -m pytest tests/test_migration_coverage.py -q
```

Cross-reference: `docs/schema/MIGRATION_008_PLAN.md`, `docs/AUDIT_DEFERRED_REGISTRY.md`.

**Migration 009 vs 008 narrative (ADV-A6-003 / R4):** Migration **007** rebuilt sync job tables with CHECK constraints; **008** (planned) covers remaining enum CHECKs per `MIGRATION_008_PLAN.md`; **009** applied `status` CHECK constraints on ingestion tables; **010** enforced non-null `rule_set_id` / `rule_version` on validation lineage with explicit-column rebuild (no `SELECT *` replay).
