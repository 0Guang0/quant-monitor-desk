# System Architecture

Quant Monitor Desk is organized around a local data platform with web and UI shells around it. The runtime design in `docs/architecture/03_runtime_flows.md` describes scheduler/CLI/user requests flowing through `ResourceGuard`, `DataSyncOrchestrator`, adapters, raw/staging stores, validation, conflict checks, `WriteManager`, clean/snapshot tables, and read surfaces. Current code implements much of the data-platform side and keeps the API/frontend surface intentionally small.

## Main entrypoints

- FastAPI app: `backend/app/main.py`. It creates a `FastAPI` app and exposes `/health`, returning `status` plus the current resource profile from `backend/app/config.py`.
- Packaged CLI: `backend/app/cli/main.py`, exposed as `qmd-data` in `pyproject.toml`. It builds `qmd data` subcommands for route preview, sync, backfill, full-load, live-fetch, init-basic, health, scheduler, incremental, revision-audit, reconcile, and more.
- Ops CLI: `scripts/qmd_ops.py`, exposed as `qmd-ops`, wraps ops tasks such as DB inspection and delegates data commands.
- DB init/registry scripts: `scripts/init_db.py` and `scripts/sync_registry.py` are console scripts `qmd-init-db` and `qmd-sync-registry`.
- Frontend: `frontend/src/main.tsx` renders `frontend/src/App.tsx`, which is a placeholder dashboard shell.

## Backend package map

- `backend/app/config.py`: project/config roots and resource profile environment handling. It loads `.env` if present, so do not document secret values from local env files.
- `backend/app/core/`: resource guard, API limits, snapshot lineage.
- `backend/app/datasources/`: source registry, capability registry, route planning, live tier routing, product live gates, adapters, fetch ports, normalizers, provider catalog.
- `backend/app/sync/`: orchestration, job state machine, validation/write pipelines, runners, scheduler, watermark, indicator binding.
- `backend/app/db/`: DuckDB connection management, migrations, validation gate, write manager, SQL identifier safety, row counts, failed-write sidecar.
- `backend/app/storage/`: raw store, file registry, evidence/staged file ports, path compatibility.
- `backend/app/validation/` and `backend/app/validators/`: data quality and source conflict validation.
- `backend/app/layer1_axes/` through `layer5_evidence/`: five-layer domain modules.
- `backend/app/ops/`: data health, live acceptance, incremental runs, sandbox clean-write controls, manual probes, and operational reports.

## Runtime path: route, fetch, validate, write

The production fetch facade is `DataSourceService` in `backend/app/datasources/service.py`. Its constructor loads `SourceRegistry` and `SourceCapabilityRegistry`, creates a `SourceRoutePlanner`, and stores optional test/fixture fetch ports. `fetch()` plans a route, emits route-plan events, checks `ResourceGuard`, blocks unavailable routes, asserts capabilities for overrides, invokes the selected adapter/fetch port, and writes fetch log/file registry evidence.

`SourceRoutePlanner` in `backend/app/datasources/route_planner.py` orders candidates as `Primary`, `Validation`, and optionally `FallbackPolicy`. It rejects sources that are disabled, missing capability, blocked by platform matrix, missing user authorization, license-gated, validation-only primary, or otherwise unavailable. It returns auditable statuses such as `READY`, `DISABLED_SOURCE`, `VALIDATION_ONLY_BLOCKED`, `CAPABILITY_MISSING`, and `USER_AUTH_REQUIRED`.

`DataSyncOrchestrator` in `backend/app/sync/orchestrator.py` owns job runners for `incremental`, `backfill`, `reconcile`, `full_load`, `data_quality`, and `revision_audit`. It checks resource state before moving a job into `FETCHING`, delegates validation/write pipelines, and guards production paths so adapters cannot bypass `DataSourceService`.

`WriteManager` in `backend/app/db/write_manager.py` is the standard clean-write boundary. It requires an explicit validation gate, validates target/staging identifiers and primary keys, supports write modes from `specs/contracts/write_contract.yaml`, writes audit rows, and records failures with redacted error messages.

## Current API and frontend status

The source-backed API is currently only the health shell. Existing docs under `docs/api/` describe intended FastAPI routes and agent tool contracts, but do not assume those routes exist unless confirmed in `backend/app/api/` or mounted from `backend/app/main.py`.

The frontend is a scaffold. `frontend/src/App.tsx` displays the project name and five layer names. README decision D-08 says production UI should not be hard-coded before user confirmation of information architecture and interaction.

## Source references

- `backend/app/main.py`
- `backend/app/cli/main.py`
- `backend/app/cli/data_commands.py`
- `backend/app/datasources/service.py`
- `backend/app/datasources/route_planner.py`
- `backend/app/sync/orchestrator.py`
- `backend/app/db/write_manager.py`
- `frontend/src/App.tsx`
- `docs/architecture/03_runtime_flows.md`
