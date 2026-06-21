# R-4 Idempotency / Failure Repair Evidence

Status: CLOSED

Root cause: Phase 3 partial fetch failure could escape before a structured per-request failure artifact was persisted.

Repair:

- `capture_phase3_raw_evidence()` now records per-request failed fetch payloads with production hash/count no-mutation proof.
- Phase 3 aggregate evidence marks rerun-safe overwrite semantics.
- Tests cover vendor failure artifact and repeated execution.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-live-pilot-postgate tests/test_batch275_live_pilot_gate.py -q`
- Result: `26 passed, 1 skipped`
- Full final pytest: `656 passed, 2 skipped`
