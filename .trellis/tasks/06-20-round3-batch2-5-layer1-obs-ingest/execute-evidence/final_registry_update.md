# Final Registry Update — Batch 2.5 §8.6 (AC-REG-1)

> 2026-06-20 · Phase 4 adversarial remediation + §8.6 closeout + audit repair

## RESOLVED this session

| ID                     | Item                                                               | Evidence                                                                                                          |
| ---------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| **B2.5-O-04**          | `commit_clean_observation_and_snapshots` + WriteManager clean path | `ingestion.py` single-txn commit · `observation_writer.py` · `test_layer1Observation_cleanWrite_usesWriteManager` |
| **B2.5-O-07**          | Single `fetch_log` per service fetch                               | `base_adapter.record_fetch_log` + `service.fetch`; micro-fetch tests assert `+1` delta                            |
| **AC-TRACE-1**         | Raw fetch JSON → observation mapping (not fixture-only)            | `observation_mapper.py::_load_raw_evidence_payload` · `test_layer1Observation_mappingUsesRawFetchPayload`         |
| **A1-01/04/07**        | Trace integrity + raw path sourcing                                | Same as AC-TRACE-1                                                                                                |
| **A1-02/16/B25-A2-02** | ADR-001 single transaction                                         | `commit_clean_observation_and_snapshots` one `BEGIN`/`COMMIT` scope; all writes `own_transaction=False`           |
| **A1-03/B25-A2-01**    | Phase 4 evidence baseline                                          | `capture_task_phase4_evidence` reuses Phase 1 sandbox DB + `_load_phase2_gate`                                    |
| **A1-05**              | Phase 4 FileRegistry + WriteManager                                | `_register_clean_file_registry_rows` + `FileRegistry.register_on_connection`                                      |
| **B25-A2-07**          | Lineage fetch dedupe                                               | `data_quality.py::_collect_fetch_lineage` authoritative `DESC LIMIT 1`                                            |

## REMAINING DEFERRED (non-blocking)

| ID        | Resolution phase     | Notes                                                   |
| --------- | -------------------- | ------------------------------------------------------- |
| B2.5-O-02 | §8.6 narrow PR       | `schema.sql` lag vs migration 011                       |
| B2.5-O-03 | migration 012        | App validator enforces no-future-data                   |
| B2.5-O-05 | User-authorized live | Staged `macro_supplementary` route for frozen indicator |
| B2.5-O-06 | migration 008        | Broad CHECK closeout (A9-P1-01)                         |

## Registry files touched

- `docs/AUDIT_DEFERRED_REGISTRY.md` — B2.5-O-04, B2.5-O-07 → RESOLVED; O-02/O-03/O-05/O-06 remain DEFERRED
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` — O-02/O-03/O-05/O-06 DEFERRED rows
- `docs/RESOLVED_ISSUES_REGISTRY.md` — B2.5-O-04, B2.5-O-07 added
- `research/batch25-deferred-items.md` — **normative task-scoped deferred index** (added audit repair 2026-06-20)
- `docs/quality/staged_acceptance_policy.md` — single fetch_log delta
- `implement.jsonl` — curated Batch 2.5 runtime paths (F-A1-01)
- `MASTER.plan.md` §0.10 — AC-REG-1 / AC-HANDOFF-1 closed

## Batch 3 handoff (AC-HANDOFF-1 · 018A §13 normative)

```text
Layer 1 observation ingestion bridge: PASS
Ingestion type: staged
Allowed downstream use: yes (fixture/staged semantics only; not live production)
Allowed indicator scope: ENV-E1-DGS10
Allowed as_of window: 2024-06-15 (single-point micro-fetch + clean write + snapshots)
Remaining data limitations:
  - Live FRED primary deferred (B2.5-O-05); staged macro_supplementary only
  - schema.sql lags migration 011 (B2.5-O-02)
  - axis_observation has no DB CHECK; app validators enforce no-future-data (B2.5-O-03)
  - Migration 008 broad CHECK deferred (B2.5-O-06)
```

| Field           | Value                                                                      |
| --------------- | -------------------------------------------------------------------------- |
| ingestion_type  | `staged`                                                                   |
| scope           | frozen staged indicator `ENV-E1-DGS10` · `as_of=2024-06-15`                |
| window          | single-point micro-fetch + clean write + snapshots                         |
| evidence_dir    | `.trellis/tasks/06-20-round3-batch2-5-layer1-obs-ingest/execute-evidence/` |
| next_batch_hook | Batch 3 modeling layers per `ROUND3_BATCH_IMPLEMENTATION_MAP.md`           |
