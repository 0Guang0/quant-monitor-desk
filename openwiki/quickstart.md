# OpenWiki Quickstart

Quant Monitor Desk is a local-first quantitative monitoring console. The product workflow in `README.md` is:

```text
Trusted data -> Multi-layer modeling -> Evidence monitoring -> Agent summary -> Human review
```

The README is explicit that the first version is not an automatic trading system. The implemented system is currently strongest in the backend data platform: source registries, route planning, ingestion/sync jobs, DuckDB schema/migrations, validation gates, write auditing, resource limits, and Layer 1-5 modeling modules. The FastAPI and frontend surfaces are still small shells: `backend/app/main.py` exposes `/health`, and `frontend/src/App.tsx` is a placeholder dashboard that says production UI needs user confirmation.

## Start here by task

- Architecture and code map: [architecture/system-architecture.md](architecture/system-architecture.md)
- Product/domain model and five layers: [domain/data-and-modeling.md](domain/data-and-modeling.md)
- DuckDB, schema, migrations, validation, writes: [data/data-platform.md](data/data-platform.md)
- Data sync, live fetch, route planning, gates: [workflows/data-sync-and-live-gates.md](workflows/data-sync-and-live-gates.md)
- Setup, tests, CI, operations: [operations/testing-and-operations.md](operations/testing-and-operations.md)
- Guidance for future coding agents: [agent-guide.md](agent-guide.md)

Existing documentation remains important. Use `docs/START_HERE.md` as the role router, `docs/INDEX.md` as the detailed documentation index, `MIGRATION_MAP.md` as the broad design/spec map, and `docs/modules/README.md` to distinguish authoritative module docs from compatibility links.

## Repository shape

- `backend/app/`: Python application code. Major areas include `cli/`, `datasources/`, `db/`, `sync/`, `ops/`, `storage/`, `validation/`, `validators/`, `agents/`, `notifications/`, and Layer 1-5 packages.
- `frontend/`: Vite React shell. Current UI is placeholder only.
- `specs/`: machine-readable contracts, schema, datasource registry specs, model-input specs, and layer specs.
- `docs/`: architecture, module, operation, quality, decision, API, schema, and registry documentation.
- `rules/`: current global execution, testing, and resource-limit rules moved out of the retired implementation-task tree.
- `configs/`: local runtime YAML such as datasource, alert, resource limits, QMT, market registry, and Layer 1 axis config.
- `scripts/`: packaged and CI/ops entry scripts such as DB init, registry sync, production gate, smoke scripts, and `qmd_ops`.
- `tests/`: broad pytest suite covering adapters, sync, schema, live gates, layers, data health, CLI, resource guard, and production contracts.
- `data/`: local runtime state for DuckDB, raw files, parquet, cache, logs, reports, and audit artifacts. Treat it as runtime data, not source.

## First local setup

The README documents `uv` as the preferred Python path:

```bash
uv sync --locked
uv run python scripts/init_db.py
uv run pytest -q
uv run ruff check .
uv run python -m compileall -q backend scripts tests
```

Frontend checks live under `frontend/`:

```bash
cd frontend
npm ci
npm run typecheck
npm run test
npm run build
```

GitHub CI currently uses `pip install -e ".[dev]"` before pytest/ruff/compileall and runs frontend `npm ci`, `npm audit --audit-level=high`, typecheck, tests, and build in `.github/workflows/ci.yml`. Treat the README/docs `uv` path as the project-preferred local path and the CI workflow as the current hosted implementation.

## Current implementation status

- FastAPI: health shell in `backend/app/main.py`. Design docs under `docs/api/` describe intended routes, but do not assume those routes are mounted until source confirms it.
- Frontend: placeholder shell in `frontend/src/App.tsx`. README decision D-08 says final information architecture and interactions need user confirmation before production implementation.
- CLI: `qmd-data`, `qmd-ops`, `qmd-init-db`, and `qmd-sync-registry` are declared in `pyproject.toml`.
- Data platform: substantial. Start with `backend/app/datasources/service.py`, `backend/app/datasources/route_planner.py`, `backend/app/sync/orchestrator.py`, `backend/app/db/write_manager.py`, `backend/app/db/validation_gate.py`, and migrations under `backend/app/db/migrations/`.
- Live data: fail-closed by default. Product live fetch requires `QMD_ALLOW_LIVE_FETCH` opt-in, ResourceGuard approval, required authorization/credentials, and isolated acceptance roots where applicable.
- Agent behavior: read-only by design. Docs and contracts forbid direct clean-table writes, arbitrary SQL, free web fetches, factual override by model text, and action semantics.

## Source authority rules

Prefer current source and machine-readable contracts under `specs/` when older planning material conflicts. The README says `docs/` and `specs/` are design/contract areas, not runtime code locations, and warns that old Round/Wave/DCP task cards are read-only evidence. Recent git history moved active global rules to `rules/`; use that directory for current execution/testing/resource rules.

Do not read or document secret values. `.env` exists locally and should not be read. Use `.env.example`, `docs/ops/config_secret_policy.md`, and environment variable names in source when configuration guidance is needed.

## Recent repository direction

Recent git history inspected during this OpenWiki init includes retirement of older Trellis/Loop and implementation-task docs, initialization of the OpenWiki/agent pointers, and live-data acceptance cleanup. That matches the current code emphasis on compact authority docs, route planning, isolated live acceptance, fail-closed product live gates, and auditable incremental evidence.
