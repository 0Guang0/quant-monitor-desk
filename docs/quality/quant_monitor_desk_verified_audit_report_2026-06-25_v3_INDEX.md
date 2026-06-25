# Verified Audit Report v3 — Repository Index

> **Report ID:** `quant_monitor_desk_verified_audit_report_2026-06-25_v3`  
> **Purpose:** In-repo routing index for `VR-*` findings when the full report PDF/Markdown is not archived in git.  
> **Batch owner:** `BATCH_3V_VERIFIED_AUDIT_CLEANUP`  
> **Playbook:** `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_COORDINATOR_PLAYBOOK.md`

---

## 1. Batch 3V owned findings

| VR ID          | Batch card     | Branch                                         | Close action                     |
| -------------- | -------------- | ---------------------------------------------- | -------------------------------- |
| `VR-OPS-001`   | B02_01         | `fix/round3v-contract-drift-write-modes`       | contract drift test              |
| `VR-WRITE-001` | B02_01         | same                                           | implemented/reserved write modes |
| `VR-DATA-001`  | B02_02         | `fix/round3v-schema-hash-fail-closed`          | schema_hash fail-closed          |
| `VR-STOR-001`  | B02_03         | `fix/round3v-rawstore-atomic-write`            | atomic raw write                 |
| `VR-SYNC-002`  | B02_04         | `fix/round3v-sync-support-matrix-recovery`     | support matrix                   |
| `VR-SYNC-001`  | B02_04 or 3F.4 | same / handoff                                 | crash-window test or re-defer    |
| `VR-REG-001`   | B02_05         | `fix/round3v-registry-manifest-consistency`    | migration 009 coverage           |
| `VR-DOC-001`   | B02_05         | same                                           | manifest/doc consistency         |
| `VR-L5-001`    | B03_01         | `review/round3v-layer5-model-schema-reconcile` | stale close or split             |
| `VR-MODEL-001` | B03_01         | same                                           | designed vs implemented matrix   |

---

## 2. Routed out of Batch 3V

| VR ID                    | Routed to              | Card folder                       |
| ------------------------ | ---------------------- | --------------------------------- |
| `VR-DATAHEALTH-001`      | Round 3F.3             | `ROUND_3_BATCH6_DATA_GOVERNANCE/` |
| `VR-RG-001`              | Round 3F.5             | same                              |
| `VR-L1PERF-001`          | Round 3F.5             | same                              |
| `VR-PERF-001`            | Round 3F.5 / Round 5.2 | same                              |
| `VR-API-001`             | Round 4.1              | `ROUND_4_.../BATCH_04_.../B04_01` |
| `VR-FE-001`, `VR-FE-002` | Round 4.3              | `B04_03`                          |
| `VR-AGENT-001`           | Round 4.2              | `B04_02`                          |
| `VR-BT-001`              | Round 4.5              | `B04_05`                          |
| `VR-NOTIF-001`           | Round 4.4              | `B04_04`                          |
| `VR-SEC-001`             | Round 5.1              | `ROUND_5_.../B05_01`              |

See `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V routing table.

---

## 3. Known manifest gap (B3V-REG)

`MANIFEST.json` lists `FINAL_AUDIT_REPORT.md` with sha256; file **not present** at repo root as of Batch 3V planning. B02_05 must **restore from trusted source** or **update all references** to replacement closeout — never fabricate content (`VR-DOC-001`).

---

## 4. Full report archival

When the full verified audit report is checked in, place at:

`docs/quality/audits/quant_monitor_desk_verified_audit_report_2026-06-25_v3.md`

and add sha256 entry to `MANIFEST.json` via normal release manifest process.
