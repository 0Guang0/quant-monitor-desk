# R-5 Perf / Hygiene Registry And Smoke Evidence

Status: CLOSED for repair; authoritative perf refresh remains DEFERRED to CI nightly / Batch6 ops.

Repair:

- `R3-B25-PERF-BUDGET-01` and `R3-B25-HYG-03` are present in:
  - `docs/AUDIT_DEFERRED_REGISTRY.md`
  - `docs/UNRESOLVED_ISSUES_REGISTRY.md`
  - `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`
- Registry text states smoke/perf evidence is not live-source authorization.

Smoke verification:

- Exact wrapper `uv run ...` could not run because `uv` is not on PATH in this shell.
- Direct venv command without temp override initially failed inside pytest due Windows temp permission: `PermissionError: C:\Users\Guang\AppData\Local\Temp\pytest-of-Guang`.
- Passing bounded command:

```powershell
$env:TEMP='.audit-sandbox\r3b275-audit\tmp'
$env:TMP='.audit-sandbox\r3b275-audit\tmp'
$env:PYTEST_ADDOPTS='-p no:cacheprovider --basetemp=.audit-sandbox\r3b275-audit\pytest-tmp'
.\.venv\Scripts\python.exe scripts\production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox\r3b275-audit
```

Result:

- `PASS: init_db`
- `PASS: sync_registry`
- `PASS: pytest_resource_guard`
- `PASS: pytest_service_path`
- `PASS: pytest_vendor_service_e2e`
- `production_equivalent_smoke: ALL PASS`
- Metrics include `elapsed_s=7.86`, `guard_status=observable`, `pytest_steps=5`.

Deferred closure command:

- Owner: CI nightly / Batch6 ops
- Phase: performance-budget artifact refresh
- Closure test: `uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit` plus persisted threshold/budget artifact.
- Boundary: smoke/perf evidence does not authorize live sources or production-live readiness.
