# Vertical Slices — Round 3 Batch 2.75 (Plan 3.5 · to-issues)

> **Parent:** Trellis `06-21-round3-batch2-75-live-pilot` / `R3-B2.75-PROD-LIVE-PILOT` / `018B`  
> **Protocol:** tracer-bullet vertical slices — each slice is a thin end-to-end path (tests → orchestration → evidence), not a horizontal layer.  
> **Mapping:** MASTER §8.0–8.8 · strict serial Audit PH-B0–PH-B6  
> **Granularity:** 8 slices (AFK-heavy; one HITL gate before first live network fetch)

---

## Slice 1 — VS-1 — Fail-closed gate + authorization wiring

| Field          | Value                                                      |
| -------------- | ---------------------------------------------------------- |
| **Title**      | Authorization record + `LivePilotRequest` + RED gate tests |
| **Type**       | AFK                                                        |
| **Blocked by** | None — Batch 2.5 archived PASS; `R3-B2.75-PLAN-01` closed  |
| **MASTER**     | §8.1 Phase -1 / §8.2 Phase 0                               |
| **Item IDs**   | `R3-B2.75-PROD-LIVE-PILOT`, `R3-B2.75-01`                  |

### What to build

Wire the approved authorization file into a typed `LivePilotRequest` (or equivalent) and add **failing-first** tests proving: missing authorization blocks before route/fetch; disabled source blocks; route not `READY` blocks; sandbox target enforced; production DB path not writable by default.

### Acceptance criteria

- [ ] `docs/quality/batch275_user_authorization_2026-06-21.md` referenced by orchestration
- [ ] `tests/test_batch275_live_pilot_gate.py` RED then GREEN for fail-closed cases
- [ ] `execute-evidence/phase_minus1_reconciliation.md` lists five tracked IDs + not-in-scope note
- [ ] Audit PH-B0 PASS

---

## Slice 2 — VS-2 — Read-only production baseline

| Field          | Value                                                |
| -------------- | ---------------------------------------------------- |
| **Title**      | Phase 1 DB/data-root/source baseline (zero mutation) |
| **Type**       | AFK                                                  |
| **Blocked by** | Slice 1 (PH-B0 PASS)                                 |
| **MASTER**     | §8.3 Phase 1                                         |
| **Audit**      | PH-B1                                                |

### What to build

Capture read-only inventory of production `DATA_ROOT` and `quant_monitor.duckdb` **before** any pilot activity; snapshot source registry/capability status for the three approved requests; prove Phase 1 caused no mutation (hash/row-count).

### Acceptance criteria

- [ ] `execute-evidence/phase1_baseline_inventory.json` + `.md`
- [ ] Fields align with `ops_db_inspect_contract.yaml`
- [ ] `phase1_no_mutation_proof.md` documents before-only state
- [ ] `execute-evidence/phase1_capability_snapshot.json`
- [ ] Audit PH-B1 PASS

---

## Slice 3 — VS-3 — Route/capability dry-run matrix

| Field          | Value                                                       |
| -------------- | ----------------------------------------------------------- |
| **Title**      | Phase 2 route preview for 3 micro-pilot requests (no fetch) |
| **Type**       | AFK                                                         |
| **Blocked by** | Slice 2 (PH-B1 PASS)                                        |
| **MASTER**     | §8.4 Phase 2                                                |
| **Audit**      | PH-B2                                                       |

### What to build

For each approved request in authorization §3, run route preview + capability check + ResourceGuard decision **before** any live fetch. Persist JSON matrix; stop with failure evidence if status is not `READY` (unless documented `PILOT_FAIL_SOURCE` path).

### Acceptance criteria

- [ ] `execute-evidence/phase2_route_preview_matrix.json` covers requests 1–3
- [ ] No fixture/staged data satisfies this phase
- [ ] Production DB row counts unchanged vs Phase 1
- [ ] Audit PH-B2 PASS

---

## Slice 4 — VS-4 — HITL gate (before first network fetch)

| Field          | Value                          |
| -------------- | ------------------------------ |
| **Title**      | Phase 3 HITL user confirmation |
| **Type**       | **HITL**                       |
| **Blocked by** | Slice 3 (PH-B2 PASS)           |
| **MASTER**     | §8.5a Phase 3 HITL             |
| **Audit**      | PH-B3 (HITL sub-gate)          |

### What to build

Obtain explicit user confirmation before any outbound network call; produce `phase3_hitl_user_confirmation.md` with three-request summary and risk acknowledgment.

### Acceptance criteria

- [ ] `execute-evidence/phase3_hitl_user_confirmation.md` exists before fetch
- [ ] O-01 closed in MASTER §0.11

---

## Slice 5 — VS-5 — Raw-only live micro-fetches (all 3 requests)

| Field          | Value                                                         |
| -------------- | ------------------------------------------------------------- |
| **Title**      | Phase 3 sandbox raw-only fetch via `live_pilot` orchestration |
| **Type**       | AFK (code) + network                                          |
| **Blocked by** | Slice 4 (HITL signed)                                         |
| **MASTER**     | §8.5b Phase 3 fetch                                           |
| **Audit**      | PH-B3                                                         |

### What to build

Implement `backend/app/ops/live_pilot.py`: validate authorization → isolated sandbox → route gate → `dry_run=false` raw-only fetch via `DataSourceService` (not `StubFetchPort` / staged fixture). Execute all three approved requests.

### Acceptance criteria

- [ ] Sandbox root under `.audit-sandbox/batch275-live-pilot/`
- [ ] `execute-evidence/phase3_raw_micro_fetch_evidence.json` for requests 1–3
- [ ] Production clean DB delta = zero
- [ ] Request 2 does not upgrade Primary; Request 3 does not close FRED primary
- [ ] Audit PH-B3 PASS

---

## Slice 6 — VS-6 — Sandbox validation (no clean write)

| Field          | Value                                             |
| -------------- | ------------------------------------------------- |
| **Title**      | Phase 4 validation/conflict on raw pilot evidence |
| **Type**       | AFK                                               |
| **Blocked by** | Slice 5                                           |
| **MASTER**     | §8.6 Phase 4                                      |
| **Audit**      | PH-B4                                             |

### What to build

Run `DataQualityValidator` / `SourceConflictValidator` against sandbox raw evidence; **default plan: no clean write** (`allow_clean_write=false`). Produce validation and conflict reports; block any clean write on severe failure.

### Acceptance criteria

- [ ] `execute-evidence/phase4_validation_report.json` + `phase4_conflict_inspect.txt`
- [ ] No write to production DB; no sandbox clean write unless separately approved
- [ ] Audit PH-B4 PASS

---

## Slice 7 — VS-7 — Performance-budget evidence gate

| Field          | Value                                                   |
| -------------- | ------------------------------------------------------- |
| **Title**      | Phase 4.5 A6 smoke / perf artifact or explicit re-defer |
| **Type**       | AFK                                                     |
| **Blocked by** | Slice 6                                                 |
| **MASTER**     | §8.7 Phase 4.5                                          |
| **Item IDs**   | `R3-B25-PERF-BUDGET-01`, `R3-B25-HYG-03`                |

### What to build

Run bounded `scripts/production_equivalent_smoke.py` profile **or** document explicit re-deferral with owner/phase/closure test in registries. Must respect `GLOBAL_RESOURCE_LIMITS.md`.

### Acceptance criteria

- [ ] `execute-evidence/phase45_perf_budget.json` **or** registry re-defer row
- [ ] No production DB mutation; not used as live authorization
- [ ] Audit PH-B5 PASS

---

## Slice 8 — VS-8 — Closeout + Batch 3 handoff

| Field          | Value                                      |
| -------------- | ------------------------------------------ |
| **Title**      | Phase 5 `PILOT_*` decision + registry sync |
| **Type**       | AFK                                        |
| **Blocked by** | Slice 7                                    |
| **MASTER**     | §8.8 Phase 5                               |
| **Audit**      | PH-B6 + A1–A8                              |

### What to build

End in exactly one state: `PILOT_PASS_RAW_ONLY` (expected default), `PILOT_FAIL_*`, or `PILOT_REDEFERRED`. Update `AUDIT_DEFERRED_REGISTRY.md` + `UNRESOLVED_ISSUES_REGISTRY.md` (+ `RESOLVED` for precisely closed rows). Produce Batch 3 handoff note for `019` citing what source-shape facts may be referenced.

### Acceptance criteria

- [ ] `execute-evidence/final_pilot_closeout.md` + `final_registry_update.md`
- [ ] `B2.5-O-06`, `R3-B25-HYG-01/02`, Batch 6 CLI gates **not** closed unless separate evidence
- [ ] `test_batch25_production_data_gate.py` + policy tests remain green
- [ ] Full §9–§10 regression green

---

## Dependency graph

```text
VS-1 → VS-2 → VS-3 → VS-4 (HITL) → VS-5 → VS-6 → VS-7 → VS-8
```

## to-issues notes (no GitHub tracker)

This repo uses Trellis task + `vertical-slices.md` instead of GitHub issues (`plan.freeze.md` §3.8 waiver pattern from Batch 2.5).
