# R-1 Authorization Envelope Repair Evidence

Status: CLOSED

Root cause: authorization matched only `(source_id, data_domain, operation)`.

Repair:

- `backend/app/ops/live_pilot.py` now checks the full approved envelope: source, domain, operation, symbols/indicators, date window, and max rows.
- `tests/test_batch275_live_pilot_gate.py` covers wrong symbol, widened window, expanded row cap, and unapproved optional source.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-live-pilot-postgate tests/test_batch275_live_pilot_gate.py -q`
- Result: `26 passed, 1 skipped`
- Tier A final: `43 passed, 1 skipped`
