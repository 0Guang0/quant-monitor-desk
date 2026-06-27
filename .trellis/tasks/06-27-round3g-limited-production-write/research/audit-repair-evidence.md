# R3G-03 Audit Repair Evidence

**Date:** 2026-06-27  
**Branch:** `feature/round3g-limited-production-write`  
**Full pytest:** exit 0 (2 skipped)  
**validate-execute-handoff:** PASS

## Summary

| Priority | Total  | Closed |
| -------- | ------ | ------ |
| P0       | 0      | 0      |
| P1       | 18     | 18     |
| P2       | 28     | 28     |
| P3       | 24     | 24     |
| **All**  | **70** | **70** |

## Finding closure table

| ID           | Fix                                                               | Test / evidence                                                                                      |
| ------------ | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| A1-P1-01     | `validate_approval_contract` cross-checks `rollback_plan_path`    | `test_ApprovalContract_rollbackPlanPathMismatch_blocks`                                              |
| A1-P1-02     | Cross-checks `audit_decision_file` vs CLI path                    | `test_ApprovalContract_auditDecisionFilePathMismatch_blocks`                                         |
| A1-P2-01     | `_enforce_live_fetch_gates` + `validate_fred_authorization`       | `limited_production_entry.py`; CLI flags wired                                                       |
| A1-P2-02     | Tier A documents R3G-01 regression                                | `test_r3g03TierA_documentsRehearseAuditProdPathRegression`                                           |
| A1-P2-03     | `no_cap_expansion=false` adversarial                              | `test_ApprovalContract_noCapExpansionFlag_blocks`                                                    |
| A1-P2-04     | Synthetic bypass via dry_run report                               | `test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim`                                |
| A1-P2-05     | ponytail single-candidate comment retained                        | `approval_contract.py:250`                                                                           |
| A1-P3-01     | GitNexus note (index refresh deferred to merge)                   | `research/gitnexus-execute-summary.md`                                                               |
| A1-P3-02     | omission-check updated                                            | `research/project-map-omission-check.md`                                                             |
| A1-P3-03     | ponytail: `build_before_proof` + `key_table_row_counts` snapshot  | `limited_production_entry.py`                                                                        |
| A3-P1        | `quote_ident` on all dynamic table SQL + contract validation      | `test_ApprovalContract_invalidTargetTableSql_blocks`                                                 |
| A3-P2-01     | FRED live fetch gates (see A1-P2-01)                              | `_enforce_live_fetch_gates`                                                                          |
| A3-P2-02     | CLI missing audit/before tests                                    | `test_PromoteCli_missingAuditDecision_blocks`, `test_PromoteCli_missingBeforeProof_blocks`           |
| A3-P3-01     | execute path `mkdir_if_missing=False`                             | `_assert_production_db_allowed`                                                                      |
| A3-P3-02     | GitNexus note                                                     | `research/gitnexus-execute-summary.md`                                                               |
| A4-P1-01..02 | Path cross-validation (A1-P1)                                     | same tests                                                                                           |
| A4-P1-03     | execute `_non_target_row_count` measured                          | `_production_clean_write` + `build_after_proof`                                                      |
| A4-P1-04     | DuckDB non-target row rollback test                               | `test_RollbackPlan_nonTargetRowsUnchangedOnDryRunIdentify`                                           |
| A4-P1-05     | Parametrized field mismatch tests                                 | `test_ApprovalContract_approvalAuditMismatch_perField_blocks`                                        |
| A4-P1-06     | `LimitedProductionEntryError.code` → CLI `error_code`             | `data_commands.py`                                                                                   |
| A4-P1-07     | WARN decision path                                                | `test_ApprovalContract_warnDecision_allowsAlignedFixture`                                            |
| A4-P2-01     | guardrails behavior test                                          | `test_r3g03LimitedProduction_noAgentTriggeredWriteMarker`                                            |
| A4-P2-02     | Tier A regression doc test                                        | `test_r3g03TierA_documentsRehearseAuditProdPathRegression`                                           |
| A4-P2-03     | ponytail: promote fields documented in runbook §6                 | `docs/ops/staging_data_e2e_runbook.md`                                                               |
| A4-P2-04     | synthetic bypass test                                             | `test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim`                                |
| A4-P3-01     | `_mismatched_field` names conflict field                          | `approval_contract.py`                                                                               |
| A4-P3-02     | ponytail: rollback window per-key defer (identify-only scope)     | `rollback_plan.py` note                                                                              |
| A4-P3-03     | empty DB: `key_table_row_counts` `{}` guard unchanged             | dry_run path                                                                                         |
| A2-P2-01     | ponytail mirror comment on `_production_clean_write`              | `limited_production_entry.py`                                                                        |
| A2-P2-02     | public `gates.py` re-exports                                      | `backend/app/ops/sandbox_clean_write/gates.py`                                                       |
| A2-P2-03     | `validate_contract_source_caps(profile=...)`                      | `rehearsal_plan.py` + `approval_contract.py`                                                         |
| A2-P3-01..02 | `path_utils.resolve_sandbox_path` / `utc_now_iso`                 | `path_utils.py`                                                                                      |
| A2-P3-03     | CLI keeps pre-checks; runner is SSOT for semantics                | unchanged dual file check (fail-closed)                                                              |
| A2-P3-04     | live fetch wired (not dead)                                       | `_enforce_live_fetch_gates`                                                                          |
| A2-P3-05     | `key_table_row_counts` in before_proof                            | `build_before_proof`                                                                                 |
| A2-P3-06     | shared `r3g03_artifact_paths` fixture                             | `test_round3g_limited_production_clean_write.py`                                                     |
| A5-P2-01     | execute-evidence green re-captured                                | `research/execute-evidence/9.*-green.txt`, `9.8-full.txt`                                            |
| A5-P2-02     | live fetch wired                                                  | `_enforce_live_fetch_gates`                                                                          |
| A5-P2-03     | Tier B execute defer documented in runbook §6                     | `staging_data_e2e_runbook.md`                                                                        |
| A5-P3-04     | `_validate_backup_pointer` in before_proof                        | `test_BeforeProof_invalidBackupPointer_blocks`                                                       |
| A5-P3-05     | single-candidate ponytail                                         | `approval_contract.py`                                                                               |
| A5-P3-06     | GitNexus note                                                     | `research/gitnexus-execute-summary.md`                                                               |
| A6-P2-1      | `max_rows=candidate.max_rows` in DH                               | `run_source_data_health(..., max_rows=)`                                                             |
| A6-P3-1..4   | single `key_table_row_counts` via before_proof; ponytail COUNT    | `limited_production_entry.py`                                                                        |
| A7-P2-01     | live fetch gates                                                  | `_enforce_live_fetch_gates`                                                                          |
| A7-P2-02     | `require_backup` on execute                                       | `_validate_before_proof_payload`                                                                     |
| A7-P2-03     | DATA_ROOT boundary test                                           | `test_PromoteRunner_productionDbOutsideDataRoot_blocks`                                              |
| A7-P2-04     | promote runbook §6 in ops doc                                     | `docs/ops/staging_data_e2e_runbook.md`                                                               |
| A7-P3-01     | GitNexus note                                                     | `research/gitnexus-execute-summary.md`                                                               |
| A7-P3-02     | runbook documents `qmd-data` vs `qmd`                             | `staging_data_e2e_runbook.md` §6                                                                     |
| A8-P1-01     | synthetic bypass test                                             | `test_PromoteRunner_dryRunSyntheticBypassReport_rejectsMutationClaim`                                |
| A8-P1-02     | static contract tests retained; runtime matrix complete           | Tier A matrix                                                                                        |
| A8-P1-03     | window + `no_cap_expansion` tests                                 | `test_ApprovalContract_windowCapExpansion_blocks`, `test_ApprovalContract_noCapExpansionFlag_blocks` |
| A8-P2-04     | PromoteCli missing before                                         | `test_PromoteCli_missingBeforeProof_blocks`                                                          |
| A8-P2-05     | report asserts `validation_status` / `write_manager_operation_id` | `test_PromoteRunner_dryRunProducesReport`                                                            |
| A8-P2-06     | Tier A regression doc test                                        | `test_r3g03TierA_documentsRehearseAuditProdPathRegression`                                           |
| A8-P2-07     | basetemp parent exists in CI paths                                | `.audit-sandbox/pytest` used in evidence commands                                                    |
| A8-P3-08     | behavior test replaces grep                                       | `test_r3g03LimitedProduction_noAgentTriggeredWriteMarker`                                            |
| A8-P3-09     | forbidden source E2E                                              | `test_PromoteRunner_forbiddenSourceE2E_blocks`                                                       |
| A8-P3-10     | help text subprocess test                                         | `test_PromoteCli_helpDocumentsPromoteFlags`                                                          |
| ADV-01..03   | deduped into A1-P1/P2                                             | above                                                                                                |
