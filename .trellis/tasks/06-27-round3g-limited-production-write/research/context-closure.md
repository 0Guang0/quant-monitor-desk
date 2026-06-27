# Context closure — R3G-03

## Upstream wiring

- R3G-01 `rehearsal_runner` — gate chain mirror (DSS → RoutePlanner → ResourceGuard → DH → DbValidationGate → WriteManager)
- R3G-02 `audit_decision.py` — `AuditDecision` enum; promote reads `audit_decision.json` only
- `mutation_proof.key_table_row_counts` — before proof row counts
- `staged_pilot.validate_authorization` pattern — fail-closed approval YAML
- `implement.jsonl` 39 entries + frozen §9 + EXECUTION_INDEX §1–§3

## Deferred / out of scope

- Tier B prod-path (`--execute --no-dry-run` on real `production_db_path`) — requires user §6 approval; not run in CI
- Multi-source promote in one run — ponytail single-candidate pilot
- L1 ingestion allowlist expansion — **forbidden**

## Slice boundary

- Promote target = `production_db_path` from approval (under DATA_ROOT or `.audit-sandbox`)
- Default `dry_run=true`; `production_mutation_allowed=false` unless explicit execute
- rehearse/audit CLIs unchanged (`production_mutation_allowed=false` preserved)
- Rollback identify-only; no production DELETE in Execute
