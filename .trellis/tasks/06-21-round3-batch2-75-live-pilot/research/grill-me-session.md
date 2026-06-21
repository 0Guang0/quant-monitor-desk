# Grill-Me Session — Batch 2.75

## Q1: Can we reuse Batch 2.5 `capture_task_phase3_evidence`?

**A:** No. It builds `build_staged_fixture_service` and wipes a fixture sandbox. Batch 2.75 forbids fixture/staged fallback for live evidence. New `live_pilot` path with real adapters only.

## Q2: Does passing Request 3 (akshare DGS10) close FRED primary / `B2.5-O-05`?

**A:** No. It only records supplementary macro shape. `ENV-E1-DGS10` Layer1 spec still declares `FRED:DGS10`. Closeout must state FRED primary remains deferred unless separate authorization.

## Q3: Default plan includes clean write?

**A:** No. `allow_clean_write=false` per 018B §3.1. Expected closeout is `PILOT_PASS_RAW_ONLY`. Phase 4 runs validation only unless user amends authorization.

## Q4: Can Batch 3 start if we `PILOT_REDEFERRED`?

**A:** Yes, but only under `BATCH3_STAGED_DOWNSTREAM_GATE.md` — no live FRED/production DB/external vendor writes as default.

## Q5: Same sprint as ingestion R2b?

**A:** Forbidden per `layer1_ingestion_refactor_rollback_plan.md` §6. MASTER §3.2 records sprint-scope note.

## Residual risks (→ MASTER §7)

- Network flakiness on baostock/akshare → capture as `PILOT_FAIL_SOURCE` evidence, not silent retry to fixture
- Windows path length on raw store → reuse `path_compat` if needed
- Perf smoke may re-defer → must name owner in registry
