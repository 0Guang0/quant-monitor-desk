# PH-B1 Baseline Audit

## Conclusion

PASS

PH-B1 baseline and zero-mutation evidence satisfies `AUDIT.plan.md` §3.1 B1-1..B1-4. The Phase 1 capture is explicitly `production_read_only`, the production DuckDB opened read-only, the baseline inventory includes DB/schema/key-table/data-root state, the capability snapshot covers the three approved pilot requests, and the no-mutation proof records unchanged DB hash status plus unchanged key table row counts.

## B1 Checklist

| Item | Audit check                        | Verdict | Evidence                                                                                              |
| ---- | ---------------------------------- | ------- | ----------------------------------------------------------------------------------------------------- |
| B1-1 | baseline inventory json/md         | PASS    | `execute-evidence/phase1_baseline_inventory.json`; `execute-evidence/phase1_baseline_inventory.md`    |
| B1-2 | capability snapshot                | PASS    | `execute-evidence/phase1_capability_snapshot.json`                                                    |
| B1-3 | production DB zero mutation        | PASS    | `execute-evidence/phase1_no_mutation_proof.md`; supporting GREEN log `execute-evidence/8.3-green.txt` |
| B1-4 | data-root inventory, if applicable | PASS    | `execute-evidence/phase1_baseline_inventory.json`; `execute-evidence/phase1_baseline_inventory.md`    |

## Evidence Notes

- `phase1_baseline_inventory.json` records `capture_strategy=production_read_only`, target DB `data/duckdb/quant_monitor.duckdb`, `db.read_only_open=true`, `inspect.status=PASS`, `schema.table_count=21`, and no inspect errors or warnings.
- Key table baseline includes `schema_version=11`, `source_registry=5`, and zero rows in mutation-relevant operational tables including `file_registry`, `fetch_log`, `data_sync_job`, `validation_report`, `source_conflict`, `write_audit_log`, and `resource_guard_log`.
- Data-root inventory is present and not scan-limited: `raw_files_count=2`, `parquet_files_count=1`, `audit_files_count=1`, `report_files_count=0`, `scan_limited=false`.
- `phase1_capability_snapshot.json` covers exactly the three approved pilot request shapes: `baostock/cn_equity_daily_bar/fetch_daily_bar`, `akshare/cn_equity_daily_bar/fetch_daily_bar_validation`, and `akshare/macro_supplementary/fetch_macro_series`. All three show `source_in_registry=true`, `source_enabled=true`, `capability_declared=true`, and `domain_allowed_for_source=true`.
- `phase1_no_mutation_proof.md` records `DB hash unchanged=True`, `Phase 1 zero mutation=True`, and before/after row counts unchanged for all listed key tables.
- `8.3-green.txt` records the Phase 1 test passing and slice regression passing: `test_livePilot_phase1Baseline_readOnly` passed, 23 slice tests passed, and evidence capture reported `capture_strategy=production_read_only inspect_status=PASS phase1_zero_mutation=True`.

## Findings

| Severity | Finding                                                                                                                  | Impact                                                                                                                                                                  | Disposition                                                                                                                                                                                                    |
| -------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LOW      | `phase1_no_mutation_proof.md` records `DB hash unchanged=True` but does not print the concrete before/after hash values. | The artifact proves the intended boolean state and unchanged row counts, but later auditors cannot independently compare the exact hash pair from this file alone.      | Non-blocking for PH-B1 because §3.1 requires the no-mutation proof artifact and it is present with positive zero-mutation assertions. A5/prod-path hash audit should prefer concrete before/after hash values. |
| INFO     | Live GitNexus MCP/CLI queries were unavailable in this Codex session per `research/gitnexus-audit-summary.md`.           | B1 is an artifact and baseline consistency audit, not a symbol impact audit, so the PH-B1 verdict does not depend on live `query()`, `impact()`, or `detect_changes()`. | Record as availability limitation; do not treat GitNexus as green beyond the frozen local index metadata.                                                                                                      |

## GitNexus Availability Limitation

`research/gitnexus-audit-summary.md` states that no GitNexus MCP resources were exposed in this Codex session, and `node .gitnexus/run.cjs status` failed under the network sandbox via npm registry `EACCES`. Therefore live `query()`, `impact()`, and `detect_changes()` calls were unavailable. This PH-B1 audit used the frozen index facts from the summary plus the required Phase 1 evidence artifacts. Any conclusion requiring live graph traversal is outside this PH-B1 verdict.
