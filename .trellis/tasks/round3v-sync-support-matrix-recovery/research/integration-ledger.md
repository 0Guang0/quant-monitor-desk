# Integration ledger — round3v-sync-support-matrix-recovery

> Plan 5c · v3 context packing

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
|--------|----------|----------|---------------|-----------------|-------------|
| `B02_04_sync_job_support_and_recovery.md` | business | pointer | MASTER §2 | VR-SYNC AC | AC-SYNC-002/001 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.5 | decision | summary+pointer | MASTER §0 | file locks OPS read-only | AC-SYNC-PLAYBOOK |
| `specs/contracts/sync_job_contract.yaml` | contract | pointer | MASTER §5 | implemented/reserved | SYNC-01 |
| `specs/contracts/write_contract.yaml` | contract | read-only | MASTER §1.3 | crash-window 只读 | SYNC-05 |
| `MIGRATION_MAP.md` | architecture | pointer | MASTER §4 | sync 模块放置 | §4 |
| `specs/context/authority_graph.yaml` | wiring | pointer | MASTER §4 | sync 模块 authority | §9 impact |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | decision | summary+pointer | MASTER §2 | COMPLETED 顺序 | SYNC-05 |
| `research/vertical-slices.md` | rule | inline | MASTER §8 | SYNC-BOOT..05 + 06A/B/C | §8 |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §6 | rule | pointer | MASTER §8–§9 | SYNC-06 拆票 SSOT | §9.6–9.8 |
| `GLOBAL_TESTING_POLICY.md` | rule | summary+pointer | MASTER §5 | 五字段 | AC-SYNC-TEST |
