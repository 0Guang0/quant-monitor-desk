# R-2 Route / Fixture Fallback Repair Evidence

Status: CLOSED

Root cause: Batch-local tests did not prove every non-READY route stopped before live fetch construction, and fixture/staged ports were not covered.

Repair:

- Added non-READY route tests for `DISABLED_SOURCE`, `CAPABILITY_MISSING`, `USER_AUTH_REQUIRED`, and `RESOURCE_GUARD_PAUSED`.
- Added ResourceGuard hard-stop test before fetch construction.
- Added fixture/staged-service rejection tests for `StubFetchPort`, `LocalFixtureFetchPort`, and `build_staged_fixture_service`.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.audit-sandbox\pytest-live-pilot-postgate tests/test_batch275_live_pilot_gate.py -q`
- Result: `26 passed, 1 skipped`
