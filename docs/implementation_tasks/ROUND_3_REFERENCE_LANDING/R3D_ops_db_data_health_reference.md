# R3D_ops_db_data_health_reference — Ops DB/Data Health Reference Landing Task

## 1. Round / batch / branch

| Field                | Value                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------- |
| Round                | Round 3                                                                                                    |
| Batch                | Batch 1 reference carry-forward and Batch 6 implementation sub-batch                                       |
| Suggested branch     | `debt/r3-ops-inspect-data-health-references` for docs/contract plan; Batch 6 sub-branch for implementation |
| Can run in parallel? | Yes, if docs/ops/contracts only. Runtime implementation must wait for owner/allowed-file plan.             |
| Blocking?            | Does not block staged-only `019`. It supports DB/data evidence and later Batch 6 closeout.                 |

## 2. Purpose

Land external reference ideas from EasyXT, JQ2PTrade, and ptqmt-site into QMD's own local-first, read-only, contract-driven ops inspection and data health tooling.

This task does not copy external runtime code. It defines what QMD should build or defer.

## 3. External project links execute must see

| Project    | URL                                           | Borrowable detail                                                                                                                                                   | Required boundary                                                                                                     |
| ---------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| EasyXT     | `https://github.com/quant-king299/EasyXT`     | Data integrity categories: missing trading days, quality checks, price-relation checks, outlier checks; operator troubleshooting and QMT/xqshare ecosystem wording. | Do not copy trading APIs, auto-login, GUI, hardcoded DB path, direct DuckDB query assumptions, or automatic fallback. |
| JQ2PTrade  | `https://github.com/quant-king299/JQ2PTrade`  | `--duckdb-path` style local DB path override, local CLI ergonomics, API mapping pattern, MiniPTrade local DuckDB loading pattern.                                   | Do not copy PTrade/JoinQuant conversion, strategy execution, or order APIs into ops/data health.                      |
| ptqmt-site | `https://github.com/quant-king299/ptqmt-site` | Local-only / browser-side privacy wording and operator documentation organization.                                                                                  | Not a runtime dependency; docs/report style only.                                                                     |

## 4. Plan-stage input index

Plan must read and summarize:

- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `MIGRATION_MAP.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `docs/ops/db_inspect_cli.md`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/local_file_system.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/runtime_versions.md`

Plan must cite the three external URLs above in MASTER Source Context Index.

## 5. Candidate outputs

Docs/contract phase may produce or update:

- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `docs/ops/ops_report_cli.md`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/data_quality_rules.yaml` ops profile
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md` cross-reference

Implementation phase may later produce:

- `backend/app/ops/db_inspector.py`
- `backend/app/ops/data_health.py`
- `backend/app/ops/report_models.py`
- `scripts/qmd_ops.py` or approved console-script entry
- `tests/test_ops_db_inspector.py`
- `tests/test_ops_data_health.py`

## 6. Required boundaries

- Read-only DB by default.
- No production DB mutation.
- No network fetch.
- No migration execution.
- No secret/token printing.
- No full-market/full-history scan by default.
- No direct reuse of EasyXT hardcoded `stock_daily` table assumption.
- All reports must carry data path, source, run id, row counts, and error code/docs anchor.

## 7. Acceptance criteria

- DB inspect design remains read-only and local-first.
- Data health checks are contract-driven, not hardcoded to a single external project's schema.
- CLI supports explicit DB path or config-derived path.
- Missing/empty DB, schema inventory, row counts, raw/parquet evidence, fetch_log/source_used evidence are representable.
- Any runtime implementation has tests proving no production write and no network fetch.
