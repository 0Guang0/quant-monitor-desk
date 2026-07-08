# Testing And Operations

This repository has a broad test suite and several operational gates. Use this page to choose checks by change area, then verify exact commands against current source and CI before release work.

## Local setup and baseline checks

The README documents the preferred local backend path:

```bash
uv sync --locked
uv run python scripts/init_db.py
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q backend scripts tests
```

Frontend checks:

```bash
cd frontend
npm ci
npm run typecheck
npm run test
npm run build
```

`docs/ops/verification_commands.md` includes a fuller Windows-oriented gate list with coverage, ruff format, production gate, DB init, registry sync, and ingestion smoke. Confirm older docs before copying commands into automation, especially after the recent move from retired implementation-task docs to `rules/`.

## Test organization

Tests live in `tests/` and are configured by both `pytest.ini` and `[tool.pytest.ini_options]` in `pyproject.toml`. Both set `testpaths = tests` and `pythonpath = .`; they differ on default addopts because `pyproject.toml` includes `.audit-sandbox` basetemp/cache settings while `pytest.ini` only has `-q`. Be aware of config precedence when debugging invocation differences.

Major test categories visible from filenames and sampled files:

- Data-source adapters and fetch ports: market, macro, crypto, official macro, SEC EDGAR, CN market, prediction market.
- Incremental and watermark flows: FRED, Alpha Vantage, BaoStock, CNINFO, Deribit, Treasury, World Bank, SEC EDGAR, CFTC, BIS, MootDX.
- Sync/orchestration: scheduler, jobs, runners, pipeline contract, orchestrator, watermarks, full-load, bounded backfill.
- DB and writes: schema contract, migrations, DuckDB connection, validation gate, write manager, raw store.
- Layers: Layer 1 axes/feature/interpretation/clean reads, Layer 2 sensors, Layer 3 loader/snapshots, Layer 4 market structure, Layer 5 evidence/provenance.
- Ops/security: resource guard, API security contract, production gate, path jail, config templates, model input whitelist, module boundaries.
- Frontend: `frontend/src/*.test.tsx` run with Vitest.

Network tests are marked `network` and skipped unless `--run-network` is passed. `tests/conftest.py` also checks live-fetch opt-in for selected live tests.

## CI and nightly

Current GitHub CI in `.github/workflows/ci.yml` has separate backend and frontend jobs.

Backend CI:

```bash
pip install -e ".[dev]"
pytest -q -n auto --cov=backend --cov-fail-under=85
ruff check .
ruff format --check .
python -m compileall backend scripts tests
python scripts/production_gate.py
python scripts/ci_ingestion_smoke.py
python scripts/ci_perf_budget_artifact.py
```

It also blocks `WriteManager` imports under `backend/app/datasources/`.

Frontend CI:

```bash
npm ci
npm audit --audit-level=high
npm run typecheck
npm run test
npm run build
```

Nightly CI in `.github/workflows/nightly.yml` sets `QMD_DATA_ROOT=.audit-sandbox/nightly-network` and `QMD_ALLOW_LIVE_FETCH=1`, then runs a limited network-marked FRED macro incremental mock smoke.

## Operational scripts

- `scripts/init_db.py`: initialize/apply DuckDB migrations.
- `scripts/sync_registry.py`: sync source registry into DB.
- `scripts/qmd_ops.py`: `qmd-ops` CLI wrapper for ops commands and data CLI delegation.
- `scripts/production_gate.py`: hardening checks, including no production stub validation, least-privilege CI permissions, dependabot presence, agent forbidden tools, resource contract defaults, and module boundaries.
- `scripts/ci_ingestion_smoke.py`: CI ingestion smoke under isolated data root.
- `scripts/ci_perf_budget_artifact.py`: bounded perf budget artifact.
- `scripts/check_module_boundaries.py`: module import/boundary checks.

## Change-to-test guidance

- Datasource routing or adapters: run targeted adapter/fetch-port tests, route planner/source registry tests, relevant incremental tests, and `scripts/production_gate.py`.
- Sync orchestration: run `tests/test_sync_orchestrator.py`, sync job/runner/pipeline tests, bounded backfill/full-load tests, and resource guard tests if job transitions change.
- DB schema or migrations: run schema, migration, DB validation gate, write manager, and production gate tests. Use a fresh isolated `QMD_DATA_ROOT` for smoke paths.
- Layer modules: run the corresponding layer tests and any source binding/clean read tests for that layer.
- API security or resource limits: run API security contract, resource guard, and production gate tests.
- Frontend: run `npm run typecheck`, `npm run test`, and `npm run build` in `frontend/`.
- Live or network behavior: do not run live tests without explicit opt-in, credentials, isolated data root, and `QMD_ALLOW_LIVE_FETCH=1`.

## Known documentation drift to watch

Existing docs prefer `uv` as the main dependency path, but GitHub CI currently uses pip editable install. Existing verification docs also mention some paths that were not present during this run, including a doc-link script and older Batch 2.75 live-pilot test names. Treat this page as a current-code map and verify older docs before acting on them.

## Source references

- `README.md`
- `docs/ops/verification_commands.md`
- `.github/workflows/ci.yml`
- `.github/workflows/nightly.yml`
- `pytest.ini`
- `pyproject.toml`
- `scripts/production_gate.py`
- `tests/conftest.py`
