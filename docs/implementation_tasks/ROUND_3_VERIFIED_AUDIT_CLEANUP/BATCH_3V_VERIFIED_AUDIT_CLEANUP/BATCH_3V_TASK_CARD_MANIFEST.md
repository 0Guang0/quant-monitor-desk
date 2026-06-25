# Batch 3V Task Card Manifest

> Batch: `BATCH_3V_VERIFIED_AUDIT_CLEANUP`  
> Scope: verified audit cleanup for `VR-*` items owned by Round 3V.1 and 3V.2.  
> Coordinator SSOT: `BATCH_3V_COORDINATOR_PLAYBOOK.md`.

---

## 1. Included task cards

| ID        | Card                                                    | Owns                         | Suggested branch                               | Track     | Predecessor          |
| --------- | ------------------------------------------------------- | ---------------------------- | ---------------------------------------------- | --------- | -------------------- |
| `B3V-C01` | `B02_01_contract_drift_and_write_modes.md`              | `VR-OPS-001`, `VR-WRITE-001` | `fix/round3v-contract-drift-write-modes`       | complex   | —                    |
| `B3V-C02` | `B02_02_schema_hash_fail_closed.md`                     | `VR-DATA-001`                | `fix/round3v-schema-hash-fail-closed`          | complex   | —                    |
| `B3V-C03` | `B02_03_rawstore_atomic_write.md`                       | `VR-STOR-001`                | `fix/round3v-rawstore-atomic-write`            | complex   | —                    |
| `B3V-C04` | `B02_04_sync_job_support_and_recovery.md`               | `VR-SYNC-002`, `VR-SYNC-001` | `fix/round3v-sync-support-matrix-recovery`     | complex   | B3V-C01 recommended  |
| `B3V-C05` | `B02_05_migration_registry_and_manifest_consistency.md` | `VR-REG-001`, `VR-DOC-001`   | `fix/round3v-registry-manifest-consistency`    | debt-lite | —                    |
| `B3V-C06` | `B03_01_layer5_model_schema_reconcile.md`               | `VR-L5-001`, `VR-MODEL-001`  | `review/round3v-layer5-model-schema-reconcile` | debt-lite | post Batch 01 master |

---

## 2. Dependency graph

```text
PROJECT_IMPLEMENTATION_ROADMAP (Round 3V)
  -> B3V-C05 registry/manifest (parallel)
  -> B3V-C06 Layer5/model reconcile (parallel, read-first)
  -> B3V-C01 contract/write modes
      -> B3V-C04 sync support (write crash-window)
  -> B3V-C02 schema_hash fail-closed
  -> B3V-C03 RawStore atomic write
```

---

## 3. Branch ownership

| Branch                                         | Owns                                                                                              | Must not own                                                |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `fix/round3v-contract-drift-write-modes`       | `ops_db_inspect_contract.yaml`, `db_inspector.py`, `write_contract.yaml`, write-mode parity tests | migration files, live fetch, production clean write         |
| `fix/round3v-schema-hash-fail-closed`          | `validation_gate.py`, adapter schema_hash path, related tests                                     | unrelated routing, production clean write                   |
| `fix/round3v-rawstore-atomic-write`            | `raw_store.py`, `path_compat.py`, atomic write tests                                              | FileRegistry semantics change unless test-proven            |
| `fix/round3v-sync-support-matrix-recovery`     | `sync_job_contract.yaml`, `orchestrator.py`, `runners.py`, sync deferred errors                   | `qmd data` CLI release, production clean write              |
| `fix/round3v-registry-manifest-consistency`    | registries, `MIGRATION_COVERAGE.md`, README/MANIFEST/docs alignment                               | rewriting migration 009 without proof                       |
| `review/round3v-layer5-model-schema-reconcile` | reconcile matrices, registry/docs updates                                                         | `layer5_evidence/**` runtime edits without dedicated branch |

---

## 4. Registry ownership (main session batch close)

| Registry row / `VR-*` | Close owner           | Notes                          |
| --------------------- | --------------------- | ------------------------------ |
| `VR-OPS-001`          | B3V-C01               | contract drift test            |
| `VR-WRITE-001`        | B3V-C01               | implemented vs reserved modes  |
| `VR-DATA-001`         | B3V-C02               | schema_hash fail-closed        |
| `VR-STOR-001`         | B3V-C03               | atomic raw write               |
| `VR-SYNC-002`         | B3V-C04               | support matrix                 |
| `VR-SYNC-001`         | B3V-C04 or Round 3F.4 | close or handoff               |
| `VR-REG-001`          | B3V-C05               | migration 009 coverage         |
| `VR-DOC-001`          | B3V-C05               | manifest/doc consistency       |
| `VR-L5-001`           | B3V-C06               | stale close or split follow-up |
| `VR-MODEL-001`        | B3V-C06               | designed vs implemented matrix |

Agents submit **proposed registry deltas**; main session reconciles `UNRESOLVED` / `RESOLVED` / `AUDIT_DEFERRED` rows.

---

## 5. Merge package

Recommended integration branch: `integration/round3-batch3v`

Merge order (Track A code + Track B reconcile):

| Order | ID      | Branch                                         |
| ----- | ------- | ---------------------------------------------- |
| 1     | B3V-C05 | `fix/round3v-registry-manifest-consistency`    |
| 2     | B3V-C06 | `review/round3v-layer5-model-schema-reconcile` |
| 3     | B3V-C01 | `fix/round3v-contract-drift-write-modes`       |
| 4     | B3V-C02 | `fix/round3v-schema-hash-fail-closed`          |
| 5     | B3V-C03 | `fix/round3v-rawstore-atomic-write`            |
| 6     | B3V-C04 | `fix/round3v-sync-support-matrix-recovery`     |

Full sequence and file locks: `BATCH_3V_COORDINATOR_PLAYBOOK.md` §7.
