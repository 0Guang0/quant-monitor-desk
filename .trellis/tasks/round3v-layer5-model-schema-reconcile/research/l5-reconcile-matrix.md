# Layer5 / Model Schema Reconcile Matrix

> **Task:** B3V-L5R · `B03_01_layer5_model_schema_reconcile.md`  
> **Branch:** `review/round3v-layer5-model-schema-reconcile`  
> **Baseline:** post Batch 01 master · merge `376e30e6` (`R3-TASK-023`)  
> **Status:** Execute verified 2026-06-25 — pytest + matrix refreshed  
> **Baseline:** post Batch 01 master · merge `376e30e6` (`R3-TASK-023`)  
> **Date:** 2026-06-25

---

## 1. Per-VR summary

| VR ID          | Audit ask (task card)                                                                             | Reconcile verdict                                                                                              | Resolution                           | Closure test (mandatory)                                                                                              | Follow-up                                                  |
| -------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `VR-L5-001`    | Full evidence chain, builder, provenance, agent-text rejection, manual review, lineage hash tests | Staged runtime **implemented** post `376e30e6`; DB/production path **not** in scope                            | **stale close**                      | `tests/test_layer5_evidence_chain.py` (7) + `tests/test_layer5_evidence_foundation.py` (6) — **13 passed** 2026-06-25 | L5 DB tables → `VR-MODEL-001` / Round 3F                   |
| `VR-MODEL-001` | L3/L4/L5 designed vs implemented vs deferred matrix                                               | Most modeling tables **designed**; L1 **migrated**; L3/L4/L5 **staged runtime only**; no L3/L4 in `schema.sql` | **resolve with matrix** + docs align | `tests/test_migration_coverage.py` (6) — **passed** 2026-06-25 + `docs/schema/MIGRATION_COVERAGE.md`                  | Migration ownership → Round 3F (`R3-MODEL-L3L4-MIGRATION`) |

---

## 2. VR-L5-001 — Evidence chain capability matrix

| Capability                           | Runtime module                                | Test pointer                                               | Status                   | Notes                                        |
| ------------------------------------ | --------------------------------------------- | ---------------------------------------------------------- | ------------------------ | -------------------------------------------- |
| Evidence chain builder               | `evidence_chain.py` `EvidenceChainBuilder`    | `test_evidenceChain_traceUpstreamSnapshots`                | **implemented (staged)** | Upstream L3/L4 context slots                 |
| Empty upstream / context guard       | `evidence_chain.py`                           | `test_evidenceChain_rejectsEmptyUpstreamContext`           | **implemented**          |                                              |
| Agent text not fact                  | `foundation.py` + `reject_agent_text_as_fact` | `test_evidenceChain_rejectsAgentTextAsFact`                | **implemented**          | AC-023-3                                     |
| Provenance required (factual)        | `foundation.py`                               | `test_evidenceFoundation_factualRecord_requiresProvenance` | **implemented**          |                                              |
| Manual review on severe conflict     | `evidence_chain.py`                           | `test_evidenceChain_severeConflictQueuesManualReview`      | **implemented**          |                                              |
| Manual review state consistency      | `foundation.py`                               | `test_evidenceFoundation_manualReview_*`                   | **implemented**          |                                              |
| Identity hash deterministic          | `foundation.py`                               | `test_evidenceFoundation_identityHash_isDeterministic`     | **implemented**          |                                              |
| Lineage envelope + parameter hash    | `lineage.py`                                  | `test_layer5Lineage_envelopeMatchesSnapshotContractFields` | **implemented**          | `layer_id=layer5`                            |
| Instrument registry validation       | `instrument_registry.py`                      | `test_instrumentRegistry_uniqueIds`                        | **implemented (staged)** |                                              |
| Security bar no-future-date          | `evidence_validator.py`                       | `test_securityBar_rejectsFutureTradeDate`                  | **implemented (staged)** |                                              |
| EvidenceReadPort boundary            | `ports.py`                                    | `test_evidenceReadPort_boundary`                           | **implemented**          | No storage import                            |
| DB persistence / WriteManager path   | —                                             | —                                                          | **deferred**             | Round 3F migration                           |
| financial / valuation / event tables | —                                             | —                                                          | **deferred**             | 023 full scope; out of VR-L5-001 stale close |

**Stale close evidence bundle:**

- Commit: `376e30e6` (merge wave-d B01-023)
- Registry: `AUDIT_DEFERRED_REGISTRY.md` → `R3-TASK-023` RESOLVED
- Regression tests: see Closure test column above

---

## 3. VR-MODEL-001 — L3 / L4 / L5 table matrix

**Legend**

| Column                      | Meaning                                         |
| --------------------------- | ----------------------------------------------- |
| **designed**                | Listed in module doc and/or `schema.sql` design |
| **implemented (runtime)**   | Python module + staged tests/fixtures           |
| **implemented (migration)** | DuckDB migration applied                        |
| **deferred**                | No migration; explicit defer note               |

### 3.1 Layer 3 (`docs/modules/layer3_industry_shock_anchor.md`)

| Table                           | design_ssot | migration | runtime                          | Status                        |
| ------------------------------- | ----------- | --------- | -------------------------------- | ----------------------------- |
| `industry_chain_registry`       | module doc  | —         | `layer3_chains/loader.py` staged | **designed + staged runtime** |
| `industry_chain_anchor`         | module doc  | —         | loader + fixtures                | **designed + staged runtime** |
| `industry_chain_node`           | module doc  | —         | loader                           | **designed + staged runtime** |
| `industry_chain_edge`           | module doc  | —         | loader                           | **designed + staged runtime** |
| `industry_chain_cross_edge`     | module doc  | —         | loader                           | **designed + staged runtime** |
| `industry_chain_instrument_map` | module doc  | —         | loader                           | **designed + staged runtime** |
| `industry_chain_event_anchor`   | module doc  | —         | deferred in docs                 | **deferred**                  |
| `industry_chain_daily_snapshot` | module doc  | —         | `snapshot_builder.py` staged     | **designed + staged runtime** |

> `specs/schema/schema.sql` **does not** define L3 tables — design SSOT split (BLK-L5R-03).

### 3.2 Layer 4 (`docs/modules/layer4_market_structure.md`)

| Table                     | design_ssot | migration | runtime                  | Status                        |
| ------------------------- | ----------- | --------- | ------------------------ | ----------------------------- |
| `market_registry`         | module doc  | —         | `layer4_markets/` staged | **designed + staged runtime** |
| `market_calendar`         | module doc  | —         | adapters staged          | **designed + staged runtime** |
| `market_index_snapshot`   | module doc  | —         | adapters staged          | **designed + staged runtime** |
| `market_sector_snapshot`  | module doc  | —         | adapters staged          | **designed + staged runtime** |
| `market_breadth_snapshot` | module doc  | —         | adapters staged          | **designed + staged runtime** |
| `market_rule_event`       | module doc  | —         | adapters staged          | **designed + staged runtime** |

### 3.3 Layer 5 (`docs/modules/layer5_security_evidence.md` + `schema.sql`)

| Table                                 | design_ssot           | migration | runtime                          | Status                                     |
| ------------------------------------- | --------------------- | --------- | -------------------------------- | ------------------------------------------ |
| `instrument_registry`                 | module + `schema.sql` | —         | `instrument_registry.py` staged  | **designed; migration deferred**           |
| `security_bar_daily` (doc name)       | module doc            | —         | `models.SecurityBarDaily` staged | **designed + staged runtime**              |
| `security_bar_1d` (`schema.sql` name) | `schema.sql`          | —         | —                                | **designed only** — naming mismatch vs doc |
| `futures_bar_daily`                   | module doc            | —         | —                                | **deferred**                               |
| `options_chain_snapshot`              | module doc            | —         | —                                | **deferred**                               |
| `financial_statement_snapshot`        | module doc            | —         | —                                | **deferred**                               |
| `valuation_snapshot`                  | module doc            | —         | —                                | **deferred**                               |
| `event_registry`                      | module doc            | —         | —                                | **deferred**                               |
| `evidence_chain`                      | module doc            | —         | in-memory `EvidenceChainRecord`  | **staged runtime only**                    |
| `stock_model_evidence`                | module doc            | —         | —                                | **deferred**                               |

### 3.4 Cross-reference: `MIGRATION_COVERAGE.md` (current)

| Object                                   | Doc status                          | Matrix alignment                                                      |
| ---------------------------------------- | ----------------------------------- | --------------------------------------------------------------------- |
| `instrument_registry`, `security_bar_1d` | N/A — Layer 5 (023)                 | **Consistent** — not migrated                                         |
| L3/L4 tables                             | **Added** L3/L4 sections 2026-06-25 | **Aligned** — B03-MODEL-02 complete                                   |
| L1 `axis_*` (7 tables)                   | DONE migration 011                  | Closure: `test_migrationCoverage_l1AxisTables_existAfterMigration011` |

---

## 4. Execute checklist

- [x] Refresh pytest timestamps in §1 after full run (2026-06-25)
- [x] Complete B03-MODEL-03 `test_migration_coverage.py` (6 tests green)
- [x] Update `MIGRATION_COVERAGE.md` from §3
- [x] Fill `registry_proposed_delta.yaml` for main session
- [x] Adversarial audit before merge (main session) — ADV-L5R-01..04 CLOSED 2026-06-25
