# GitNexus Execute Summary — R3G-03

**Date:** 2026-06-27  
**Task:** 06-27-round3g-limited-production-write

## query: limited production sandbox clean write promote

GitNexus returned cross-community processes involving `staged_pilot`, `DbValidationGate`, `WriteManager`, and production gate scripts. R3G-03 promote reuses the same QMD gate chain as R3G-01 `rehearsal_runner` without opening rehearse/audit to production DB.

## impact() targets

| Symbol                                                             | Risk          | Notes                                                |
| ------------------------------------------------------------------ | ------------- | ---------------------------------------------------- |
| `run_rehearsal` / `run_sandbox_clean_write_rehearsal`              | LOW (no edit) | New modules only; rehearse CLI unchanged             |
| `write_audit_decision`                                             | LOW (no edit) | Promote reads decision JSON only                     |
| `build_production_mutation_proof` / `key_table_row_counts`         | LOW           | Read-only reuse in before/after proof                |
| `data_commands.sandbox_clean_write_*`                              | MEDIUM        | Added `promote` subcommand; rehearse/audit untouched |
| `approval_contract` / `rollback_plan` / `limited_production_entry` | NEW           | Direct blast radius = promote CLI + new tests        |

**No HIGH/CRITICAL warnings.** Rehearse/audit `production_mutation_allowed=false` preserved.

**Audit repair (2026-06-27):** Post-Execute symbols (`run_limited_production_entry`, `validate_approval_contract`) remain absent from stale index until `node .gitnexus/run.cjs analyze` at merge. Static review + `gates.py` public surface used for repair.

## Reuse decisions (frozen §4.1)

- Row counts: `mutation_proof.key_table_row_counts`
- Auth shape: `approval_contract` mirrors staged_pilot fail-closed pattern
- Gate chain: mirrored from `rehearsal_runner` with `ponytail:` ceiling (no third orchestrator extract)
- Rollback: new `rollback_plan.py`, identify-only dry-run
