# Phase -1 Registry Reconciliation — Batch 2.75

> Execute §8.1 · AC-PM1..PM4 · 2026-06-21

## Umbrella task

| ID                         | Role                                   | MASTER AC          |
| -------------------------- | -------------------------------------- | ------------------ |
| `R3-B2.75-PROD-LIVE-PILOT` | Controlled live pilot gate (this task) | AC-P0..P5, AC-GATE |

## Five tracked IDs → acceptance criteria

| ID                      | Current registry state (pre-Execute)               | Mapped AC           | Closeout owner                                                    |
| ----------------------- | -------------------------------------------------- | ------------------- | ----------------------------------------------------------------- |
| `R3-B2.75-01`           | UNRESOLVED / DEFERRED — pilot not executed         | AC-P5-1..4, AC-GATE | Batch 2.75 Execute → `PILOT_*`                                    |
| `GLOBAL-P2-01`          | Pending fix registry — external live pilot not run | AC-P3, AC-P5        | Same; paired with R3-B2.75-01                                     |
| `B2.5-O-05`             | DEFERRED — FRED primary vs staged macro            | AC-P2, AC-P3-5      | Batch 2.75; Request 3 shape-only; **does not** close FRED primary |
| `R3-B25-PERF-BUDGET-01` | OPEN — perf budget artifact stale                  | AC-P45-1..3         | §8.7 smoke or re-defer                                            |
| `R3-B25-HYG-03`         | OPEN (hygiene) — A6 benchmark not refreshed        | AC-P45-1..3         | §8.7 `production_equivalent_smoke.py` or re-defer                 |

## AC-PM2 — Do not reopen

- `R3-B2.75-PLAN-01` is **RESOLVED** (planning gate only). Execute must **not** treat plan closure as live pilot PASS.
- Batch 2.5 staged evidence remains staged-only until this Execute produces live sandbox evidence.

## AC-PM3 — Not-in-scope (explicit)

| Item                             | Batch          | Reason                            |
| -------------------------------- | -------------- | --------------------------------- |
| Batch 3 / `019` Layer 2 modeling | Batch 3        | Out of scope per MASTER §3.2      |
| Migration 008 / `B2.5-O-06`      | Batch 6        | Not Batch 2.75 closeout           |
| Ingestion split R2b–R2d          | Post PR        | Sprint mutex — see below          |
| `qmd data` production CLI        | Batch 6        | Not authorized                    |
| cninfo optional pilot            | Deferred       | Not in three-request set          |
| Production clean DB write        | Not authorized | Default `allow_clean_write=false` |

## AC-PM4 — Sprint mutex (ingestion R2b–R2d)

Per `layer1_ingestion_refactor_rollback_plan.md` §6 and authorization §Sprint constraint: **this sprint does not start ingestion R2b–R2d split**. Live pilot uses new `live_pilot.py` orchestration only; **must not** modify `backend/app/layer1_axes/ingestion.py`.

## ROUND3_BATCH_IMPLEMENTATION_MAP alignment

- Batch 2.75 placed after Batch 2.5, before Batch 3.
- Bundle §4.2 sources loaded per `implement.jsonl`.
- Closeout must end in exactly one `PILOT_*` state with registry updates.

## Phase -1 outcome

Registry read complete. Five tracked IDs mapped. Proceed to §8.2 Phase 0 authorization wiring.
