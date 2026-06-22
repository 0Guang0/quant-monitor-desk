# Batch 3 — Staged-Only Downstream Gate

> Closes audit item **A01-P1-02** / **R3-B25-DOC-01**.  
> Batch 2.5 Layer 1 ingestion is **staged/fixture only** until Batch 2.75 live pilot closes or is re-deferred.

## Mandatory constraints for Batch 3 MASTER / AUDIT

Before Batch 3 implementation or any “real-data-ready” claim:

1. Cite `final_registry_update.md` — ingestion type: **staged**, not production-live.
2. Cite `018A_layer1_observation_ingestion_bridge.md` §13 — downstream must not assume continuous production data.
3. Cite `docs/ROUND3_HANDOFF.md` Batch 2.5 section — **archived PASS · staged/fixture only**.
4. If `R3-B2.75-01` remains DEFERRED, Batch 3 MUST NOT use live FRED / production DB / external vendor writes.

## R3-B3-STAGED-DOWNSTREAM-GATE

This gate is also tracked in `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`. Batch 3 planning must close this gate before `019` implementation starts. The current Batch 2.75 closeout is `PILOT_FAIL_SOURCE`, so Batch 3 remains staged-only until a later evidence gate narrows that statement.

## Closure test

- Batch 3 Trellis `MASTER.plan.md` contains a “Staged downstream limitations” subsection referencing this file.
- `test_batch25_evidence_is_staged_not_production_live` remains green.

## Cleanup phase

**Batch 3 planning gate** — required before `task.py start` on Batch 3 task directory.
