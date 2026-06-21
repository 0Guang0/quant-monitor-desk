# R-3 Phase 4 Fail-Closed Repair Evidence

Status: CLOSED

Root cause: Phase 4 evidence did not fail closed on missing Request 2 verdict/reconciliation artifacts and did not declare the real validation/conflict/write gate paths.

Repair:

- `capture_phase4_validation()` now requires `eastmoney_stock_zh_a_hist_verdict.md` and `phase3_request2_evidence_reconciliation.md`.
- Phase 4 payload/proof now records `can_write_clean=false`, clean-write block reasons, declared `DataQualityValidator`, `SourceConflictValidator`, and `DbValidationGate` paths.
- Severe findings block clean write in evidence.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-live-pilot-postgate tests/test_batch275_live_pilot_gate.py -q`
- Result: `26 passed, 1 skipped`
- Prior focused validator check from handoff: `tests/test_source_conflict_validator.py tests/test_data_quality_validator.py` = `34 passed`
- Full final pytest: `656 passed, 2 skipped`
