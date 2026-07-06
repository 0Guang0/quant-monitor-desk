# OpenWiki Quickstart

Quant Monitor Desk is a local-first quantitative monitoring console. Its stated workflow is `Trusted data -> Multi-layer modeling -> Evidence monitoring -> Agent summary -> Human review`, and the README is explicit that day-one scope is not automatic trading. The stack is Python 3.11+, FastAPI, DuckDB, Pydantic, YAML/SQL contracts, and a Vite/React/TypeScript frontend shell. See `README.md`, `pyproject.toml`, and `frontend/package.json`.

Most implemented behavior today is in the backend data platform and CLI paths, not in the web UI. `backend/app/main.py` exposes a small `/health` FastAPI shell, and `frontend/src/App.tsx` is still a placeholder dashboard that says the UI must be confirmed before production. The dense runtime surface is the data-source registry/routing layer, sync orchestration, DuckDB validation/write path, operations scripts, and Layer 1-5 modeling modules.

## Start here by task

- Architecture and code map: [architecture/system-architecture.md](architecture/system-architecture.md)
- Product/domain model and five layers: [domain/data-and-modeling.md](domain/data-and-modeling.md)
- DuckDB, schema, migrations, validation, writes: [data/data-platform.md](data/data-platform.md)
- Data sync, live fetch, route planning, gates: [workflows/data-sync-and-live-gates.md](workflows/data-sync-and-live-gates.md)
- Setup, tests, CI, operations: [operations/testing-and-operations.md](operations/testing-and-operations.md)
- Guidance for future coding agents: [agent-guide.md](agent-guide.md)

Existing documentation is still important. Use `docs/START_HERE.md` as the role router, `docs/INDEX.md` as the detailed documentation index, `MIGRATION_MAP.md` as the broad design/spec map, and `docs/modules/README.md` to distinguish authoritative module docs from compatibility links.

## Repository shape

- `backend/app/`: Python application code. Major areas include `cli/`, `datasources/`, `db/`, `sync/`, `ops/`, `storage/`, `validation/`, and Layer 1-5 packages.
- `frontend/`: Vite React shell. Current UI is placeholder only.
- `specs/`: machine-readable contracts, schema, datasource registry specs, model-input specs, and layer specs.
- `docs/`: architecture, module, operation, quality, decision, and implementation-task documentation.
- `configs/`: local runtime YAML such as datasource, alert, resource limits, and Layer 1 axis config.
- `scripts/`: packaged and CI/ops entry scripts such as DB init, registry sync, production gate, smoke scripts, and `qmd_ops`.
- `tests/`: large pytest suite covering adapters, sync, schema, live gates, layers, data health, CLI, resource guard, and production contracts.
- `data/`: runtime data roots for DuckDB, raw files, parquet, cache, logs, reports. Treat as local runtime state.

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

GitHub CI currently installs Python with `pip install -e ".[dev]"` before pytest/ruff/compileall and runs frontend `npm ci`, `npm audit --audit-level=high`, typecheck, tests, and build in `.github/workflows/ci.yml`. Treat the README/docs `uv` path as the project-preferred local path and the CI workflow as the current hosted implementation.

## Current implementation status

- FastAPI: shell health app in `backend/app/main.py`; narrative API docs exist under `docs/api/`, but current route surface is small.
- Frontend: placeholder shell in `frontend/src/App.tsx`; README decision D-08 says final UI needs user confirmation before production implementation.
- Data platform: substantial. `backend/app/datasources/service.py`, `route_planner.py`, `sync/orchestrator.py`, `db/write_manager.py`, and migrations under `backend/app/db/migrations/` are the main runtime paths.
- Live data: fail-closed by default. `QMD_ALLOW_LIVE_FETCH` and resource checks gate product live fetches; Tier A/B/C routing is implemented in `backend/app/datasources/live_tier_router.py`.
- Agent behavior: read-only by design. The docs and contracts forbid direct clean-table writes, arbitrary SQL, free web fetches, and action semantics.

## Source authority rules

Prefer current source and contracts over older planning material when they disagree. The root README says `docs/` and `specs/` are authoritative design/contract areas and warns that older Round/Wave/DCP task cards are read-only evidence, not execution order. `docs/modules/README.md` also marks some merged module docs as compatibility-only.

Do not read or document secret values. `.env` exists but should not be read. Use `.env.example`, `docs/ops/config_secret_policy.md`, and environment variable names in source when configuration guidance is needed.

## Recent repository direction

Recent git history inspected during this OpenWiki init includes cleanup of Trellis/Loop workflow docs and M-DATA-03/Tier A-B-C live acceptance work. That matches the current source emphasis on isolated live acceptance, route planning, product live gates, and incremental evidence artifacts.
