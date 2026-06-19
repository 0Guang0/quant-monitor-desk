# Round 2.5 Repair Alignment Tracker

> **Status:** in progress · **Gate:** must PASS before opening Trellis task **017** (Round 3 Layer 1)  
> **Trellis task:** `.trellis/tasks/06-19-round2-repair-alignment/`  
> **Baseline:** `master` post PR #14 (repaired-docs import)  
> **Master registry:** [`AUDIT_DEFERRED_REGISTRY.md`](../AUDIT_DEFERRED_REGISTRY.md) — every issue **RESOLVED** or **DEFERRED** with resolution phase

## Issue resolution policy

1. **全清 or 记录延后** — no undocumented open issues.
2. **不阻塞 ≠ 不解决** — deferred rows must name **resolution phase**, **task hook**, and **closure test** (see registry).
3. **017 gate:** only `PROC-R2.5-1` (merge/handoff) may block; all other pre-R3 items must be DEFERRED with phase in registry.

---

## Round 2.5 scope (R2.5-1 … R2.5-6) — **blocks 017 until merged**

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| R2.5-1 | `DISABLED_SOURCE` + D-11 domain gating | **DONE** | `source_registry.py`, `base_adapter.py`, tests |
| R2.5-2 | `schema.sql` migration **007** `write_audit_log` columns | **DONE** | `schema.sql`, `test_schema_contract.py` |
| R2.5-3 | `load_api_limits()` query budget authority | **DONE** | `api_limits.py`, `test_api_security_contract.py` |
| R2.5-4 | Doc honesty (handoff, gap ledger, tracker, registry policy) | **DONE** | linked docs |
| R2.5-5 | `test_legacySourceRoles_forbiddenAsSourceRoles` | **DONE** | `test_source_registry.py` |
| R2.5-6 | Domain schedulable **before** domain_allowed (`DISABLED_SOURCE` priority) | **DONE** | `base_adapter.py` · `test_fetch_disabledDomain_returnsDisabledSourceBeforeDomainAllowed` |
| PROC-R2.5-1 | Commit + PR + Trellis complete | **OPEN** | registry OPEN table · blocks 017 |

**Exit criteria:** pytest/ruff green · R2.5-1..6 DONE · `PROC-R2.5-1` RESOLVED.

---

## Round 3 PARTIAL repay — **DEFERRED** (registry IDs)

| ID | Resolution phase | Task hook |
|----|------------------|-----------|
| R3-PARTIAL-1 | Round 3 **early** ops | `DECISIONS.md` §11 · backfill validate+write or ADR |
| R3-PARTIAL-2 | Round 3 **early** (week 1–2) | D2-P1-2 · first FetchPort / `run_full_load` |
| R3-PARTIAL-3 | Round 3 **mid** | D2-P2-2 · `run_reconcile` re-fetch |
| R3-PARTIAL-4 | Round 3 **mid** | conflict UX ADR |
| R3-PARTIAL-5 | Round 3 **ops optional** | D-A2-3 |

Full columns: [`AUDIT_DEFERRED_REGISTRY.md`](../AUDIT_DEFERRED_REGISTRY.md) §DEFERRED Round 3.

---

## Round 4 deferred — **DEFERRED** (registry IDs R4-*)

Contract tests (`api_security` HTTP), notifications (**028**), frontend pages (**026–027**).  
Detail tables below; authoritative closure tests in registry.

### R4-API-SEC — task **024**

| Sub-ID | Contract test | Status | Resolution phase |
|--------|---------------|--------|------------------|
| R4-API-SEC-1 | `test_apiSecurityContract_isSingleAuthorityForQueryBudget` | **RESOLVED** (R2.5) | — |
| R4-API-SEC-2 | `test_resourceLimitsApiLimits_matchApiSecurityContract` | **RESOLVED** (R2.5) | — |
| R4-API-SEC-3..13 | HTTP / auth / startup / page size tests | **DEFERRED** | Round 4 · **024** |

### R4-NOTIF — task **028**

| Sub-ID | Item | Status | Resolution phase |
|--------|------|--------|------------------|
| R4-NOTIF-1..3 | throttle + dedup tests | **DEFERRED** | Round 4 · **028** |

### R4-FE — tasks **026** + **027**

| Sub-ID | Item | Status | Resolution phase |
|--------|------|--------|------------------|
| R4-FE-1 | `test_frontendPageContracts_doNotUseStale500Limit` | **DEFERRED** | Round 4 · **024**+**027** |
| R4-FE-2 | `/notifications` page | **DEFERRED** | Round 4 · **026**+**028** |
| R4-FE-3 | Layer 1–5 pages | **DEFERRED** | Round 4 · **027** |

---

## Post–Round 2 / Round 5 (summary)

| ID | Resolution phase |
|----|------------------|
| D2-P1-1, D2-P1-3, D2-P2-1, D2-P3-1 | Round 3 late / ops — registry |
| R2-GAP-2, R4-* | Round 4 — registry |
| R2-RISK-5 | Round 5 — registry |

---

## Related documents

- [`AUDIT_DEFERRED_REGISTRY.md`](../AUDIT_DEFERRED_REGISTRY.md) — **canonical** issue ledger
- [`REPAIR_IMPORT_CODE_GAP_LEDGER.md`](./REPAIR_IMPORT_CODE_GAP_LEDGER.md)
- [`ROUND2_GAPS_AND_DEVIATIONS.md`](../implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/ROUND2_GAPS_AND_DEVIATIONS.md)
- [`ROUND3_HANDOFF.md`](../ROUND3_HANDOFF.md)
