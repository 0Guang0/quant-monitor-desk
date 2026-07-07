# Task Plan: Source Route and DB Acceptance Spine

## Goal

把 SourceRoutePlan、DataSourceService、production-equivalent acceptance DB、degraded clean、WriteManager 审计和指标全链路验收收敛成一条成品级主干，让正式业务实现不再停留在 mock、replay、dry-run、临时 sandbox 或未持久化路由证据上。

设计目标不是把 route、fetch、validate、write、Layer read 暴露成一串新命令，而是做一个深 Module：调用方只跨一个小 Interface，Implementation 负责把现有数据平台能力串成生产等价验收。

## Current Phase

Commercial review remediation is complete as of `34990d25 test: resolve source route audit findings`. All P0/P1/P2/P3 findings from `task/audit/task-01-source-route and DB acceptance spine/review-commercial-01.txt` were resolved, adversarially rechecked, and committed with a clean worktree.

Current product-spine implementation connects the FRED tracer beyond persisted route evidence into live fetch/write/downstream-read acceptance when live gates and credentials are present. Authority vocabulary findings are cleaned and the strict guard passes; remaining helper-consumer output is advisory migration inventory, not a product PASS gate.

API/interface follow-up is complete: `preview()` and `execute()` now use the same FRED route evidence path for `macro_series:fred:fetch_macro_series`, while unsupported targets still fail honestly as `not_implemented`.

## Spec Summary

### Objective

建立一条可验收、可审计、可重放的正式数据链路：真实数据源经 SourceRoutePlan 路由和 DataSourceService fetch，写入 raw/staging，经过 DataQualityValidator 与 SourceConflictValidator，再由 WriteManager 写入 clean，最后由 Layer 读取。链路必须区分 primary-grade clean 与 degraded clean，并用 production-equivalent acceptance DB 作为成品级验收主干。

### Commands

- Catchup: `python "$env:USERPROFILE\.config\opencode\skills\planning-with-files\scripts\session-catchup.py" (Get-Location)`
- Full backend verification: `uv run python -m pytest -q`
- Boundary verification: `uv run python scripts/check_module_boundaries.py`
- Indicator binding check: `uv run python scripts/check_indicator_binding_matrix.py`
- Product gate candidate: `uv run python scripts/production_gate.py`
- Production-equivalent acceptance command: `qmd-ops accept-source-route-db`; current FRED tracer runs through the formal CLI/Module path, reports honest BLOCKED for missing authorization/credentials/env gate, and runs live fetch/write/read when gates are satisfied.

### Product Structure

- Authority docs/contracts describe final product constraints only.
- Execution phases, batch sequencing and temporary gates belong under `task/` execution plans only.
- Production-equivalent acceptance artifacts live under an isolated `QMD_DATA_ROOT`, never canonical main DuckDB.
- Unit test helpers may live under tests, but must not become product entrypoints.
- External seam: `SourceRouteDbAcceptanceSpine`.
- External Interface: `preview(request) -> AcceptancePreview` and `execute(request, data_root, live_authorized) -> AcceptanceReport`.
- Internal Adapters may wrap source-specific live helpers and old smoke wrappers during migration, but callers should not learn those shapes.

### Code Style and Boundary Rules

- Use existing project vocabulary: SourceRoutePlan, DataSourceService, FallbackPolicy, primary-grade clean, degraded clean, WriteManager, production-equivalent acceptance DB.
- Do not introduce new source-role names that revive old role models.
- Do not add mock or replay behavior to product code paths.
- Do not bypass DataSourceService, SourceRoutePlan, ResourceGuard, DataQualityValidator, SourceConflictValidator or WriteManager in product paths.
- Do not write canonical main DB during acceptance.

### Testing Strategy

- Highest seam: one production-equivalent acceptance runner / CLI path.
- Unit tests may mock external I/O only to isolate behavior.
- Product acceptance must use formal product entrypoints and must report live/replay/mock/dry_run/not_implemented honestly.
- The acceptance report is the business-facing proof, not low-level monkeypatch success.

### Success Criteria

- `SourceRouteDbAcceptanceSpine` exists as the production-equivalent acceptance Module with a small Interface and a deep Implementation.
- SourceRoutePlan is persisted for any path that fetches, validates, writes clean, or claims acceptance.
- Product fetch path goes through DataSourceService and route/capability/resource gates.
- WriteManager can audit primary-grade clean and degraded clean distinctly.
- Validation-as-fallback only occurs under explicit domain FallbackPolicy and is marked degraded.
- Production-equivalent acceptance DB uses the same migrations/schema/spec/contracts as final main DB while staying physically isolated.
- Acceptance output exposes implementation_mode, route_grade, write_grade, source_used, source_role, source_switched, quality_flags, validation/conflict status, failure class and downstream read status.
- mock/replay/dry-run/not_implemented never count as completed product acceptance.

## Testing Seam

Chosen seam: `SourceRouteDbAcceptanceSpine` runner / CLI.

Rationale: this is the highest useful seam. It cuts through route, fetch, raw, staging, validation, conflict, clean write and downstream Layer read in one business-verifiable path. Lower seams remain useful for targeted unit and integration tests, but they cannot prove product completion. Keeping the external Interface small gives Leverage to callers and Locality to maintainers.

Recommended CLI shape:

```powershell
uv run qmd-ops accept-source-route-db --data-root .audit-sandbox/source-route-db-acceptance --target macro_series:fred:fetch_macro_series --report .audit-sandbox/source-route-db-acceptance/reports/acceptance.json
```

The first tracer bullet should be `macro_series` / `fred` / `fetch_macro_series`, because current code already has a formal non-dry-run FRED macro path. If credentials or live authorization are absent, the run must produce BLOCKED or FAIL_EXTERNAL, not a fake PASS.

## Current Code Delta

| Area | Current implementation fact | Final-product gap |
|------|-----------------------------|-------------------|
| RoutePlan persistence | `DataSourceService.fetch()` can emit `ROUTE_PLAN` into `job_event_log` when `job_id` is present. | Contract/report must make `route_grade` and persisted route evidence mandatory for acceptance. |
| Source route contract | `source_route_contract.yaml` requires route planning before adapter construction and allows job_event_log/source_route_log persistence. | `route_grade=primary|degraded|blocked` is not yet a first-class required field. |
| WriteManager request | `WriteRequest` has `source_used` and `source_role`. | It lacks explicit `source_switched`, `quality_flags`, `stale_reason/fallback_reason`; audit currently writes source_switched/stale_reason as fixed values. |
| Write contract | `write_contract.yaml` requires source_used/source_role. | It does not yet require full degraded-clean metadata. |
| Existing smoke | `scripts/production_equivalent_smoke.py` initializes isolated DB and runs pytest suites/metrics. | It is a smoke wrapper, not the final acceptance Module Interface. |
| Live acceptance | `tier_a_live_acceptance.py` has isolated root/live env/report prior art. | It is Tier-A/source-specific and should become an internal Adapter or be migrated behind the new Interface. |
| Test helper | `tests/live_incremental_support.py` bootstraps acceptance DB but uses monkeypatch/factories. | It remains test-only; it must not be promoted to product acceptance. |

## Vertical Slice Issues

### Slice 0: External Acceptance Module Interface

- **Blocked by:** None.
- **User stories covered:** one highest seam, small Interface, no product acceptance by helper leakage.
- **What to build:** Define `SourceRouteDbAcceptanceSpine`, `AcceptanceRequest`, `AcceptancePreview` and `AcceptanceReport` as the external Module Interface. Keep route/fetch/validate/write/report internals hidden.
- **Acceptance criteria:**
  - [x] Callers can preview and execute acceptance without constructing route planner, adapter, fetch port, staging table or WriteRequest directly.
  - [x] AcceptanceReport contains all product/audit fields from the PRD.
  - [x] CLI delegates to the Module instead of duplicating the orchestration.
  - [x] Adding source-specific support happens through internal Adapters, not new external commands.

### Slice 0.5: Consumer Inventory and Advisory Deprecation

- **Blocked by:** None.
- **User stories covered:** safe migration from old helpers, no broken CI, no zombie acceptance code.
- **What to build:** Inventory active consumers of `production_equivalent_smoke.py`, `tier_a_live_acceptance.py`, `tests/live_incremental_support.py`, source-specific live helpers and direct adapter acceptance paths. Mark them advisory-deprecated where they overlap with the new Module, but do not remove them until delegated or unused.
- **Acceptance criteria:**
  - [x] A check or report lists remaining direct old-helper consumers.
  - [x] Old helpers are classified as Adapter, test helper, smoke wrapper or removable.
  - [x] No old helper is deleted before a replacement path exists.
  - [x] No new product behavior is added to deprecated helpers except delegation to the new Module.

### Slice 1: Persisted RoutePlan Evidence Spine

- **Blocked by:** None.
- **User stories covered:** traceability, no silent fallback, route-grade evidence.
- **What to build:** Every product fetch/write/acceptance path must persist SourceRoutePlan evidence and expose route_grade, selected source, selected role, primary failure reason and fallback policy.
- **Acceptance criteria:**
  - [x] RoutePlan is persisted before fetch in existing DataSourceService job-event path.
  - [x] Acceptance report can point to RoutePlan evidence payloads.
  - [x] Missing RoutePlan blocks production-equivalent acceptance.

### Slice 2: Formal Fetch Entry via DataSourceService

- **Blocked by:** Slice 1.
- **User stories covered:** no adapter bypass, resource/capability/license route integrity.
- **What to build:** Product runner paths must use DataSourceService and reject direct adapter execution outside unit-test helpers.
- **Acceptance criteria:**
  - [x] Formal acceptance path cannot run by direct adapter injection.
  - [x] DataSourceService emits route/fetch evidence for acceptance.
  - [x] ResourceGuard/capability/auth failures are reported, not bypassed.

### Slice 3: Degraded Clean Write Semantics

- **Blocked by:** Slice 1.
- **User stories covered:** validation-as-fallback, primary-grade vs degraded clean, downstream honesty.
- **What to build:** WriteManager and validation gate semantics support primary-grade clean and degraded clean with source_role, source_switched, quality_flags and stale/fallback reason.
- **Acceptance criteria:**
  - [x] FallbackPolicy-authorized validation source writes are marked degraded.
  - [x] Unauthorized Validation source clean writes are rejected.
  - [x] Severe conflict and schema drift block normal clean write.

### Slice 4: Production-Equivalent Acceptance DB

- **Blocked by:** Slices 1, 2 and 3.
- **User stories covered:** product-grade DB shape, no canonical DB pollution, honest acceptance.
- **What to build:** A formal isolated acceptance DB bootstrap and runner that uses final migrations/schema/spec/contracts and writes a structured acceptance report.
- **Acceptance criteria:**
  - [x] Acceptance DB path is isolated from canonical main DB.
  - [x] DB uses final migrations/schema/spec/contracts.
  - [x] Runner rejects monkeypatch-only or helper-only acceptance paths.
  - [x] Report classifies live/replay/mock/dry_run/not_implemented honestly.

### Slice 5: Downstream Layer Read Honesty

- **Blocked by:** Slices 3 and 4.
- **User stories covered:** no degraded data masquerading as primary, honest NULL/fail-closed behavior.
- **What to build:** Layer read path and acceptance report must show whether downstream consumed primary-grade clean, rejected degraded clean, downgraded it, showed it only, or returned honest NULL.
- **Acceptance criteria:**
  - [x] Downstream read status appears in acceptance report.
  - [x] source_switched rows cannot silently participate as primary-grade inputs.
  - [x] Metrics that require primary-grade inputs fail closed or return honest NULL.

### Slice 6: Authority and Contract Guardrails

- **Blocked by:** None; can run in parallel with Slice 1.
- **User stories covered:** no stage vocabulary in authority docs, no mock as product completion.
- **What to build:** Guardrails that prevent authority docs/contracts from reintroducing execution-stage vocabulary or mock/replay-as-acceptance language.
- **Acceptance criteria:**
  - [x] Authority docs/contracts stay product-state-only.
  - [x] Execution phases only appear under task execution plans.
  - [x] mock/replay/dry-run cannot be described as product acceptance success.

Current guard state: `scripts/check_authority_acceptance_language.py --strict` returns `PASS` with 0 violations after cleaning product-state wording in `docs/modules/data_sources.md`.

## Tiny Commit Plan

Status note: commits 1-8 and 12-13 have landed in a slightly different order than originally listed. Commit 9's stable validation status taxonomy is not yet implemented as a separate product concept; Commit 10 and 11 behavior is covered through WriteManager degraded evidence tests.

1. [x] Commit 1: Add/adjust the report contract for `AcceptanceRequest`, `AcceptancePreview` and `AcceptanceReport` without wiring execution. Landed as `f20915bc feat(acceptance): add source route DB report contract`.
2. [x] Commit 2: Add `SourceRouteDbAcceptanceSpine` skeleton and CLI delegation that returns `implementation_mode=not_implemented` honestly. Landed as `f6849450 feat(acceptance): add source route DB CLI stub`.
3. [x] Commit 3: Inventory old smoke/helper consumers and add advisory deprecation metadata or checks. Landed as `5e2d703e chore(acceptance): inventory legacy helper consumers`.
4. [x] Commit 4: Add contract shape for persisted RoutePlan evidence and first-class `route_grade`. Landed as `e3c9f857 feat(datasources): add route grade evidence`.
5. [x] Commit 5: Normalize current `job_event_log` `ROUTE_PLAN` payload into AcceptanceReport route evidence. Landed as `16d3f3e feat(acceptance): normalize route evidence in reports`.
6. [x] Commit 6: Add product-path enforcement that rejects direct adapter bypass outside tests if any gaps remain. No new code was needed in this pass; existing contract-driven guard coverage remains the enforcement point.
7. [x] Commit 7: Add WriteManager request/audit fields for `source_switched`, `quality_flags`, `stale_reason` and `fallback_reason`. Landed as `1149e3f0 feat(db): carry degraded write audit fields`.
8. [x] Commit 8: Add write contract tests proving degraded-clean metadata is mandatory. Landed as `efaa26cf feat(db): require degraded write evidence`.
9. [x] Commit 9: Add validation gate behavior for PASSED_PRIMARY, PASSED_DEGRADED, FAILED and MANUAL_REVIEW_REQUIRED or equivalent stable product statuses. Covered by acceptance report job-status mapping and existing validation-gate tests.
10. [x] Commit 10: Add tests proving unauthorized Validation source cannot write clean. Covered by `efaa26cf`.
11. [x] Commit 11: Add tests proving FallbackPolicy-authorized Validation source writes only degraded clean. Covered by `efaa26cf`.
12. [x] Commit 12: Build production-equivalent acceptance DB bootstrap using isolated QMD_DATA_ROOT and final migrations/schema/spec/contracts behind the new Module. Landed as `8b0d3e4e feat(acceptance): bootstrap isolated acceptance db`.
13. [x] Commit 13: Wire the first `macro_series` / `fred` tracer bullet through route preview behind the Module; without live authorization it reports BLOCKED honestly. Landed as `1132281e feat(acceptance): trace fred macro route block`.
13a. [x] Commit 13a: Add FRED credential gate for the tracer; with `--allow-live-fetch` but no `FRED_API_KEY`, report BLOCKED with route evidence. Landed as `45d7d7d feat(acceptance): block fred tracer without api key`.
13b. [x] Commit 13b: Persist FRED tracer RoutePlan evidence into the isolated acceptance DB `job_event_log`. Landed as `0df7a2a feat(acceptance): persist tracer route evidence`.
14. [x] Commit 14: Add acceptance report writer with implementation_mode, route_grade, write_grade and downstream_layer_read_status envelope. Landed as `c2bb15f feat(acceptance): centralize report artifact writing`.
15. [x] Commit 15: Migrate or wrap `production_equivalent_smoke.py` as a compatibility Adapter. Landed as `bef50d1c feat(acceptance): wrap smoke source route adapter`.
16. [x] Commit 16: Add representative end-to-end acceptance test that produces live or honest BLOCKED/FAIL_EXTERNAL output without mock success. Landed as `a3de1536 test(acceptance): verify cli route evidence persistence`.
17. [x] Commit 17: Update Layer read acceptance checks for degraded clean handling. The acceptance spine now probes Layer1 clean read after FRED live clean write; existing Layer1/Layer2 readers fail-closed on `source_switched=True`.
18. [x] Commit 18: Add a guard that checks authority docs/contracts for execution-stage vocabulary and reports violations. Landed as `1a3b1ff feat(acceptance): guard authority acceptance language`.
19. [x] Commit 19: Run full verification and update task evidence. Landed as this planning-file sync after full pytest/hook verification.
20. [x] Commit 20: Resolve all commercial review findings in `review-commercial-01.txt` under `/testing-guidelines`; remove remaining meta/artifact/phase/fake-RED/source-text tests and tighten exception/outcome assertions. Landed as `34990d25 test: resolve source route audit findings`.

Each commit must leave the codebase working. If a commit would touch more than about five files or mix two concerns, split it further.

## Checkpoints

### Checkpoint A: Route and Fetch Spine

- [x] SourceRoutePlan persisted in job_event_log route event payloads, including the FRED acceptance tracer path.
- [x] Product fetch path uses DataSourceService in the existing route/fetch spine; acceptance tracer runs live fetch/write/read when gates are satisfied and blocks honestly otherwise.
- [x] Direct adapter bypass cannot be used for product acceptance.

### Checkpoint B: Clean Write Semantics

- [x] primary-grade clean and degraded clean are distinguishable in audit.
- [x] unauthorized Validation source clean write rejected.
- [x] FallbackPolicy-authorized degraded write is fully marked.

### Checkpoint C: Production-Equivalent Acceptance

- [x] Acceptance DB is isolated but schema-equivalent.
- [x] Acceptance report exposes required fields.
- [x] mock/replay/dry-run/not_implemented cannot pass as product completion.
- [x] Legacy `production_equivalent_smoke.py` can delegate to the acceptance spine and fails honestly when the spine report is not PASS.
- [x] FRED acceptance report records downstream Layer1 read status and route/fetch evidence in the isolated DB.

### Checkpoint D: Ready for Human Review

- [x] Full test commands recorded.
- [x] ResourceGuard/product-live gate status recorded for product-spine acceptance runs as BLOCKED or live PASS evidence.
- [x] Files modified summarized.
- [x] Any source failures classified as FAIL_EXTERNAL, blocked, or implementation gap.
- [x] Commercial review P0/P1/P2/P3 findings resolved and rechecked.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Reuse existing data platform modules instead of rewriting from scratch | Existing SourceRoutePlan, DataSourceService, validators, WriteManager and sync orchestrator are the correct product seams; the gap is spine integration and honesty. |
| Use one highest acceptance seam | A single production-equivalent acceptance runner proves the business chain better than many low-level seams. |
| Keep mock only in unit tests | External I/O needs isolation in unit tests, but mock must not count as product acceptance. |
| Preserve canonical main DB write prohibition | The acceptance DB must expose product defects without polluting real user data. |
| Treat stage vocabulary as execution-plan-only | Authority docs/contracts should describe product state, not temporary delivery stages. |
| Use `SourceRouteDbAcceptanceSpine` as the external Module | A small Interface hides route/fetch/validate/write/report complexity and avoids a shallow collection of commands. |
| Start RoutePlan persistence from `job_event_log` | Current code already emits `ROUTE_PLAN`; a dedicated route table should be added only if query/report needs justify the migration. |
| Deprecate old acceptance helpers advisories first | Existing tests and runbooks may still use them; removal before delegation would create churn without product value. |

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing tests rely on direct adapter injection | Medium | Keep adapter injection only in unit tests; add product-path tests that reject it for acceptance. |
| Real external sources fail due to network, auth or rate limits | High | Report FAIL_EXTERNAL or blocked honestly; do not convert to mock PASS. |
| Schema changes needed for route/degraded audit fields | Medium | Prefer existing audit/event payloads first; add schema only with migration and contract tests. |
| Acceptance runner becomes too broad | High | Start with one representative tracer bullet; expand only after report shape is stable. |
| Authority docs regain stage vocabulary | Medium | Add guardrail check against authority docs/contracts, excluding task execution plans and historical registries if necessary. |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| `session-catchup.py` not found under `$USERPROFILE\.opencode\skills` | 1 | Retried using actual skill path under `$USERPROFILE\.config\opencode\skills`. |
| Acceptance tests still expected generic `NOT_IMPLEMENTED` for the new FRED tracer target | 1 | Updated generic tests to use a non-tracer target and FRED CLI tests to expect `BLOCKED` plus route evidence. |
| CLI subprocess test removed `FRED_API_KEY`, but project config reloaded it from `.env` | 1 | Set `FRED_API_KEY` to an empty string in the subprocess env so config does not refill it and product code still treats it as missing. |

## Question Resolution Status

1. First downstream Layer read: resolved for this task with the Layer1 FRED macro clean reader probe. Layer2 already has fail-closed source-switched coverage and remains a future expansion target, not a blocker for this representative tracer bullet.
2. Final CLI spelling: deferred product naming choice. Current supported command is `qmd-ops accept-source-route-db`; changing the spelling later should keep the `SourceRouteDbAcceptanceSpine` interface unchanged.
3. Authority docs cleanup: resolved. `docs/modules/data_sources.md` was cleaned and `scripts/check_authority_acceptance_language.py --strict` passes with 0 violations.

## Notes

- This plan intentionally describes implementation order and task slicing. Stage and task vocabulary is allowed here because this file is an execution planning artifact, not an authority design document.
- The PRD for this task is `PRD.md` in the same directory.
- Issue tracker publication has not been performed in this session; the local task directory is the current source of planning truth.
