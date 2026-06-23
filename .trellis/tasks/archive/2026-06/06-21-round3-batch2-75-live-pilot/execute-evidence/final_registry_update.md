# Batch 2.75 Registry Update — Execute Closeout

> **Date:** 2026-06-21  
> **Pilot closeout state:** `PILOT_FAIL_SOURCE`

## Batch 3 handoff template (MASTER section 11)

```
Layer 1 observation ingestion bridge: PASS (Batch 2.5 staged)
Ingestion type: staged | user-authorized live (partial) | production live
Allowed downstream use: limited — sandbox live shape facts for Request 1 and Request 3 only
Allowed indicator scope: ENV-E1-DGS10 akshare macro shape probe only (not FRED primary)
Allowed as_of window: 2026-06-21 pilot window (recent 5 trading days equity; recent 7 calendar days macro)
Remaining data limitations: Request 2 Eastmoney hist unreachable; B2.5-O-05 FRED primary deferred; perf budget RE_DEFERRED
Pilot closeout state: PILOT_FAIL_SOURCE
Reference: docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md until explicit production-live closeout
```

## AC-REG-2 checklist

| Registry                                 | Action                                                          | Item                                        |
| ---------------------------------------- | --------------------------------------------------------------- | ------------------------------------------- |
| `UNRESOLVED_ISSUES_REGISTRY.md`          | Remove `R3-B2.75-01` deferred row; add `R3-B2.75-REQ2-EM` defer | Pilot executed; Request 2 endpoint open     |
| `AUDIT_DEFERRED_REGISTRY.md`             | Move `R3-B2.75-01` → RESOLVED; add `R3-B2.75-REQ2-EM` DEFERRED  | Closeout evidence linked                    |
| `RESOLVED_ISSUES_REGISTRY.md`            | Add `R3-B2.75-01` with `PILOT_FAIL_SOURCE`                      | Does not open production-live               |
| `ROUND3_BATCH25_PENDING_FIX_REGISTRY.md` | Note partial live execution                                     | Request 1/3 sandbox evidence; not full PASS |

## Resolved by this closeout

### `R3-B2.75-01` / `GLOBAL-P2-01` (partial)

Controlled live pilot **executed** with sandbox raw evidence for three authorized requests. Closeout **`PILOT_FAIL_SOURCE`** because Request 2 original endpoint failed. Does **not** open formal production data access.

Evidence:

- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/final_pilot_closeout.md`
- `phase3_raw_micro_fetch_evidence.json`
- `phase4_validation_report.json`
- `phase3_no_production_mutation_proof.md`

## Re-deferred (unchanged or explicit)

| ID                      | Status         | Owner              | Phase           | Closure test                                                                              |
| ----------------------- | -------------- | ------------------ | --------------- | ----------------------------------------------------------------------------------------- |
| `B2.5-O-05`             | DEFERRED       | User / Batch 2.75+ | FRED primary    | Authorized FRED live; Request 3 shape-only does not close                                 |
| `R3-B25-PERF-BUDGET-01` | OPEN           | Execute / CI       | 4.5             | `phase45_perf_budget.json` RE_DEFERRED → smoke PASS                                       |
| `R3-B25-HYG-03`         | OPEN           | Execute / CI       | 4.5             | Same                                                                                      |
| `R3-B2.75-REQ2-EM`      | DEFERRED (new) | 018C probe         | Post Batch 2.75 | `stock_zh_a_hist` reachable or documented alternate in `018C_tdx_pytdx_low_cost_probe.md` |

## Batch 3 — cite / do not cite

**May cite:**

- baostock sandbox live raw structure (Request 1)
- akshare macro supplementary shape rows for `DGS10` probe (Request 3)
- Route preview READY matrix and fail-closed gate behavior

**Must not cite:**

- Request 2 as Eastmoney hist PASS
- Sina `stock_zh_a_daily` sidecar as validation-path success
- `PILOT_PASS_RAW_ONLY` or production-live readiness
- Perf smoke as live authorization

**Future probe boundary:** `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md` — not Batch 2.75.
