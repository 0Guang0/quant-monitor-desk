# Repair/Debt Lite Plan — debt/r3-ops-inspect-data-health-references

## Source of truth

- audit / registry ID: `R3-REF-OPS-DB-DATA-HEALTH`
- task card: `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md`
- prompt: `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_06_debt_r3_ops_inspect_data_health_references.md`
- base branch: `integration/round3` @ `74a305db`
- target branch: `debt/r3-ops-inspect-data-health-references`
- merge target: `integration/round3`
- owner agent: PROMPT_06 session (docs/contracts only)

## Boundary

- allowed files:
  - `docs/ops/db_inspect_cli.md`
  - `docs/ops/data_health_cli.md`
  - `docs/ops/ops_report_cli.md`
  - `specs/contracts/ops_db_inspect_contract.yaml`
  - `specs/contracts/data_quality_rules.yaml` (ops profile only)
  - `.trellis/tasks/debt-r3-ops-inspect-data-health-references/**`
- forbidden files:
  - `backend/app/**`
  - `frontend/**`
  - `scripts/qmd_ops.py` runtime changes
  - `tests/test_ops_db_inspector.py` runtime tests
  - `data/duckdb/**`
  - registry rows (`docs/AUDIT_DEFERRED_REGISTRY.md`, etc.)
- production/data boundary: no DB writes, no network fetch, no migration execution
- explicit non-goals: runtime implementation, external code copy, EasyXT schema assumptions, PTrade/JQ order APIs

## Source Context Index (external references)

| Project    | URL                                           | Read mode        |
| ---------- | --------------------------------------------- | ---------------- |
| EasyXT     | `https://github.com/quant-king299/EasyXT`     | summarized below |
| JQ2PTrade  | `https://github.com/quant-king299/JQ2PTrade`  | summarized below |
| ptqmt-site | `https://github.com/quant-king299/ptqmt-site` | summarized below |

No network fetch was performed in this slice. Borrowable ideas are taken from `R3D_ops_db_data_health_reference.md`, `GLOBAL_EXECUTION_RULES.md`, and existing QMD ops design docs.

## External reference → QMD landing map

| #   | Borrowable idea (source)                                                                          | QMD landing target                                                                             | Decision                                                                                 |
| --- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | Data integrity categories: missing trading days, field quality, price-relation, outliers (EasyXT) | `docs/ops/data_health_cli.md` §4; `specs/contracts/data_quality_rules.yaml` `ops_cli_profiles` | **ADOPT** — Phase C / Batch 6; contract-driven via existing `DataQualityValidator` rules |
| 2   | Operator troubleshooting / monitor-style PASS-WARN-FAIL status (EasyXT)                           | `docs/ops/data_health_cli.md` §6; reuse `ops_db_inspect_contract.yaml` `status_enum`           | **ADOPT** — shared ops status vocabulary                                                 |
| 3   | QMT/xqshare ecosystem operator wording without auto-enable (EasyXT)                               | `docs/ops/db_inspect_cli.md` §2–§3; forbidden flags in contract                                | **ALREADY LANDED** — reinforce cross-ref only                                            |
| 4   | Hardcoded `stock_daily` / single-table DuckDB assumptions (EasyXT)                                | `docs/ops/data_health_cli.md` §2 boundary; contract `key_tables` from QMD schema               | **REJECT** — QMD uses `security_bar_1d` + registry tables                                |
| 5   | Trading APIs, auto-login, GUI, silent fallback (EasyXT)                                           | `GLOBAL_EXECUTION_RULES.md` Round2.6 red lines                                                 | **REJECT**                                                                               |
| 6   | `--duckdb-path` / explicit local DB override (JQ2PTrade)                                          | `specs/contracts/ops_db_inspect_contract.yaml` `--db`; `data_health_cli.md` `--db`             | **ALREADY LANDED** for db-inspect; extend to data-health design                          |
| 7   | Local CLI ergonomics, repeatable validation runs (JQ2PTrade)                                      | `docs/ops/data_health_cli.md` §5 CLI contract                                                  | **ADOPT**                                                                                |
| 8   | mapping-first / `api_mapping.json` pattern (JQ2PTrade)                                            | `docs/modules/source_capability_registry.md` (existing); not duplicated in ops CLI             | **DEFER** — source registry domain, not ops health CLI                                   |
| 9   | MiniPTrade lifecycle + context + report builder (JQ2PTrade)                                       | `docs/modules/backtest_review_lifecycle.md` (existing)                                         | **REJECT** for ops/data-health — backtest-only                                           |
| 10  | PTrade/JoinQuant strategy conversion, order APIs (JQ2PTrade)                                      | —                                                                                              | **REJECT**                                                                               |
| 11  | Local-only / browser-side privacy disclosure (ptqmt-site)                                         | `docs/ops/ops_report_cli.md` §2; cross-ref `privacy_data_flow.md`                              | **ADOPT**                                                                                |
| 12  | Offline/static operator report organization (ptqmt-site)                                          | `docs/ops/ops_report_cli.md` §4–§5                                                             | **ADOPT** — Phase E after JSON evidence stabilizes                                       |
| 13  | Online site shape as runtime dependency (ptqmt-site)                                              | —                                                                                              | **REJECT**                                                                               |

## Vertical slices

| Slice | Source ID                   | AC                                                             | Allowed files                                                                                  | Verification         | Evidence     |
| ----- | --------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------------------- | ------------ |
| S1    | `R3-REF-OPS-DB-DATA-HEALTH` | DEBT.plan with Source Context Index + reference map            | `.trellis/tasks/debt-r3-ops-inspect-data-health-references/DEBT.plan.md`                       | manual review        | this file    |
| S2    | `R3-REF-OPS-DB-DATA-HEALTH` | `data_health_cli.md` design frozen as Batch 6 input            | `docs/ops/data_health_cli.md`                                                                  | `check_doc_links.py` | merge report |
| S3    | `R3-REF-OPS-DB-DATA-HEALTH` | `ops_report_cli.md` design frozen as Round 5 input             | `docs/ops/ops_report_cli.md`                                                                   | `check_doc_links.py` | merge report |
| S4    | `R3-REF-OPS-DB-DATA-HEALTH` | Contract cross-refs + ops profile in `data_quality_rules.yaml` | `specs/contracts/ops_db_inspect_contract.yaml`, `data_quality_rules.yaml`, `db_inspect_cli.md` | registry tests       | merge report |

## Merge gate

- targeted tests:
  - `pytest tests/test_trellis_audit_trace_authority.py -q`
  - `pytest tests/test_round3_audit_registry_alignment.py -q`
  - `pytest tests/test_unresolved_item_task_coverage.py -q`
  - `python scripts/check_doc_links.py`
- full tests: not required (docs/contracts only slice)
- lint/format/compile: not touched
- registry reconciliation: registry files untouched; `R3-REF-OPS-DB-DATA-HEALTH` docs landing only
- remaining deferred: runtime `backend/app/ops/data_health.py` → Batch 6 sub-batch per `R3D_ops_db_data_health_reference.md`
