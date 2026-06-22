# Batch 3 — Staged-Only Downstream Gate

> Closes local alias **`R3-B3-STAGED-DOWNSTREAM-GATE`** and audit follow-up **`A01-P1-02`** / **`R3-B25-DOC-01`**.  
> Batch 2.5 Layer 1 ingestion remains **staged/fixture only**. Batch 2.75 controlled pilot closeout is **`PILOT_FAIL_SOURCE`**.

## Gate status

| Field | Value |
| ----- | ----- |
| Gate ID | `R3-B3-STAGED-DOWNSTREAM-GATE` |
| Branch | `integration/round3` (merged from `feature/round3-batch3-staged-gate`) |
| Worktree | `../quant-monitor-desk-wt-r3-batch3-staged-gate` |
| Trellis slice | `.trellis/tasks/06-22-round3-batch3-staged-gate/DEBT.plan.md` |
| Status | **CLOSED** (2026-06-22) — docs/tests gate only; does not open production-live readiness |
| Unblocks | `feature/round3-019-layer2-sensor` may start **staged-only** planning/implementation |
| Does not unblock | production-live claims, live FRED primary, production DB writes, source default enablement |

## Required decision record

1. **Batch 2.75 closeout is `PILOT_FAIL_SOURCE`.**
2. **Request 2 Eastmoney hist remains deferred as `R3-B2.75-REQ2-EM`.**
3. **Batch 3 / `019` may proceed only as staged-only downstream work.**
4. **No evidence in the staged-gate branch creates production-live readiness.**
5. **`018C` may run in parallel but does not unblock production-live claims.**

## Mandatory constraints for Batch 3 MASTER / AUDIT

Before Batch 3 implementation or any “real-data-ready” / “production-live” claim:

1. Cite Batch 2.5 `final_registry_update.md` — ingestion type: **staged**, not production-live.
2. Cite `018A_layer1_observation_ingestion_bridge.md` §13 — downstream must not assume continuous production data.
3. Cite `docs/ROUND3_HANDOFF.md` — **staged/fixture only**; closeout **`PILOT_FAIL_SOURCE`**.
4. Cite `docs/quality/production_live_pilot_policy.md` — Batch 2.75 does **not** open formal production data access.
5. While `R3-B2.75-REQ2-EM` remains open, Batch 3 MUST NOT use live FRED primary, production clean DB mutation, or external vendor writes as default prerequisites.
6. `B2.5-O-05` remains **DEFERRED**: Batch 2.75 Request 3 (`akshare` / `macro_supplementary`) records supplementary macro shape only and does **not** close FRED `primary_source` for `ENV-E1-DGS10`. Batch 3 must not treat `macro_supplementary` as live FRED or production-live macro evidence.

## `019` staged-only start conditions

| # | Condition |
| - | --------- |
| 1 | `R3-B3-STAGED-DOWNSTREAM-GATE` is **CLOSED** |
| 2 | Batch 3 `MASTER.plan.md` includes **“Staged downstream limitations”** referencing this file |
| 3 | `test_batch25_evidence_is_staged_not_production_live` remains green |
| 4 | `test_batch3_staged_gate_records_fail_closed_decisions` remains green |

Forbidden default inputs: live FRED primary for `ENV-E1-DGS10`, production clean DB mutation, QMT/xqshare/Yahoo live routes, full-market/full-history scans.

## Fail-closed production-live language

Forbidden claims include “production-live ready”, “live production ingestion”, and treating Batch 2.5/2.75 sandbox evidence as production truth. `018C` probe PASS does not close `R3-B2.75-REQ2-EM` or unblock production-live claims.

Permitted wording: **staged-only**, **fixture-backed**, **sandbox evidence**, **does not open production-live access**.

## Closure test

- [x] Decision record and `019` start conditions recorded here.
- [x] `test_batch25_evidence_is_staged_not_production_live` remains green.
- [x] `test_batch3_staged_gate_records_fail_closed_decisions` remains green.

## Cleanup phase

Required before `task.py start` on Batch 3 (`019`). Runtime `019` stays on `feature/round3-019-layer2-sensor` after merge to `integration/round3`.
