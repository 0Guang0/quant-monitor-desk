# Adversarial Audit Report — PROMPT_14 Staged Pilot (Agent A)

> **Generated:** 2026-06-22  
> **Baseline:** `master` @ `5c16c675` (post PROMPT_14+17 merge)  
> **Scope:** `staged_pilot.py`, `staged_pilot_fetch_ports.py`, `run_staged_pilot.py`, `test_staged_pilot.py`, execute-evidence  
> **Verdict:** **WARN** — minimum staged pilot done criteria met; data-safety and evidence gaps block sample expansion

---

## Slice 2 closeout (registry/docs) — 2026-06-22

| ID | Status | Fix |
|----|--------|-----|
| ADV-POST14-A-009 | **CLOSED@Slice2** | `R3-PROMPT14-AKSHARE-VAL-01` in `AUDIT_DEFERRED_REGISTRY.md` + `UNRESOLVED_ISSUES_REGISTRY.md` |
| ADV-POST14-A-010 | **CLOSED@Slice2** | REQ2-EM cross-ref on `R3-B2.75-REQ2-EM` + new defer row; **not closed** |
| ADV-POST14-A-016 | **CLOSED@Slice2** | `R3-PROMPT14-STAGED-01` RESOLVED + `pilot_closeout.json` evidence path in registries |

---

## §0 Context (Phase 0)

See coordinator handoff: PROMPT_14/16 task cards, prior `adversarial_audit_report.md`, ponytail scan, merge gates for PROMPT_15/16, PROMPT_14 execute-evidence (`PILOT_PASS_STAGED_RAW`).

---

## §1 Executive Summary

| Metric | Value |
|--------|-------|
| Verdict | **WARN** |
| Total findings | **19** |
| HIGH | **2** |
| MEDIUM | **10** |
| LOW | **7** |
| REGRESSION | **1** |
| STILL-OPEN (cross-ref) | **2** |

---

## §2 Findings

### HIGH

#### ADV-POST14-A-001 | vulnerability | HIGH | NEW

Production DB absent → no-mutation proof is vacuous pass (`mutation_proof.py` returns `{}`; `db_hash_unchanged: true` with no file).

**Fix:** `proof_status=INCONCLUSIVE` when DB missing; or require read-only production DB snapshot before pilot.

#### ADV-POST14-A-002 | gap | HIGH | NEW

No conflict / source divergence evidence (required by R3X_real_data_staged_pilot §3.7, production_live_pilot_policy §6).

**Fix:** Run `SourceConflictValidator` or explicit `NO_CONFLICT_CHECK_DEFERRED` artifact.

### MEDIUM

| ID | Title | Class |
|----|-------|-------|
| ADV-POST14-A-003 | cninfo via akshare vendor; source attribution `cninfo` | NEW |
| ADV-POST14-A-004 | Dual file_registry path (WriteManager + staged bypass); STAGED vs pending_validation | REGRESSION |
| ADV-POST14-A-005 | Authorized `date_window` not bound to fetch (14 calendar days hardcoded) | NEW |
| ADV-POST14-A-006 | Validation is shallow JSON only; no DbValidationGate / quality rules | NEW |
| ADV-POST14-A-007 | Sandbox stub `can_write_clean=True` | NEW |
| ADV-POST14-A-008 | `_ExplicitSourceRoutePlanner` masks organic route_status | NEW |
| ADV-POST14-A-009 | akshare re-defer not in AUDIT_DEFERRED_REGISTRY | **CLOSED@Slice2** |
| ADV-POST14-A-010 | akshare `stock_zh_a_hist` same family as R3-B2.75-REQ2-EM (must stay DEFERRED) | **CLOSED@Slice2** (cross-ref only) |
| ADV-POST14-A-011 | Missing tests: fail-closed paths, mock fetch success | NEW |
| ADV-POST14-A-012 | `test_production_live_pilot_policy.py` lacks staged pilot coverage | NEW |

### LOW

ADV-POST14-A-013 through ADV-POST14-A-019: absolute paths in evidence, global `_NETWORK_BUDGET`, LiveFetchPort naming, closeout narrative, taxonomy class names, weak cninfo validation, auth filename substring gate.

---

## §3 Cross-check vs PROMPT_14 Done Criteria

| Criterion | Status |
|-----------|--------|
| ≥1 source staged/raw evidence | PASS |
| Failed sources explained | **PASS@Slice2** (registry updated) |
| no-mutation proof | WEAK PASS |
| route preview | PASS |
| validation / conflict | PARTIAL |
| no production-live claim | PASS |
| R3-B2.75-REQ2-EM not closed | PASS |

---

## §4 Recommended Fix Priority

1. ADV-POST14-A-001 — no-mutation proof fail-closed when DB absent  
2. ADV-POST14-A-002 — conflict evidence or explicit defer  
3. ~~ADV-POST14-A-009 + A-010~~ — **Slice 2 done**  
4. ADV-POST14-A-004 — single file_registry path  
5. ADV-POST14-A-011 + A-012 — tests  
6. A-003, A-005, A-006, A-007 — attribution, date window, validators, stub flags  
7. LOW batch

---

## Top 5 Blockers

1. ADV-POST14-A-001 — empty no-mutation proof  
2. ADV-POST14-A-002 — no conflict evidence  
3. ADV-POST14-A-010 — REQ2-EM family failure (**registry cross-ref only; remains DEFERRED**)  
4. ADV-POST14-A-004 — dual file_registry path  
5. ADV-POST14-A-011 — missing critical-path tests
