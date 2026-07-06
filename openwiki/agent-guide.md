# Agent Guide

Use this page before making code changes. It summarizes the source authority and guardrails a future coding agent needs after reading [quickstart.md](quickstart.md).

## Read order

1. `openwiki/quickstart.md` for the current map.
2. The relevant OpenWiki page for your change area.
3. `README.md` for project boundaries and user-approved decisions D-01 through D-12.
4. `docs/INDEX.md` and `docs/modules/README.md` for detailed authoritative module docs.
5. `MIGRATION_MAP.md` only when you need broad design/spec navigation.
6. Current source and tests for final truth.

## Authority and drift

The repository contains many implementation-task and roadmap documents. They are useful context, but do not treat old Round/Wave/DCP task cards as execution order. The README says active SSOTs include `PROJECT_IMPLEMENTATION_ROADMAP.md` section 3, `MODULE_COMPLETION_RATING.md`, and `docs/implementation_tasks/README.md`, while old task archives are read-only evidence.

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

## Where to start by change area

- CLI command behavior: `backend/app/cli/main.py`, `backend/app/cli/data_commands.py`, tests named `test_qmd_data_cli*` and sync CLI tests.
- Source routing/capability: `backend/app/datasources/route_planner.py`, `capability_registry.py`, `source_registry.py`, `service.py`, specs under `specs/contracts/` and `specs/datasource_registry/`.
- Live gates: `backend/app/datasources/product_live_gate.py`, `live_tier_router.py`, `backend/app/ops/tier_a_live_acceptance.py`, ADRs under `docs/decisions/`.
- Sync orchestration: `backend/app/sync/orchestrator.py`, `jobs.py`, `pipeline.py`, `runners.py`, `scheduler.py`.
- DB writes and schema: `backend/app/db/migrate.py`, `backend/app/db/migrations/`, `backend/app/db/write_manager.py`, `specs/schema/schema.sql`.
- Layer 1: `backend/app/layer1_axes/`, `specs/layer1_axes/`, `configs/layer1_axes.yml`.
- Layer 2: `backend/app/layer2_sensors/`, cross-asset fixtures and tests.
- Layer 3: `backend/app/layer3_chains/`, `specs/layer3_global_industry_chains/`.
- Layer 4: `backend/app/layer4_markets/`.
- Layer 5: `backend/app/layer5_evidence/`, evidence/provenance tests.
- Frontend: `frontend/src/App.tsx` and tests. Remember the UI is still a placeholder and D-08 requires user confirmation before production IA/interaction decisions.

## Verification discipline

Use targeted tests first, then broader gates. For risky backend changes, include `pytest -q` or the relevant subset, `ruff check .`, `python -m compileall -q backend scripts tests`, and `python scripts/production_gate.py`. For frontend changes, run typecheck, Vitest, and build in `frontend/`.

Network/live tests require explicit operator intent. Use isolated `QMD_DATA_ROOT` values under `.audit-sandbox` for acceptance/smoke paths, never the canonical local production DB.

## Existing agent instruction files

Top-level `AGENTS.md` and `CLAUDE.md` contain GitNexus and workflow guidance. This OpenWiki run adds an `## OpenWiki` section to both files so future agents start here.
