# Integration ledger — round3v-contract-drift-write-modes

> Plan 5c · v3 context packing

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
| ------ | -------- | -------- | ------------- | --------------- | ----------- |
| `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/BATCH_3V_HARDENING_RULES.md` | decision | summary+pointer | MASTER §0 | no production-live / no registry agent close | AC-BOUND |
| `docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/B02_01_contract_drift_and_write_modes.md` | business | pointer | MASTER §2 | VR-OPS/WRITE AC | AC-OPS-DRIFT |
| `specs/contracts/ops_db_inspect_contract.yaml` | contract | pointer | MASTER §5 | key_tables + deferred SSOT | AC-OPS-DRIFT |
| `specs/contracts/write_contract.yaml` | contract | pointer | MASTER §5 | implemented/reserved split | AC-WRITE-SPLIT |
| `docs/architecture/module_boundary_matrix.md` | architecture | pointer | MASTER §3 | ops/db boundary | AC-BOUND |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | rule | summary+pointer | MASTER §5 | five-field docstrings | AC-EVIDENCE |
| `backend/app/ops/db_inspector.py` | wiring | pointer | MASTER §4 | contract loader target | §9.1–9.2 |
| `backend/app/db/write_manager.py` | wiring | pointer | MASTER §4 | SUPPORTED_MODES parity | §9.3–9.5 |
| `research/vertical-slices.md` | rule | inline | MASTER §8 | OPS/WRITE slices | §8 |
| `docs/quality/staged_acceptance_policy.md` | decision | pointer | MASTER §0 | staged-only posture | AC-BOUND |
