# Round 3F — Batch6 Data Governance Task Cards

> Roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3F.  
> Current executable entrypoint: `BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`.  
> Scope: Batch6 data governance, source health, ResourceGuard, performance, backfill/reconcile, lineage/Layer3 hygiene closure, and ops hygiene.

---

## 1. Canonical entrypoint

Start here:

- `BATCH_3F_BATCH6_DATA_GOVERNANCE/README.md`
- `BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_TASK_CARD_MANIFEST.md`
- `BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_COORDINATOR_PLAYBOOK.md`
- `BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`
- `BATCH_3F_BATCH6_DATA_GOVERNANCE/BATCH_3F_HARDENING_RULES.md`

The roadmap owns the actual forward plan. This folder is the execution package for Round 3F.

---

## 2. Verified audit additions

| Card                                     | Owns                                                             | Roadmap batch |
| ---------------------------------------- | ---------------------------------------------------------------- | ------------- |
| `R3F_verified_audit_ops_perf_hygiene.md` | `VR-DATAHEALTH-001`, `VR-RG-001`, `VR-L1PERF-001`, `VR-PERF-001` | 3F.3 and 3F.5 |

---

## 3. Newly centralized Batch6 gaps

The Batch 3F package now also centralizes:

- `ADV-R3X-LINEAGE-001`
- `R3Y-LINEAGE-VR-001`
- `R3-B6-021-O-01`
- `R3-B6-021-O-02`
- `B2.5-O-05` live FRED primary
- `R2-RISK-2`
- `R2-RISK-3` registry consistency
- `R3-AUDIT-DEF-01/02/03`
- `R3-PARTIAL-4` registry closeout
- `R3-PARTIAL-5` no-reopen guard
- `PROMPT_03/04/05`
- `R3-B25-INGEST-SPLIT-R2B`
- `WAVE-B-HYG-01/02/03`

---

## 4. Boundary

Do not use Round 3F cards to implement Round4 API/frontend/Agent/notifications or Round5 release security gates. Do not enable production clean write; Round 3G owns that gate.
