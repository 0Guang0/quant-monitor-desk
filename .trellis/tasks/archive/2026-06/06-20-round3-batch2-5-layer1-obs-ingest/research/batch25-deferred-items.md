# Batch 2.5 — Deferred Items Register (normative)

> **Purpose:** Single task-scoped index for all **intentionally DEFERRED** Batch 2.5 items after audit repair (2026-06-20).  
> **Authority chain:** `docs/AUDIT_DEFERRED_REGISTRY.md` (wins on conflict) → this file → `docs/UNRESOLVED_ISSUES_REGISTRY.md` → `execute-evidence/final_registry_update.md` §Remaining data limitations.

## Active DEFERRED (4)

| ID            | Problem                                                                             | Resolution phase                           | Task hook                                                    | Blocks Batch 3 staged?                             | Closure test / evidence                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **B2.5-O-02** | `specs/schema/schema.sql` missing 7× `axis_*` tables; migration 011 is runtime SSOT | Optional narrow PR or Batch 6 schema sync  | `06-20-round3-batch2-5-layer1-obs-ingest` §8.6               | **No** (staged OK)                                 | `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`                                                                              |
| **B2.5-O-03** | `axis_observation` has no DB CHECK on timestamp ordering (ADR-002 app-layer)        | migration 012 or remain app-validated      | `ingestion.py` commit + `observation_contract.py`            | **No**                                             | `test_layer1Ingestion_phase0_axisObservation_noDbCheck_classified` + Phase 4 no-future-data tests                                   |
| **B2.5-O-05** | `ENV-E1-DGS10` declares FRED primary; path uses staged `macro_supplementary`        | User-authorized live FRED or remain staged | MASTER AC-P2-0 · `ingestion.py` `FRED_PRIMARY_DEFERRED_NOTE` | **Yes for live claims**; **No for staged/fixture** | `test_layer1Ingestion_phase0_frozenIndicator_stagedRouteCapabilityDeclared` · `test_batch25_evidence_is_staged_not_production_live` |
| **B2.5-O-06** | Migration 008 broad CHECK closeout (alias A9-P1-01)                                 | Round 3 Batch 6 / migration 008            | `docs/schema/MIGRATION_008_PLAN.md`                          | **No**                                             | migration 008 applied + contract tests                                                                                              |

## RESOLVED this batch (reference)

| ID        | Closed     | Evidence                                                                                                                                     |
| --------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| B2.5-O-04 | 2026-06-20 | `commit_clean_observation_and_snapshots` + `Layer1ObservationWriter` · `test_layer1Observation_cleanWrite_usesWriteManager`                  |
| B2.5-O-07 | 2026-06-20 | Single `fetch_log` per service fetch · `base_adapter.record_fetch_log` · `test_layer1MicroIngestion_writesFetchLogAndRawEvidence` (+1 delta) |

## Downstream labeling (018A §13 / Batch 3)

Batch 3 may use Layer 1 outputs **only with staged/fixture semantics** until:

- **B2.5-O-05** closed with user authorization evidence, or
- Explicit operator acceptance of fixture-only downstream modeling.

Documented limitations block: live FRED claims (O-05), schema.sql mirror drift (O-02), DB CHECK gap (O-03), migration 008 CHECK subset (O-06).

## Cross-links

- `docs/AUDIT_DEFERRED_REGISTRY.md` §DEFERRED — Round 3 Batch 2.5
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` §Round 3 Batch 2.5
- `execute-evidence/final_registry_update.md` — Batch 3 handoff + Remaining data limitations
- `docs/quality/staged_acceptance_policy.md` §6 — Phase 3 staging + fetch_log delta
- `tests/test_batch25_production_data_gate.py` — prevents staged→live wording drift
