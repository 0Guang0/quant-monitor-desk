# Round2 ABCD Re-Audit Closeout (2026-06-19)

Follow-up to adversarial re-audit on branch `fix/round2-abcd-audit-remediation`.

## Closed in this pass

| ID | Fix |
|----|-----|
| P1-02 | `rule_contract.py` wired into runners; stronger lineage test asserts non-empty fetch_ids |
| P1-04 / A9-01 | `specs/schema/schema.sql` CHECK constraints aligned with migration 009; contract test added |
| P1-05 | Ruff gate green (`python -m ruff check backend scripts tests`) |
| P2-02 / NEW-02 | Reconcile fail-closed on re-fetch failure (removed synthetic compare rows) |
| P2-03 / A4-03 | `retry_count` in fetch/reconcile payloads; `parse_event_payload` surfaces `_parse_error` |
| P2-04 | `ITEM_SUCCESS` incremental event with instrument task_id |
| NEW-04 | `run_backfill` requires `clean_table` |
| A6-02 | `SyncJobStateMachine.connection_manager` public property |
| A7-02 | `tests/test_sync_pipeline_contract.py` |
| A9-02 | Migration `010_lineage_not_null.sql` — NOT NULL `rule_set_id` / `rule_version` on validation_report |
| P3-02 | `filterwarnings` in `pyproject.toml` for Starlette/httpx deprecation |
| P3-03 | Frontend shell tests pass (3 total) |
| P3-04 | Ponytail equivalence documented in `docs/decisions/README.md` |

## Deferred (documented, not blocking Round2 closure)

| ID | Reason |
|----|--------|
| P2-06 / A8-02 | Real vendor scale / latency benchmarks → Round3 early (`ROUND3_EARLY_CLOSE_PLAN.md`) |
| A1-02 | QMT/Yahoo live vendor E2E requires user authorization |
| A3-01 | Further `runners.py` decomposition → Round3 refactor window |
| A5-02 | Multi-failure combination soak tests → Round3 |
| P2-05 | Rename `allowed_domain` column → compatibility migration in Round3 |
| P3-07 | npm `devdir` env warning — host npm config, not app defect |

## Verification gate

```bash
python -m pytest -q
python -m pytest -q --cov=backend --cov-fail-under=85
python -m ruff check backend scripts tests
python -m ruff format --check backend scripts tests
python scripts/production_equivalent_smoke.py
cd frontend && npm run typecheck && npm test && npm run build
```
