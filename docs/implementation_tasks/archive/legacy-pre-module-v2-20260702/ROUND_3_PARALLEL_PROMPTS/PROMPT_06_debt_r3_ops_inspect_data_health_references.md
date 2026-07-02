# PROMPT_06 — debt/r3-ops-inspect-data-health-references

Use this prompt in a fresh session for landing EasyXT/JQ2PTrade/ptqmt-site references into QMD ops DB inspect and data-health design. This is optional parallel docs/contract work; runtime implementation waits for a later approved sub-batch.

## Mission

Convert external reference ideas into QMD-owned ops/data-health contracts and documentation without copying external runtime code.

## Branch / worktree

- Branch: `debt/r3-ops-inspect-data-health-references`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-r3-ops-data-health-ref`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
4. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
5. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
6. `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`
7. `docs/ops/db_inspect_cli.md`
8. `specs/contracts/ops_db_inspect_contract.yaml`
9. `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`
10. `docs/ROUND3_HANDOFF.md`
11. `docs/modules/duckdb_and_parquet.md`
12. `docs/modules/local_file_system.md`
13. `docs/modules/data_validation_and_conflict.md`
14. `docs/modules/write_manager.md`
15. `specs/contracts/data_quality_rules.yaml`
16. `specs/contracts/source_conflict_rules.yaml`
17. `specs/contracts/resource_limits.yaml`
18. `specs/contracts/runtime_versions.md`

## External references to open and cite in the plan

- `https://github.com/quant-king299/EasyXT`
- `https://github.com/quant-king299/JQ2PTrade`
- `https://github.com/quant-king299/ptqmt-site`

## Allowed files

Docs/contract phase only unless the plan is explicitly upgraded:

- `docs/ops/db_inspect_cli.md`
- future `docs/ops/data_health_cli.md` if needed
- future `docs/ops/ops_report_cli.md` if needed
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/data_quality_rules.yaml` ops profile if needed
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md` only if an index is stale
- targeted docs/tests for read-only/local-only semantics

## Hard boundaries

- Do not copy external runtime code.
- Do not implement backend runtime in this branch unless the user approves a later implementation slice.
- Do not perform network fetch.
- Do not write project DB files.
- Do not assume EasyXT's DB schema is QMD's schema.
- Do not import PTrade/JoinQuant strategy or order APIs.

## Workflow

1. Create a Phase 8D lightweight plan.
2. Summarize borrowable ideas from the three reference projects.
3. Map each idea to QMD-owned docs/contracts, or mark it as rejected/deferred.
4. Make minimal docs/contract changes.
5. Run doc and registry tests.
6. Produce a merge report.

## Verification commands

- `pytest tests/test_trellis_audit_trace_authority.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `python scripts/check_doc_links.py`

## Done criteria

- External URLs are present in MASTER Source Context Index.
- Every borrowed idea has an explicit QMD-owned landing target or rejection reason.
- Docs/contracts remain read-only and local-first.
- No runtime behavior changed.
