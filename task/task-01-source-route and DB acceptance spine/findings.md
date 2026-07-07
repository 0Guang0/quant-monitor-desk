# Findings & Decisions

## Requirements

- Create exactly three planning files in this task directory: `task_plan.md`, `findings.md`, `progress.md`.
- Do not create extra planning files.
- Write `task_plan.md` using the combined perspective of spec-driven development, to-issues, planning-and-task-breakdown and request-refactor-plan.
- Continue from the existing PRD about Source Route and DB Acceptance Spine.
- Keep task-specific execution planning under this task directory, not in authority design docs.
- The implementation objective is a production-equivalent acceptance spine, not a from-scratch rewrite of the whole data platform.

## Research Findings

- Previous conversation established that authority docs/contracts must describe final product constraints only; execution stages belong under task plans.
- Existing codebase already has relevant modules: SourceRoutePlan, DataSourceService, DataQualityValidator, SourceConflictValidator, WriteManager, sync orchestrator, Layer read paths and `.audit-sandbox` / `QMD_DATA_ROOT` isolation.
- `DataSourceService.fetch()` already emits a `ROUTE_PLAN` event into `job_event_log` when a job_id is present, so the first persistence path should build on that instead of inventing a second table immediately.
- `source_route_contract.yaml` already requires route planning before adapter construction and allows persistence in `job_event_log.payload_json` or `source_route_log`, but it does not yet make `route_grade` a required first-class field.
- Current `WriteRequest` has `source_used` and `source_role`, but not full degraded clean metadata: `source_switched`, `quality_flags`, `stale_reason` and `fallback_reason`.
- Current `WriteManager` inserts into `write_audit_log.source_switched` and `stale_reason`, but the implementation still writes fixed `False` / `None`; this would erase degraded-clean evidence unless changed.
- `scripts/production_equivalent_smoke.py` is an isolated smoke/metrics wrapper over pytest suites, not the final production-equivalent acceptance Interface.
- `backend/app/ops/tier_a_live_acceptance.py` is strong prior art for isolated live acceptance, manifests and environment checks, but its Interface is Tier-A/source-specific.
- `tests/live_incremental_support.py` bootstraps an acceptance DB for tests but uses monkeypatching and injected factories, so it must remain a test helper.
- Existing acceptance assets are not sufficient as-is: source-specific sandbox/live acceptance helpers and temporary test DBs are useful prior art, but they do not replace a single production-equivalent acceptance spine.
- The correct business distinction is primary-grade clean vs degraded clean.
- Validation sources may enter clean only when domain FallbackPolicy explicitly authorizes a degraded write; otherwise they remain validation/source_conflict/manual_review/evidence inputs.
- mock/replay/dry-run/not_implemented must be report classifications, not product acceptance success states.
- RoutePlan persistence is a product requirement, not an optional implementation detail.
- Implemented acceptance spine now has a concrete report contract and CLI surface: `SourceRouteDbAcceptanceSpine`, `AcceptanceRequest`, `AcceptancePreview`, `AcceptanceReport`, and `qmd-ops accept-source-route-db`.
- Acceptance execution now rejects canonical main data roots before bootstrapping, then creates an isolated `duckdb/quant_monitor.duckdb` with production migrations.
- `SourceRoutePlan.route_grade` is now first-class evidence. Current grades are `primary`, `degraded` and `blocked`, with `not_planned` used at the acceptance report layer before route planning exists.
- Route evidence normalization now maps `job_event_log`-style route payloads into the acceptance report fields: route plan id, route grade, source used, source role, source switched, quality flags and failure class.
- `WriteRequest` now carries degraded-clean metadata: `source_switched`, `quality_flags`, `stale_reason` and `fallback_reason`.
- `WriteManager` audit now writes `source_switched` and a stale/fallback reason into `write_audit_log`; `fallback_reason` temporarily maps into `stale_reason` until a dedicated audit column is migrated.
- Degraded clean writes are now fail-closed unless they carry a degraded role (`validation` or `fallback`), `source_switched=True`, quality flags and a stale/fallback reason.
- First tracer target is implemented for `macro_series:fred:fetch_macro_series`. It currently proves route evidence, live-authorization honesty and FRED credential honesty: without `--allow-live-fetch` or without `FRED_API_KEY`, it returns `BLOCKED` instead of pretending to pass.
- Full route/fetch/write/read acceptance for the FRED tracer is not complete yet. The tracer stops after route evidence and authorization classification.
- Acceptance report artifact writing is now owned by `backend.app.ops.source_route_db_acceptance.write_acceptance_report`; `qmd-ops accept-source-route-db` delegates report persistence instead of hand-building JSON.
- FRED tracer RoutePlan evidence is now persisted into the isolated acceptance DB `job_event_log` as `ROUTE_PLAN`; the report `route_plan_id` can be traced back to the stored payload.
- `production_equivalent_smoke.py` now has an explicit optional compatibility adapter to `SourceRouteDbAcceptanceSpine`; it does not change default smoke behavior and returns failure when the delegated acceptance report is not PASS.
- The formal CLI path now has end-to-end evidence that report `route_plan_id` is persisted in the isolated acceptance DB `job_event_log`, not only present in stdout JSON.
- `scripts/check_authority_acceptance_language.py` now reports execution-stage vocabulary and non-live-mode-as-success claims across the active authority path set.
- Current authority guard output is `FAIL` with 4 remaining `execution_stage_vocabulary` findings in `docs/modules/data_sources.md`; this is an open cleanup item, not a completed acceptance condition.
- Existing Layer1 and Layer2 clean readers already reject `source_switched=True` rows (`tests/test_layer1_clean_reader.py`, `tests/test_layer2_clean_reader.py`), but `SourceRouteDbAcceptanceSpine` still does not run a downstream read probe after clean write.
- CNINFO product-live factory had a hook-blocking mismatch: `use_mock=False` returned the direct akshare network port even though a replay-first product-live port existed. It now returns `CninfoProductLiveFetchPort`, with regression coverage.
- Planning catchup on 2026-07-07 completed with no output from `C:\Users\Guang\.claude\skills\planning-with-files\scripts\session-catchup.py`; no additional unsynced context was reported.

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Reuse existing modules and refactor the spine | The codebase already has the right domain modules; the problem is fragmented product-path integration and acceptance honesty. |
| Use production-equivalent acceptance runner / CLI as the highest test seam | It verifies the full business chain with the fewest seams and avoids proving isolated internals while missing product failure. |
| Keep mock only in unit tests | Unit tests need external I/O isolation; product acceptance must not treat mock/replay as completion. |
| Use isolated DB with final schema/contracts | This exposes real product issues without contaminating canonical main DB. |
| Keep execution-stage vocabulary in task plans only | Prevents future agents from treating temporary stages as final product constraints. |
| Introduce `SourceRouteDbAcceptanceSpine` as the deep Module | One small Interface should hide route/fetch/validation/conflict/write/Layer/report Implementation detail. |
| Use `job_event_log` RoutePlan persistence first | It matches current code and avoids premature schema churn; `source_route_log` remains a future internal Adapter if query needs require it. |
| Treat old helpers as advisory-deprecated Adapters first | Existing tests/runbooks may still depend on them; migrate consumers before removal. |

## Interface Analysis

Recommended external Module: `SourceRouteDbAcceptanceSpine`.

Recommended Interface:

```text
preview(request) -> AcceptancePreview
execute(request, data_root, live_authorized) -> AcceptanceReport
```

This Interface is deep because callers do not need to know how to construct `SourceRoutePlanner`, `FetchPort`, adapter, `SyncJobSpec`, staging table, validation report, conflict report, `WriteRequest` or Layer read probe. Those facts stay local to the Implementation.

Rejected shallow shape:

```text
plan_route(); fetch(); write_raw(); validate(); write_clean(); read_layer(); build_report()
```

That shape would spread correctness rules across callers and tests. It would reduce Locality and make every source-specific path re-learn the same acceptance contract.

## Migration Findings

- Replacement exists conceptually but not yet as code: `SourceRouteDbAcceptanceSpine`.
- Active consumers of old helpers must be measured before removal.
- Deprecation should be advisory until the new Module covers at least one real tracer bullet and old entrypoints can delegate to it.
- Compulsory removal should wait until CI, tests, docs and runbooks no longer call the old helper directly.
- Migration tooling should report direct calls to old helper entrypoints and direct adapter acceptance paths.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| User-provided catchup command path used `.opencode`, but installed skill path is `.config\opencode` | Retried catchup with actual installed path. |
| Authority docs previously contained execution-stage terms | Cleaned the active authority docs/specs/rules touched in this conversation; task plans may still use task sequencing vocabulary. |
| Initial plan under-specified the external Module Interface | Added explicit `SourceRouteDbAcceptanceSpine` seam and preview/execute Interface. |
| Initial plan treated old helpers mostly as prior art | Reframed them as active migration/deprecation subjects that may need compatibility Adapters. |
| Acceptance tests initially still expected `NOT_IMPLEMENTED` for `macro_series:fred:fetch_macro_series` after the tracer was implemented | Changed generic not-implemented tests to use a non-tracer target, and changed FRED CLI tests to assert `BLOCKED` plus route evidence. |
| CLI subprocess tests can accidentally reload `FRED_API_KEY` from project `.env` if the variable is deleted | Set `FRED_API_KEY` to an empty string when testing missing credentials; config will not override an existing key, and product code treats empty as missing. |
| Pre-commit full pytest repeatedly failed in CNINFO live incremental test with `FAILED_FINAL` | Root cause was the CNINFO factory using direct external network for product-live; switched it to the existing replay-first product-live port and added `tests/test_cninfo_product_live_factory.py`. |

## Implementation Commits

| Commit | Meaning |
|--------|---------|
| `f20915bc` | Added source route DB acceptance report contract. |
| `f6849450` | Added `qmd-ops accept-source-route-db` CLI stub delegated to the spine. |
| `5e2d703e` | Added advisory legacy acceptance helper consumer inventory. |
| `e3c9f857` | Added route grade evidence to route models and payloads. |
| `16d3f3e` | Normalized route evidence into acceptance reports. |
| `1149e3f0` | Carried degraded write audit fields through WriteManager. |
| `efaa26cf` | Required complete degraded write evidence before clean writes. |
| `8b0d3e4e` | Bootstrapped isolated production-equivalent acceptance DB. |
| `1132281e` | Added FRED macro tracer route evidence and blocked live authorization result. |
| `45d7d7d` | Added FRED macro tracer missing-API-key block while preserving route evidence. |
| `c2bb15f` | Centralized acceptance report artifact JSON writing in the acceptance module and delegated CLI persistence to it. |
| `0df7a2a` | Persisted FRED tracer RoutePlan evidence into the isolated acceptance DB job event log. |
| `bef50d1c` | Wrapped `production_equivalent_smoke.py` as an optional compatibility adapter to the acceptance spine. |
| `a3de1536` | Added CLI end-to-end proof that route evidence is persisted in the isolated acceptance DB. |
| `7448a62b` | Kept CNINFO product-live factory on the existing replay-first port to avoid external-network flake in full pytest. |
| `1a3b1ff` | Added authority acceptance language guard and fixture tests. |

## Resources

- PRD: `task/task-01-source-route and DB acceptance spine/PRD.md`
- Current planning files: `task_plan.md`, `findings.md`, `progress.md`
- Relevant product vocabulary: SourceRoutePlan, DataSourceService, FallbackPolicy, WriteManager, primary-grade clean, degraded clean, production-equivalent acceptance DB.
- Relevant existing seams: production gate, module boundary checks, indicator binding checks, SourceRoutePlan tests, WriteManager tests, sync orchestrator tests, live acceptance helpers.
- Current code evidence: `backend/app/datasources/service.py`, `backend/app/datasources/route_planner.py`, `backend/app/sync/orchestrator.py`, `backend/app/db/write_manager.py`, `scripts/production_equivalent_smoke.py`, `backend/app/ops/tier_a_live_acceptance.py`, `tests/live_incremental_support.py`.
- Authority evidence: `docs/modules/source_route_plan.md`, `docs/modules/data_sources.md`, `docs/modules/write_manager.md`, `docs/architecture/04_data_architecture.md`, `rules/GLOBAL_RULES.md`, `rules/GLOBAL_TESTING_POLICY.md`, `specs/contracts/source_route_contract.yaml`, `specs/contracts/write_contract.yaml`, `specs/schema/schema.sql`.

## Visual/Browser Findings

- No visual/browser/PDF content was used in this session.

---

*Update this file after every 2 view/browser/search operations.*
*This prevents information from being lost.*
