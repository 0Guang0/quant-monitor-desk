# Round 3V — Verified Audit Cleanup

> Purpose: route and close the verified `VR-*` findings from `quant_monitor_desk_verified_audit_report_2026-06-25_v3` without mixing unrelated future work into one batch.  
> Roadmap anchor: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3V.  
> **Batch entrypoint:** `BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md`  
> **Coordinator playbook:** `BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`  
> Production posture: no production clean write, no production-ready claim, no live source enablement.

---

## 1. Batch map

| Round slice | Folder                                                     | Owns                                                                                                                              | Can run in parallel with                                              |
| ----------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Batch 3V.1  | `BATCH_3V_VERIFIED_AUDIT_CLEANUP/` cards `B02_01`–`B02_05` | contract drift, schema_hash, RawStore atomic writes, sync support matrix, migration registry reconcile, manifest/docs consistency | Batch 3V.2 read-only reconcile; Round 3F planning                     |
| Batch 3V.2  | `BATCH_3V_VERIFIED_AUDIT_CLEANUP/` card `B03_01`           | Layer5/model schema post-audit reconcile, not blind reimplementation                                                              | Batch 3V.1 if read-only; must fork if runtime/schema edits are needed |

Legacy folder names `BATCH_02_*` / `BATCH_03_*` are **redirect stubs only** — canonical cards live under `BATCH_3V_VERIFIED_AUDIT_CLEANUP/`.

Items routed to Round 3F / Round4 / Round5 have their own task cards in those Round folders.

---

## 2. Global execution rules

- Every branch must state exact `VR-*` IDs it owns.
- Do not close a `VR-*` item by implication; close only with exact evidence.
- If the latest project state already fixed a reported issue, create a reconciliation note and update registry/coverage; do not reimplement it.
- If a finding belongs to Round4 or Round5, do not implement it in Round 3V.
- Use `/to-issues`, `/tdd`, `/ponytail full`, `/karpathy-guidelines`, and `/testing-guidelines` before code changes.
- New/changed tests must state coverage scope, test object, and purpose/goal.
- Docs-only routing changes do not require full pytest; code tasks must run targeted tests and broader merge gates.
- **Execute Batch 3V only after reading** `BATCH_3V_COORDINATOR_PLAYBOOK.md`.

---

## 3. Forbidden scope

Round 3V must not:

- enable production clean write,
- fetch live data,
- enable FRED/TDX/QMT/Yahoo production sources,
- implement Round4 UI/API/Agent features,
- implement Round5 security CI except via explicit Round5 card,
- move Layer5 to production-ready without post-audit evidence,
- run full-market or full-history scans.
