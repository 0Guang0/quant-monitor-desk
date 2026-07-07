# Agent Guide

Use this page before making code changes. It summarizes the source authority and guardrails a future coding agent needs after reading [quickstart.md](quickstart.md).

## Read order

1. `openwiki/quickstart.md` for the current map.
2. The relevant OpenWiki page for your change area.
3. `README.md` for project boundaries and user-approved decisions D-01 through D-12.
4. `rules/` for current execution, testing, and resource-limit rules.
5. `docs/INDEX.md` and `docs/modules/README.md` for detailed authoritative module docs.
6. `MIGRATION_MAP.md` only when you need broad design/spec navigation.
7. Current source and tests for final truth.

## Authority and drift

The repository contains roadmap, migration-map, audit, and historical task documents. They are useful context, but do not treat old Round/Wave/DCP task cards as execution order. Recent git history retired the old implementation-task tree and moved global rules to `rules/`. Use `PROJECT_IMPLEMENTATION_ROADMAP.md`, `MODULE_COMPLETION_RATING.md`, `MIGRATION_MAP.md`, `docs/INDEX.md`, `docs/modules/README.md`, `rules/`, and current source/tests as the practical starting set.

When docs and source conflict, prefer current source plus machine-readable contracts under `specs/`. If changing behavior intentionally, update source, tests, and the relevant contract/docs together.

## Guardrails

- Do not read `.env` or document secrets. `.env.example` and docs may be used for placeholder setup guidance.
- Do not bypass `DataSourceService` for production fetch paths.
- Do not import or use `WriteManager` from `backend/app/datasources/`; CI blocks this.
- Do not write clean tables directly from datasources, adapters, agents, or arbitrary SQL paths.
- Do not restore old source roles `Shadow` or `Emergency`; use `Primary / Validation / FallbackPolicy`.
- Do not silently fall back to another source. Route plans, quality flags, audit logs, or conflicts must show source switching.
- Do not enable product live fetch without `QMD_ALLOW_LIVE_FETCH=1`, ResourceGuard OK, required credentials/authorization, and isolated acceptance data roots where applicable.
- Do not treat agent-generated text as factual source data. Layer 5 evidence code explicitly rejects that pattern.
- Treat `docs/api/` route descriptions as design/contract references until `backend/app/main.py` mounts matching routers.

## Where to start by change area

- CLI command behavior: `backend/app/cli/main.py`, `backend/app/cli/data_commands.py`, tests named `test_qmd_data_cli*` and sync CLI tests.
- Source routing/capability: `backend/app/datasources/route_planner.py`, `capability_registry.py`, `source_registry.py`, `service.py`, specs under `specs/contracts/` and `specs/datasource_registry/`.
- Live gates: `backend/app/datasources/product_live_gate.py`, `live_tier_router.py`, **source-route matrix spine** (`scripts/qmd_ops.py accept-source-route-db`, `backend/app/ops/source_route_db_acceptance*.py`, ADR-016). Tier A/B/C harnesses (`tier_a_live_acceptance.py` etc.) remain for M-DATA-03 sandbox paths; matrix closure is the release SSOT.
- Sync orchestration: `backend/app/sync/orchestrator.py`, `jobs.py`, `pipeline.py`, `runners.py`, `scheduler.py`.
- DB writes and schema: `backend/app/db/migrate.py`, `backend/app/db/migrations/`, `backend/app/db/write_manager.py`, `backend/app/db/validation_gate.py`, `specs/schema/schema.sql`.
- Layer 1: `backend/app/layer1_axes/`, `specs/layer1_axes/`, `configs/layer1_axes.yml`.
- Layer 2: `backend/app/layer2_sensors/`, cross-asset fixtures and tests.
- Layer 3: `backend/app/layer3_chains/`, `specs/layer3_global_industry_chains/`.
- Layer 4: `backend/app/layer4_markets/`.
- Layer 5: `backend/app/layer5_evidence/`, evidence/provenance tests.
- Frontend: `frontend/src/App.tsx` and tests. Remember the UI is still a placeholder and D-08 requires user confirmation before production IA/interaction decisions.

## Verification discipline

Use targeted tests first, then broader gates. For risky backend changes, include `pytest -q` or the relevant subset, `ruff check .`, `python -m compileall -q backend scripts tests`, and `python scripts/production_gate.py`. For frontend changes, run typecheck, Vitest, and build in `frontend/`.

Network/live tests require explicit operator intent. Use isolated `QMD_DATA_ROOT` values under `.audit-sandbox` for acceptance/smoke paths, never the canonical local production DB.

New or changed tests should follow `rules/GLOBAL_TESTING_POLICY.md`: assert business behavior, keep external I/O mocked or fixture-based by default, include meaningful assertions, and add the required Chinese five-field test docstring format for `test_*` functions.

## Existing agent instruction files

Top-level `AGENTS.md` and `CLAUDE.md` already contain the required `## OpenWiki` section pointing future agents to `openwiki/quickstart.md`.
