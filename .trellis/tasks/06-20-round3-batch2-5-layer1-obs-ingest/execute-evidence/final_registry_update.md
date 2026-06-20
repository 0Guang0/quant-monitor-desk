# Final Registry Update — Batch 2.5 §8.6 (AC-REG-1)

> 2026-06-20 · Phase 4 adversarial remediation + §8.6 closeout

## RESOLVED this session

| ID                     | Item                                                               | Evidence                                                                                                          |
| ---------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **B2.5-O-04**          | `commit_clean_observation_and_snapshots` + WriteManager clean path | `ingestion.py` single-txn commit · `observation_writer.py` · `test_layer1Observation_cleanWrite_usesWriteManager` |
| **AC-TRACE-1**         | Raw fetch JSON → observation mapping (not fixture-only)            | `observation_mapper.py::_load_raw_evidence_payload` · `test_layer1Observation_mappingUsesRawFetchPayload`         |
| **A1-01/04/07**        | Trace integrity + raw path sourcing                                | Same as AC-TRACE-1                                                                                                |
| **A1-02/16/B25-A2-02** | ADR-001 single transaction                                         | `commit_clean_observation_and_snapshots` one `BEGIN`/`COMMIT` scope; all writes `own_transaction=False`           |
| **A1-03/B25-A2-01**    | Phase 4 evidence baseline                                          | `capture_task_phase4_evidence` reuses Phase 1 sandbox DB + `_load_phase2_gate`                                    |
| **A1-05**              | Phase 4 FileRegistry + WriteManager                                | `_register_clean_file_registry_rows` + `FileRegistry.register_on_connection`                                      |
| **B25-A2-07**          | Lineage fetch dedupe                                               | `data_quality.py::_collect_fetch_lineage` authoritative `DESC LIMIT 1`                                            |

## REMAINING DEFERRED (non-blocking)

| ID        | Resolution phase     | Notes                                                                           |
| --------- | -------------------- | ------------------------------------------------------------------------------- |
| B2.5-O-02 | §8.6 narrow PR       | `schema.sql` lag vs migration 011                                               |
| B2.5-O-03 | migration 012        | App validator enforces no-future-data                                           |
| B2.5-O-05 | User-authorized live | Staged `macro_supplementary` route for frozen indicator                         |
| B2.5-O-06 | migration 008        | Broad CHECK closeout (A9-P1-01)                                                 |
| B2.5-O-07 | Optional refactor    | Double `fetch_log` insert retained; lineage uses service-authoritative row only |

## Registry files touched

- `docs/AUDIT_DEFERRED_REGISTRY.md` — B2.5-O-04 → RESOLVED; B2.5-O-07 lineage note updated
- `docs/quality/staged_acceptance_policy.md` — §6 unchanged (Phase 3 staging exception still valid)
- `MASTER.plan.md` §0.10 — AC-REG-1 / AC-HANDOFF-1 closed this session

## Batch 3 handoff fields (AC-HANDOFF-1)

| Field           | Value                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| ingestion_type  | `layer1_observation_bridge`                                                |
| scope           | frozen staged indicator `ENV-E1-DGS10` · `as_of=2024-06-15`                |
| window          | single-point micro-fetch + clean write + snapshots                         |
| evidence_dir    | `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/execute-evidence/` |
| next_batch_hook | Batch 3 modeling layers per `ROUND3_BATCH_IMPLEMENTATION_MAP.md`           |
