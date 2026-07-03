# Batch 3V — Verified Audit Cleanup

> **Canonical batch entrypoint** for Round 3V after `PROJECT_IMPLEMENTATION_ROADMAP.md`.  
> **Audit source:** `quant_monitor_desk_verified_audit_report_2026-06-25_v3` (`VR-*` findings).  
> **Coordinator playbook:** `BATCH_3V_COORDINATOR_PLAYBOOK.md`（执行前必读）。  
> **Production posture:** no production clean write; no production-ready claim; no live source fetch.

---

## 1. Batch purpose

Close or precisely re-defer verified audit findings that affect **trust in later production gates** — contract drift, fail-closed validation, atomic raw writes, sync job semantics, registry/manifest alignment, and Layer5/model schema reconcile.

This batch does **not** enable production ingestion, live sources, Round 4 productization, or Round 5 release security.

---

## 2. Canonical task cards

| Batch order | Playbook ID  | Card                                                    | Owns `VR-*`                  | Track        |
| ----------- | ------------ | ------------------------------------------------------- | ---------------------------- | ------------ |
| 01          | **B3V-OPS**  | `B02_01_contract_drift_and_write_modes.md`              | `VR-OPS-001`, `VR-WRITE-001` | complex §4   |
| 02          | **B3V-DATA** | `B02_02_schema_hash_fail_closed.md`                     | `VR-DATA-001`                | complex §4   |
| 03          | **B3V-STOR** | `B02_03_rawstore_atomic_write.md`                       | `VR-STOR-001`                | complex §4   |
| 04          | **B3V-SYNC** | `B02_04_sync_job_support_and_recovery.md`               | `VR-SYNC-002`, `VR-SYNC-001` | complex §4   |
| 05          | **B3V-REG**  | `B02_05_migration_registry_and_manifest_consistency.md` | `VR-REG-001`, `VR-DOC-001`   | debt-lite §5 |
| 06          | **B3V-L5R**  | `B03_01_layer5_model_schema_reconcile.md`               | `VR-L5-001`, `VR-MODEL-001`  | debt-lite §5 |

---

## 3. Mandatory companion files

| File                                                                           | Purpose                                                                    |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| `BATCH_3V_TASK_CARD_MANIFEST.md`                                               | Card inclusion, dependencies, branch ownership                             |
| `BATCH_3V_HARDENING_RULES.md`                                                  | Batch-level safety rules                                                   |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md`                                             | Main-session worktree, file locks, merge order, PASS gates                 |
| `BATCH_3V_SELF_CHECK.md`                                                       | Static self-check before dispatch (like Batch 01 `FIRST_BATCH_SELF_CHECK`) |
| `BATCH_3V_ADVERSARIAL_AUDIT.md`                                                | Task-card adversarial audit + hardening bindings                           |
| `docs/quality/coordination/BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md`               | Zero-open closure policy                                                   |
| `docs/quality/coordination/BATCH_3V_PLAYBOOK_ADVERSARIAL_AUDIT.report.md`      | Playbook adversarial audit closure                                         |
| `docs/quality/coordination/BATCH_3V_COORDINATOR_PLAYBOOK_POINTER.md`           | Coordination-dir index to canonical playbook                               |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | `VR-*` routing index                                                       |

Executors must read all companion files before `/to-issues` or opening a worktree.

---

## 4. Execution order (recommended)

1. Read this README + manifest + hardening + coordinator playbook.
2. **B3V-REG** and **B3V-L5R** may start first (read-only / docs-registry).
3. **B3V-OPS** before broad sync/write crash-window edits.
4. **B3V-DATA** before any future clean-write rehearsal.
5. **B3V-STOR** before larger raw/staging persistence work.
6. **B3V-SYNC** before `qmd data` / CLI exposes job types.
7. Batch closeout: every owned `VR-*` → RESOLVED or precise re-defer with owner, phase, closure test.

---

## 5. Closure report (every branch)

1. Branch / worktree / task ID
2. What changed
3. What did not change
4. Test commands and results
5. ResourceGuard status
6. Source authorization status (must be N/A — no live fetch)
7. Production DB mutation proof or no-touch statement
8. Registry updates (resolved / re-defer / none)
9. Remaining risks and next gate

---

## 6. Routed elsewhere (not in this batch)

| `VR-*`                                                               | Routed to |
| -------------------------------------------------------------------- | --------- |
| `VR-DATAHEALTH-001`, `VR-RG-001`, `VR-L1PERF-001`, `VR-PERF-001`     | Round 3F  |
| `VR-API-001`, `VR-FE-*`, `VR-AGENT-001`, `VR-BT-001`, `VR-NOTIF-001` | Round 4   |
| `VR-SEC-001`                                                         | Round 5   |

See parent `../README.md` and `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3V routing table.
