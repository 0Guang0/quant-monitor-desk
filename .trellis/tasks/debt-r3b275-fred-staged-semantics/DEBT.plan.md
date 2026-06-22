# Repair/Debt Lite Plan — r3b275-fred-staged-semantics

## Source of truth

- audit / registry ID: `B2.5-O-05`
- base branch: `integration/round3` @ `7729419d`
- target branch: `integration/round3`

## Decision

`B2.5-O-05` **RE-DEFERRED** — Batch 2.75 Request 3 does not close FRED primary; owner Batch 6.

## Verification

- `pytest tests/test_batch25_production_data_gate.py tests/test_production_live_pilot_policy.py tests/test_round3_audit_registry_alignment.py tests/test_unresolved_item_task_coverage.py tests/test_fred_staged_semantics.py -q`
- `python scripts/check_doc_links.py`
