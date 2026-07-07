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
- First tracer target is implemented for `macro_series:fred:fetch_macro_series`. It proves route evidence, live-authorization honesty, FRED credential honesty and product-live env gate honesty: missing `--allow-live-fetch`, `FRED_API_KEY` or `QMD_ALLOW_LIVE_FETCH` returns `BLOCKED` instead of pretending to pass.
- Full route/fetch/write/read acceptance for the FRED tracer is now wired for the live path: when gates and credentials are present, the spine uses existing FRED incremental sync, writes clean into the isolated acceptance DB, probes Layer1 clean read and reports `downstream_layer_read_status`.
- Acceptance report artifact writing is now owned by `backend.app.ops.source_route_db_acceptance.write_acceptance_report`; `qmd-ops accept-source-route-db` delegates report persistence instead of hand-building JSON.
- FRED tracer RoutePlan evidence is now persisted into the isolated acceptance DB `job_event_log` as `ROUTE_PLAN`; the report `route_plan_id` can be traced back to the stored payload.
- `production_equivalent_smoke.py` now has an explicit optional compatibility adapter to `SourceRouteDbAcceptanceSpine`; it does not change default smoke behavior and returns failure when the delegated acceptance report is not PASS.
- The formal CLI path now has end-to-end evidence that report `route_plan_id` is persisted in the isolated acceptance DB `job_event_log`, not only present in stdout JSON.
- `scripts/check_authority_acceptance_language.py` now reports execution-stage vocabulary and non-live-mode-as-success claims across the active authority path set.
- Current authority guard output is `PASS` with 0 findings after product-state wording cleanup in `docs/modules/data_sources.md`.
- Existing Layer1 and Layer2 clean readers already reject `source_switched=True` rows (`tests/test_layer1_clean_reader.py`, `tests/test_layer2_clean_reader.py`); `SourceRouteDbAcceptanceSpine` now also runs a Layer1 downstream read probe after FRED clean write.
- API/interface review found and fixed one small contract inconsistency after the FRED live spine landed: `execute()` supports `macro_series:fred:fetch_macro_series`, and `preview()` now reuses the existing FRED route preview path instead of returning generic `not_implemented`.
- The old Open Questions are no longer implementation blockers: Layer1 is the first downstream acceptance read, `qmd-ops accept-source-route-db` remains the current CLI spelling, and authority docs cleanup is complete.
- User clarified on 2026-07-07 that task-01 is not finally closed by the FRED representative tracer alone. Final close/pass now requires legacy helper / old smoke migration and cleanup, plus acceptance-spine coverage for every source listed in `docs/modules/data_sources.md` section 5.9.1.
- `docs/modules/data_sources.md` section 5.9.1 lists 22 design-level data sources for the source matrix: QMT / xtdata, baostock, AkShare, CNINFO, Yahoo Finance / yfinance, Alpha Vantage, Stooq, Deribit, CoinGecko, US Treasury, SEC EDGAR, CFTC COT, BIS, World Bank, FRED, Kalshi, Polymarket, mootdx / TDX compatible, 东方财富, 新浪财经, 同花顺 / iFinD and Web Search.
- Multi-source expansion should follow old helper/smoke cleanup, not precede it. Otherwise each new source can accidentally grow both the new spine and the old helper paths, leaving two competing product acceptance seams.
- `/design-an-interface` review compared three shapes: minimal single-target `preview/execute`, registry-driven batch methods, and migration-first cleanup. Chosen direction is migration-first cleanup plus the existing small public Interface; any full-matrix runner should loop over the same `AcceptanceReport` contract rather than adding provider-specific public methods.
- `/source-driven-development` source of truth for the source list is local authority documentation plus machine registries: `docs/modules/data_sources.md` for human design scope, and `specs/datasource_registry/source_registry.yaml` / `source_capabilities.yaml` for implementation enumeration.
- CNINFO product-live factory had a hook-blocking mismatch: `use_mock=False` returned the direct akshare network port even though a replay-first product-live port existed. It now returns `CninfoProductLiveFetchPort`, with regression coverage.
- Planning catchup on 2026-07-07 completed with no output from `C:\Users\Guang\.claude\skills\planning-with-files\scripts\session-catchup.py`; no additional unsynced context was reported.
- Commercial review file `task/audit/task-01-source-route and DB acceptance spine/review-commercial-01.txt` had no P0/P1 findings in its first block, but did contain later P1 findings around broad exceptions and meta-testing; all listed P0/P1/P2/P3 items are resolved as of `34990d25`.
- Review remediation removed pytest cases that only protected repository artifacts, docs wording, phase placeholders, source text, imports, manifests, or other tests. Remaining tests are closer to observable production behavior per `/testing-guidelines`.
- Adversarial recheck after remediation returned exactly `No unresolved review findings found.`
- `conversation_history/` is a local binary session cache and is now ignored; it is not part of task evidence.

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
| Make old helper/smoke cleanup the next prerequisite before expanding sources | The acceptance seam must be singular before the source matrix grows, otherwise old helper PASS and spine PASS remain ambiguous. |
| Expand by target specs behind `preview/execute`, not provider-specific public methods | The report contract is already the stable API; source-specific public methods would make the module shallow. |
| Treat unconfigured/licensed/local-terminal sources as honest blocked states | All documented sources must be represented, but live PASS is only valid when real prerequisites exist. |

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
- Final closure now requires a strict migration gate: product/runtime consumers of old helper or old smoke seams must reach zero, removable wrappers must be deleted, and remaining test helpers must be unable to claim product acceptance PASS.

## Source Matrix Expansion Findings

- The total documented source list has mixed roles: primary candidates, validation-only sources, fallback candidates, official low-frequency sources, licensed/local-terminal sources and manual-review evidence sources. One PASS rule cannot fit all of them.
- `AcceptanceReport` should remain the common business proof. Some sources will PASS when configured, some will BLOCK when credentials/licensing/local terminals are missing, and some should remain validation/manual-review-only by design.
- Validation-only sources such as AkShare, Yahoo, Stooq, Polymarket, mootdx, 东方财富, 新浪财经, 同花顺 / iFinD and Web Search must not silently write primary-grade clean.
- QMT / xtdata and 同花顺 / iFinD need explicit user/local/commercial authorization gates before live execution.
- Web Search should be represented as manual-review evidence only, not a clean main-value writer.

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
| `34990d25` | Resolved all `review-commercial-01.txt` test-quality findings and committed the cleanup after full verification. |

## Resources

- PRD: `task/task-01-source-route and DB acceptance spine/PRD.md`
- Current planning files: `task_plan.md`, `findings.md`, `progress.md`
- Relevant product vocabulary: SourceRoutePlan, DataSourceService, FallbackPolicy, WriteManager, primary-grade clean, degraded clean, production-equivalent acceptance DB.
- Relevant existing seams: production gate, module boundary checks, indicator binding checks, SourceRoutePlan tests, WriteManager tests, sync orchestrator tests, live acceptance helpers.
- Current code evidence: `backend/app/datasources/service.py`, `backend/app/datasources/route_planner.py`, `backend/app/sync/orchestrator.py`, `backend/app/db/write_manager.py`, `scripts/production_equivalent_smoke.py`, `backend/app/ops/tier_a_live_acceptance.py`, `tests/live_incremental_support.py`.
- Authority evidence: `docs/modules/source_route_plan.md`, `docs/modules/data_sources.md`, `docs/modules/write_manager.md`, `docs/architecture/04_data_architecture.md`, `rules/GLOBAL_RULES.md`, `rules/GLOBAL_TESTING_POLICY.md`, `specs/contracts/source_route_contract.yaml`, `specs/contracts/write_contract.yaml`, `specs/schema/schema.sql`.

## Visual/Browser Findings

- No visual/browser/PDF content was used in this session.

## Session 2026-07-07 Evening: Matrix Live Closure, Failure Taxonomy, User Policy

### User policy (binding for closure)

| Policy | Meaning |
|--------|---------|
| Keep `QMD_ALLOW_LIVE_FETCH=1` | Global live gate stays on for matrix runs. |
| `QMT_XTDATA_AUTHORIZED` unavailable | **Expected FAIL/BLOCKED** — exposes QMT currently has no local-terminal qualification; **do not fake auth or hide**. |
| `THS_IFIND_LICENSE_ARTIFACT` unavailable | **Expected FAIL/BLOCKED** — exposes iFinD currently has no license qualification; **do not fake auth or hide**. |
| Isolated acceptance root | Writes go to isolated `data_root` (`duckdb/quant_monitor.duckdb` + `raw/`), same migrations/schema as production, full route/fetch/validate/write chain; **never canonical main DB**. |

### 22-source authorization map (current machine `.env` snapshot)

| Bucket | Sources | Extra env beyond `QMD_ALLOW_LIVE_FETCH` | `.env` status |
|--------|---------|----------------------------------------|---------------|
| Licensed / local terminal | QMT/xtdata | `QMT_XTDATA_AUTHORIZED` | **MISSING** → expected blocked |
| Licensed validation | 同花顺/iFinD | `THS_IFIND_LICENSE_ARTIFACT` | **MISSING** → expected blocked |
| API-key / identity | Alpha Vantage, FRED, SEC EDGAR | `ALPHA_VANTAGE_API_KEY`, `FRED_API_KEY`, `SEC_EDGAR_USER_AGENT` | **READY** |
| Public / no matrix `auth_env` | baostock, AkShare, CNINFO, Yahoo, Stooq, Deribit, CoinGecko, US Treasury, CFTC, BIS, World Bank, Kalshi, Polymarket, mootdx, 东财, 新浪, Web Search | none in matrix | need live gate only |

**Closure implication:** Final matrix closure with user policy is **20/22 minimum honest baseline** when QMT+iFinD lack qualification; do not treat their BLOCKED as bugs to patch away.

### Failure taxonomy (business-facing)

Three orthogonal dimensions — do not mix:

1. **无资格 (A)** — missing auth/license/local terminal → honest BLOCKED; QMT, iFinD per user policy.
2. **探针/符号错 (B)** — full production-equivalent chain wired in isolated DB, live network works, but matrix probe symbol mismatches live payload → false `rows_written=0` FAIL_EXTERNAL.
3. **外部/网络 (C)** — chain wired, upstream unreachable → `NETWORK_ERROR` / FAIL_EXTERNAL (SEC).

**Deribit is type B, not A, not “source only has expired data”:**

- Deribit **is integrated**: `create_deribit_fetch_port` live → `run_deribit_incremental` → `crypto_derivative_clean` in isolated acceptance DB (same class as baostock/SEC).
- Expired `BTC-28JUN24-65000-C` lives in **replay/mock whitelist only**; live API returns hundreds of active options (e.g. `BTC-8JUL26-55000-C`).
- Root cause: matrix handler hardcoded expired seed; `deribit_staging_rows_from_bundle` filters `instrument_name == req.instrument_id` → 0 staging rows while `overall_status` can still be COMPLETED/EMPTY_RESPONSE.
- Fix direction (uncommitted): `resolve_deribit_live_option_instrument()` + `resolve_matrix_deribit_live_instrument()`; matrix uses per-instrument `clean_row_count` not whole-table count.

**Contrast with other sources:**

| Source | Integration | Issue class |
|--------|-------------|-------------|
| CNINFO / AV / Kalshi | Full chain | Was B (wrong symbol/ticker); SSOT helpers fixed |
| CoinGecko / Kalshi / QMT evidence | evidence_fetch path | Was missing adapter; fixed with product live port + raw evidence |
| SEC EDGAR | Full chain | C — `NETWORK_ERROR` (SSL EOF in agent env; urllib) |
| QMT / iFinD | Gates exist | A — no qualification; keep failing |

### 「验收单 vs 活市场」documentation intent

Proposed matrix/contract prose (not yet written to authority docs):

- **验收单** = replay/test fixed symbols (may include expired contracts) for deterministic offline tests.
- **活市场** = live matrix must align probe with current API-tradable instruments.
- Prevents copying test-fixture names into live acceptance and getting false FAIL.

**Expired/hardcoded symbols in codebase — scope is narrow:**

- Heavy in `tests/fixtures/` and mock whitelists (Deribit expired options, old Kalshi `KXHIGHNY-24`).
- Stable live probes like `sh.600519`, `SPY` are **not expired** — fixed but actively traded samples.
- Product runtime matrix live handlers should use SSOT helpers or dynamic resolution, not replay seeds.

### Full live matrix run v2 (2026-07-07 Phase 13 complete)

- Report: `.audit-sandbox/source-route-db-full-live-v2/reports/source-matrix-acceptance.json`
- Result: **closure pass_count=21/22**; **fail_external=1** (SEC only)
- QMT: `status=FAIL`, `failure_class=BLOCKED`, **`closure_outcome=PASS`** (deferred qualification)
- iFinD: `status=FAIL`, `failure_class=BLOCKED`, **`closure_outcome=PASS`**
- Deribit: **PASS** after live instrument resolution
  - SEC: **FAIL_EXTERNAL** `NETWORK_ERROR` — not mocked; httpx2 client change did not fix SSL in this network
- Checker `--live-authorized`: exit 1, one violation `sec_edgar FAIL_EXTERNAL`
- **ADR:** [ADR-016](../docs/decisions/ADR-016-source-route-matrix-honest-closure.md) — qualification deferred vs must PASS;禁止 mock 假绿

### Code changes this session (uncommitted)

| Area | Change |
|------|--------|
| `deribit_port.py` | `resolve_deribit_live_option_instrument()` |
| `source_route_db_acceptance_matrix.py` | `resolve_matrix_deribit_live_instrument()`, `QUALIFICATION_DEFERRED_SOURCE_IDS`, closure exempt for QMT/iFinD |
| `source_route_db_acceptance.py` | Deribit matrix uses resolved instrument + per-result `clean_row_count`; SEC matrix uses per-CIK result |
| `sec_edgar_port.py` | `_fetch_sec_submissions_json` via `httpx2` + 3 retries |
| `source_route_db_acceptance_contract.yaml` | `qualification_deferred_sources`, `live_vs_replay_probe`, deribit/coingecko symbol_ssot |
| Tests | closure deferred qualification + API key strict tests + deribit/sec unit tests |

### Verification status

| Command | Result |
|---------|--------|
| Targeted new tests + deribit e2e | **7 passed, 2 skipped** |
| Full `uv run pytest -q` | **3 failed** — `test_cn_market_adapters.py` license-gate tests; `.env`/session auth vars make QMT/iFinD appear AUTHORIZED when tests expect default disabled; **unrelated to Deribit/SEC changes** |
| SEC live probe (agent network) | SSL EOF to `data.sec.gov` — cannot verify live SEC fix in this environment |

### Next steps (recommended)

1. **Commit** Phase 13 changes after user review.
2. **SEC**: retry when network to `data.sec.gov` works; until then closure correctly stays FAIL on SEC only.
3. **Optional pytest hygiene**: `monkeypatch.delenv` in cn_market default-disabled tests (see user question).
4. **Do not** fake QMT/iFinD authorization.

---

*Update this file after every 2 view/browser/search operations.*
*This prevents information from being lost.*
