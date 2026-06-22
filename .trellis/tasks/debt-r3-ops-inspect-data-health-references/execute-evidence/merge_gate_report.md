# Merge Gate Report — debt/r3-ops-inspect-data-health-references

## Scope

Docs/contracts-only landing of EasyXT / JQ2PTrade / ptqmt-site reference ideas into QMD-owned ops and data-health design (`R3-REF-OPS-DB-DATA-HEALTH`).

## Changed files

| File | Intent |
| ---- | ------ |
| `.trellis/tasks/debt-r3-ops-inspect-data-health-references/DEBT.plan.md` | Phase 8D plan + Source Context Index + reference map |
| `docs/ops/data_health_cli.md` | New Phase C / Batch 6 data health CLI design |
| `docs/ops/ops_report_cli.md` | New Phase E ops report CLI design |
| `docs/ops/db_inspect_cli.md` | External URLs + cross-refs to new designs |
| `specs/contracts/ops_db_inspect_contract.yaml` | `reference_landing` block + future phase doc pointers |
| `specs/contracts/data_quality_rules.yaml` | `ops_cli_profiles` for contract-driven health checks |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | Updated `R3-REF-OPS-DB-DATA-HEALTH` alias row |

## Out of scope (untouched)

- `backend/app/**` — no runtime implementation
- Registry files — no row edits
- `data/duckdb/**` — no DB mutation
- Network fetch — not performed

## Verification results

| Command | Result |
| ------- | ------ |
| `pytest tests/test_trellis_audit_trace_authority.py -q` | PASS (7) |
| `pytest tests/test_round3_audit_registry_alignment.py -q` | PASS (6) |
| `pytest tests/test_unresolved_item_task_coverage.py -q` | PASS (3) |
| `python scripts/check_doc_links.py` | PASS (189 markdown files) |

## Registry reconciliation

Registry files untouched. Runtime implementation remains deferred to Batch 6 sub-batch per `R3D_ops_db_data_health_reference.md`.

## Remaining deferred

| ID | Owner | Phase | Closure |
| -- | ----- | ----- | ------- |
| `R3-EARLY-DB-INSPECT-CLI` | Batch 1 execute | Phase A runtime | `backend/app/ops/db_inspector.py` + tests |
| `R3-REF-OPS-DB-DATA-HEALTH` runtime | Batch 6 | Phase C | `backend/app/ops/data_health.py` per `data_health_cli.md` |
| Ops report runtime | Round 5 | Phase E | `backend/app/ops/report_models.py` per `ops_report_cli.md` |
