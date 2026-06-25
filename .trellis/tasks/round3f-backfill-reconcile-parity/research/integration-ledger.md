# Integration ledger — round3f-backfill-reconcile-parity

> Plan 5c · v3 context packing

## ledger

| source                                            | category     | strategy        | master_anchor | execute_extract                 | for_ac_step    |
| ------------------------------------------------- | ------------ | --------------- | ------------- | ------------------------------- | -------------- |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` Batch 3F.4    | business     | pointer         | MASTER §2     | R3F-BR-01..05                   | AC-BR-\*       |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.6+§8.5      | decision     | summary+pointer | MASTER §0     | path index + PASS cmds          | AC-BR-PLAYBOOK |
| `BATCH_3F_HARDENING_RULES.md`                     | rule         | summary+pointer | MASTER §1.3   | no production write             | §1.5           |
| `MIGRATION_MAP.md`                                | architecture | pointer         | MASTER §2     | sync module placement           | §4             |
| `specs/contracts/sync_job_contract.yaml`          | contract     | pointer         | MASTER §5     | job matrix                      | BR-04          |
| `docs/adr/ADR-023-layer5-conflict-review-path.md` | decision     | pointer         | MASTER §9.5   | R3-PARTIAL-4                    | BR-05          |
| `research/vertical-slices.md`                     | rule         | inline          | MASTER §8     | BR-01..05                       | §8             |
| `backend/app/sync/orchestrator.py`                | wiring       | inline          | MASTER §9.4   | handler registry (E11 deferred) | BR-04          |
| `GLOBAL_TESTING_POLICY.md`                        | rule         | summary+pointer | MASTER §5     | 五字段                          | AC-BR-TEST     |
