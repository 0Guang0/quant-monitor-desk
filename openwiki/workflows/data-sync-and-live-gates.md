# Data Sync And Live Gates

The data sync workflow is built to be auditable and fail-closed. The user-visible CLI presents route preview, dry-run sync, backfill, full load, live fetch, health, scheduler, incremental, revision audit, and reconcile commands, while the runtime path keeps routing, fetching, validation, and clean writes separate.

## CLI commands

`pyproject.toml` exposes `qmd-data = backend.app.cli.main:main`. `backend/app/cli/main.py` builds the parser; `backend/app/cli/data_commands.py` implements command behavior.

Important command properties from source:

- `route-preview` is read-only and returns `side_effects_allowed: false`.
- `sync` defaults to `--dry-run=True`.
- `backfill`, `full-load`, `live-fetch`, `scheduler run`, `incremental`, and `revision-audit` also default to dry-run where applicable.
- Non-dry-run sync is narrow. For many domains it fails with `USER_AUTH_REQUIRED` unless a specific implemented path and operator/live/sandbox gates are satisfied.
- `macro_series` with `source_id=fred` has a live incremental path, but it requires product live opt-in, ResourceGuard OK, required credentials or mock settings, and sandbox/isolated DB checks.

## Route planning

`SourceRoutePlanner` in `backend/app/datasources/route_planner.py` creates `SourceRoutePlan` records. It orders candidates from `SourceRegistry` as `Primary`, optional `Validation`, and optional `FallbackPolicy`. It then checks capability declarations, platform matrix availability, source registry enablement, license/user authorization, schema enum validity, and validation-only constraints.

Common route statuses include:

- `READY`
- `DISABLED_SOURCE`
- `VALIDATION_ONLY_BLOCKED`
- `CAPABILITY_MISSING`
- `USER_AUTH_REQUIRED`
- `NO_AVAILABLE_SOURCE`

Route plans are not just internal choices; `DataSourceService` emits route-plan events into `job_event_log` or the job event state machine when fetching for a job.

## DataSourceService fetch path

`DataSourceService` in `backend/app/datasources/service.py` is the production fetch facade. Its core sequence is:

```text
SourceRegistry + SourceCapabilityRegistry
  -> SourceRoutePlanner
  -> ResourceGuard
  -> selected adapter/fetch port
  -> FetchResult
  -> fetch_log / file_registry / job_event_log evidence
```

If ResourceGuard pauses or hard-stops, it raises `ResourceGuardBlockedError`. If the route is not ready and no staged test override applies, it returns a disabled-source fetch result and writes fetch evidence instead of proceeding silently.

## Sync orchestration

`DataSyncOrchestrator` in `backend/app/sync/orchestrator.py` maps job types to runners:

- `incremental`
- `backfill`
- `reconcile`
- `full_load`
- `data_quality`
- `revision_audit`
- `recover_stuck_writing_job`

Before a planned job enters `FETCHING`, `begin_fetching()` checks `ResourceGuard`. If blocked, the job transitions to `FAILED_RETRYABLE` with a resource event instead of fetching.

Production runner guards require `DataSourceService` rather than direct adapter bypasses. This preserves the route/capability/resource/audit path.

## Product live gate and tier routing

ADR-015 in `docs/decisions/ADR-015-live-acceptance-sandbox-dual-track.md` §环境门 says product live fetches must pass a unified gate, and current code implements it in `backend/app/datasources/product_live_gate.py`:

- `QMD_ALLOW_LIVE_FETCH` must be set to an opt-in value such as `1`, `true`, or `yes`.
- `gate_live_fetch_port()` also checks `ResourceGuard`.
- Missing opt-in raises `LIVE_FETCH_REJECTED`; resource block raises `RESOURCE_GUARD_PAUSED`.

`backend/app/datasources/live_tier_router.py` maps source IDs to Tier A/B/C. Tier A currently includes `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`, `alpha_vantage`, `deribit`, `baostock`, `cninfo`, and `mootdx`. Tier B contains sources such as Yahoo, AkShare, Stooq, CoinGecko, Eastmoney, Sina, TDX, iFinD, QMT, and qmt_xqshare. Tier C contains Kalshi, Polymarket, and web search.

Live acceptance uses isolated data roots under `.audit-sandbox/source-route-db*`. The **22-source matrix acceptance spine** (ADR-016) is the authoritative entry point via `qmd-ops accept-source-route-db`. Release closure uses `scripts/production_gate.py` with `--live-authorized --source-matrix-report`.

## Network and credential handling

Network/live tests are skipped by default unless pytest receives `--run-network`; see `tests/conftest.py`. Nightly CI sets `QMD_ALLOW_LIVE_FETCH=1` for a limited network-marked smoke in `.github/workflows/nightly.yml`.

Do not read `.env`. Use `.env.example`, `docs/ops/config_secret_policy.md`, and source-level environment variable names for setup. API keys and user-agent secrets must remain out of docs and logs.

Ops live-pilot authorization evidence is now operator-supplied rather than hard-coded to deleted quality files. `backend/app/ops/live_pilot_auth.py` reads `QMD_LIVE_PILOT_AUTHORIZATION`, and `backend/app/ops/staged_pilot.py` reads `QMD_STAGED_PILOT_AUTHORIZATION`; both require a markdown filename containing `_user_authorization_` and an `Approved on` marker. `backend/app/ops/tdx_manual_probe.py` has no default authorization file and requires an explicit `authorization_evidence` argument.

## Source references

- `backend/app/cli/main.py`
- `backend/app/cli/data_commands.py`
- `backend/app/datasources/service.py`
- `backend/app/datasources/route_planner.py`
- `backend/app/datasources/product_live_gate.py`
- `backend/app/datasources/live_tier_router.py`
- `backend/app/sync/orchestrator.py`
- `backend/app/ops/source_route_db_acceptance.py`
- `backend/app/ops/source_route_db_acceptance_matrix.py`
- `scripts/qmd_ops.py`
- `scripts/production_gate.py`
- `docs/decisions/ADR-015-live-acceptance-sandbox-dual-track.md`
- `docs/decisions/ADR-016-source-route-matrix-honest-closure.md`
