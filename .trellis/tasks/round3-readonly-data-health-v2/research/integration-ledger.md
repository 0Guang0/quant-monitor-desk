# Integration ledger — round3-readonly-data-health-v2

> Plan 5c · v3 context packing

## ledger

| source | category | strategy | master_anchor | execute_extract | for_ac_step |
| --- | --- | --- | --- | --- | --- |
| `docs/quality/production_live_pilot_policy.md` | decision | summary+pointer | MASTER §0 | no production-live | AC-DH2-BOUND |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_readonly_data_health_v2.md` | business | pointer | MASTER §2 | v2 profiles AC | AC-DH2-PROFILE |
| `specs/contracts/data_quality_rules.yaml` | contract | pointer | MASTER §5 | rule_id semantics | AC-DH2-FRED |
| `docs/architecture/module_boundary_matrix.md` | architecture | pointer | MASTER §3 | ops boundary | AC-DH2-BOUND |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | rule | summary+pointer | MASTER §5 | semantic asserts | AC-DH2-TEST |
| `backend/app/ops/data_health.py` | wiring | pointer | MASTER §4 | v1 base extend | §9.0+ |
| `backend/app/ops/staged_pilot.py` | wiring | pointer | MASTER §3 | manifest constants read-only | §9.4 |
| `research/vertical-slices.md` | rule | inline | MASTER §8 | DH2-BASE..07 | §8 |
| `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md` | decision | summary+pointer | MASTER §0 | hard stops | AC-DH2-BOUND |
