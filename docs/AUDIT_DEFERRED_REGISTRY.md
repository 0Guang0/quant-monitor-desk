# Audit Deferred Items Registry

**Single source of truth** for open issues, intentional deferrals, and resolved audit items.

## Resolution policy (mandatory)

Every issue MUST be in exactly one state:

| State        | Meaning                                                          |
| ------------ | ---------------------------------------------------------------- |
| **RESOLVED** | Implemented + tested + evidence linked                           |
| **OPEN**     | Not done; blocks the listed gate until closed                    |
| **DEFERRED** | Not done yet; **must** name a concrete resolution phase and task |

**Rules:**

1. **Non-blocking ≠ abandoned.** If an item does not block task 017, it still needs `Resolution phase`, `Task hook`, and `Closure test`.
2. **No silent drift.** Undocumented gaps are violations; add a row here (or in `ROUND2_REPAIR_ALIGNMENT_TRACKER.md` for R2.5-only) before merge.
3. **Phase names must be actionable:** prefer task IDs (`017`…`035`) or Trellis slug over vague “later”.
4. **Registry wins on conflict** with narrative docs; update narratives to link here.

**Companion docs:** `docs/UNRESOLVED_ISSUES_REGISTRY.md` (current unresolved/deferred split) · `docs/RESOLVED_ISSUES_REGISTRY.md` (closed items split) · `docs/quality/ROUND2_REPAIR_ALIGNMENT_TRACKER.md` (R2.5 + Round 4 contract tables) · `ROUND2_GAPS_AND_DEVIATIONS.md` (narrative) · `ROUND3_HANDOFF.md` (gate).

---

## OPEN — blocks Round 3 entry (017)

_(none — last gate `PROC-R2.5-1` closed 2026-06-19 via PR #15)_

---

## DEFERRED — Round 2.6 (contract gate + routing service)

| ID          | Item                              | Resolution phase            | Task hook                                     | Blocks 017? | Closure test / evidence                                       |
| ----------- | --------------------------------- | --------------------------- | --------------------------------------------- | ----------- | ------------------------------------------------------------- |
| R2.6-IMPL-6 | `qmd data` production CLI         | **Round 3 ops**             | `035` prep · Task 2 docs                      | No          | CLI smoke when implemented                                    |
| R2.6-IMPL-8 | Live QMT/Yahoo/xqshare validation | **User-authorized staging** | `docs/ops/qmt_xqshare_setup.md` · ops runbook | No          | authorized E2E only; inspect CLI has no `--enable-qmt` (D-11) |

## RESOLVED — Round 2.6 routing service gate (2026-06-19)

| ID          | Item                                              | Evidence                                                                               |
| ----------- | ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| R2.6-IMPL-1 | `SourceCapabilityRegistry` production enforcement | `backend/app/datasources/capability_registry.py` + `tests/test_source_capabilities.py` |
| R2.6-IMPL-2 | Adapter domain alignment                          | adapter `supported_domains` + batch_b fixture + capability tests                       |
| R2.6-IMPL-3 | `SourceRoutePlanner` + persistence                | `route_planner.py` + `job_event_log` ROUTE_PLAN payload                                |
| R2.6-IMPL-4 | `DataSourceService` fetch facade                  | `service.py` + `tests/test_datasource_service.py`                                      |
| R2.6-IMPL-5 | Sync runner service-based fetch path              | `runners.py` fetch_callable + orchestrator `datasource_service`                        |
| R2.6-IMPL-7 | Prod-equivalent scale benchmark                   | `scripts/production_equivalent_smoke.py --use-service-path`                            |

---

## DEFERRED — Round 3 (modeling + ops repay)

Does **not** block 017 per `ROUND2_GAPS` §6; **must** be closed or re-deferred with new ID before Round 4.

| ID           | Item                                                                 | Resolution phase                                      | Task hook                                           | Blocks 017? | Closure test / evidence                                               |
| ------------ | -------------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------- | ----------- | --------------------------------------------------------------------- |
| R3-PARTIAL-1 | Backfill skips validator + clean write                               | **Round 3 early** (first ops Trellis after 017 green) | `DECISIONS.md` §11 · `orchestrator.run_backfill`    | No          | Doc ADR **or** `run_backfill` post-shard validate+write path + pytest |
| R3-PARTIAL-3 | `run_reconcile` no re-fetch/compare                                  | **Round 3 mid** (after 017–019)                       | D2-P2-2 · task **014** extension                    | No          | Reconcile job re-fetch pytest                                         |
| R3-PARTIAL-4 | `manual_review_queue` after failed reconcile vs instant severe queue | **Round 3 mid** (conflict UX)                         | **016** / **023** evidence chain                    | No          | Documented UX ADR + pytest for chosen path                            |
| R3-PARTIAL-5 | COMPLETED vs write non-atomic (crash window)                         | **Round 3 ops optional**                              | `BATCH_D_STATUS` D-A2-3                             | No          | Optional same-tx COMPLETED or runbook                                 |
| D2-P1-1      | `run_revision_audit` / `run_data_quality` runners                    | **Round 3 late** (post 021)                           | Orchestrator job matrix                             | No          | Job type pytest each                                                  |
| D2-P1-3      | `python -m quant_monitor.sync` production CLI                        | **Round 3 ops** (packaging)                           | **035** prep · `scripts/sync_registry.py` successor | No          | CLI smoke + doc in `verification_commands.md`                         |
| D2-P2-1      | `source_health_snapshot` table                                       | **Round 3 mid**                                       | New migration + ops                                 | No          | Table + snapshot pytest                                               |
| D2-P2-2      | Full reconcile re-fetch (alias)                                      | _(see R3-PARTIAL-3)_                                  | —                                                   | No          | —                                                                     |
| R2-GAP-1     | `init_db.py` does not auto `sync_to_db`                              | **Round 3 ops**                                       | **035** / packaging                                 | No          | `init_db --sync-registry` flag or documented one-liner in CI          |
| D2-P3-1      | `registry_generation` / `removed_from_yaml_at` columns               | **Round 3 late**                                      | migration 009+                                      | No          | Migration + sync pytest                                               |
| D7-P1-1      | Orchestrator full handler registry                                   | **Round 3 hygiene** (post 019)                        | `sync/pipeline.py` split                            | No          | Handler registry pytest                                               |
| D7-P2-2      | `sys.path.insert` in scripts                                         | **Round 3 packaging**                                 | **035**                                             | No          | `pip install -e .` + console_scripts                                  |
| D3-P1-2      | C901 on `_validate_domain_roles` / `_execute_write`                  | **Round 3 hygiene**                                   | refactor task                                       | No          | ruff C901 clean or noqa with ADR                                      |
| A9-P1-01     | `fetch_log` / `source_registry` DB CHECK                             | **Round 3 migration 008**                             | `docs/schema/MIGRATION_008_PLAN.md`                 | No          | migration 008 applied + contract test                                 |
| A9-P2-01     | `manual_review_queue` CHECK                                          | **Round 3 migration 008**                             | same                                                | No          | same                                                                  |
| A9-P2-02     | `source_conflict.reconcile_status` CHECK                             | **Round 3 migration 008**                             | same                                                | No          | same                                                                  |
| A9-P3-01     | Migration rebuild `INSERT SELECT *` risk                             | **Round 3 migration 008**                             | explicit column list in 008                         | No          | 008 review sign-off                                                   |
| R2-RISK-1    | Orchestrator aggregation coupling                                    | **Round 3 hygiene**                                   | D7-P1-1                                             | No          | Handler extraction merged                                             |
| R2-RISK-2    | Adapters depend on storage concrete classes                          | **Round 3 mid**                                       | `evidence_ports.py`                                 | No          | Port injection on one adapter                                         |
| R2-RISK-3    | `WriteRequest` < full write_contract                                 | **Round 3 late / Round 5**                            | write_contract                                      | No          | Contract matrix doc                                                   |
| R2-RISK-4    | App-layer CHECK for some status columns                              | **By design** (C-C2)                                  | —                                                   | No          | ADR in `MIGRATION_COVERAGE.md`; migration 008 for agreed subset       |
| R2-HYG-4     | Test inter-call smell (`test_duckdb_connection`)                     | **Round 3 hygiene**                                   | optional                                            | No          | Refactor or close as wont-fix ADR                                     |
| R2-HYG-5     | Adapter metadata fields not exposed                                  | **Round 3 late**                                      | B-P2-1                                              | No          | Skeleton metadata pytest                                              |

---

## DEFERRED — Round 4 (API / frontend / notifications)

| ID            | Item                                                                                 | Resolution phase | Task hook         | Blocks 017? | Closure test / evidence                          |
| ------------- | ------------------------------------------------------------------------------------ | ---------------- | ----------------- | ----------- | ------------------------------------------------ |
| R2-GAP-2      | No source capability list HTTP API                                                   | **Round 4**      | task **024**      | No          | `GET /api/sources` or documented deferral to 025 |
| R4-API-SEC-3  | `test_pageSizeAboveAbsoluteLimit_returnsQueryTooLarge`                               | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-4  | `test_pageSizeContract_matchesDocs`                                                  | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-5  | `test_frontendPageContracts_doNotUseStale500Limit`                                   | **Round 4**      | **024** + **027** | No          | frontend + API contract test                     |
| R4-API-SEC-6  | `test_unauthenticatedRequest_returnsAuthRequired`                                    | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-7  | `test_prodWithoutToken_failsStartup`                                                 | **Round 4**      | **024**           | No          | startup pytest                                   |
| R4-API-SEC-8  | `test_prodDisabledAuth_failsStartup`                                                 | **Round 4**      | **024**           | No          | startup pytest                                   |
| R4-API-SEC-9  | `test_devDisabledAuthOnlyAllowedOnLoopback`                                          | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-10 | `test_pageSizeAboveLimit_returnsQueryTooLarge`                                       | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-11 | `test_singleLocalToken_mapsToAdmin`                                                  | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-12 | `test_deferredRolesNotEnabledInPhase1` / `test_viewerAgentRoles_areDeferredInPhase1` | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-API-SEC-13 | `test_prodAdminMutationWithoutToken_returnsAuthRequired`                             | **Round 4**      | **024**           | No          | HTTP pytest                                      |
| R4-NOTIF-1    | `test_phase1NotificationThrottle_excludesDesktop`                                    | **Round 4**      | **028**           | No          | `test_notifications.py`                          |
| R4-NOTIF-2    | `test_notificationModule_containsNoActiveDesktopThrottleInPhase1`                    | **Round 4**      | **028**           | No          | module scan test                                 |
| R4-NOTIF-3    | `test_notificationDedupKey_isStable`                                                 | **Round 4**      | **028**           | No          | unit pytest                                      |
| R4-FE-2       | Notification Center `/notifications` page                                            | **Round 4**      | **026** + **028** | No          | frontend route + e2e smoke                       |
| R4-FE-3       | Layer 1–5 dashboard pages                                                            | **Round 4**      | **027**           | No          | page contract snapshots                          |

---

## DEFERRED — Round 5+

| ID        | Item                        | Resolution phase | Task hook           | Blocks 017? | Closure test / evidence |
| --------- | --------------------------- | ---------------- | ------------------- | ----------- | ----------------------- |
| R2-RISK-5 | gitleaks / full security CI | **Round 5**      | **035** integration | No          | CI job green            |

---

## RESOLVED (reference)

| ID                        | Item                                                                | Closed                    | Evidence                                                                                                                                                                                                                                                                      |
| ------------------------- | ------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R2.5-1..5                 | Repair-package Round 2 contract drift                               | 2026-06-19                | `ROUND2_REPAIR_ALIGNMENT_TRACKER.md`                                                                                                                                                                                                                                          |
| R2.5-6                    | Domain schedulable before domain_allowed (DISABLED_SOURCE priority) | 2026-06-19                | `base_adapter.py` · `test_fetch_disabledDomain_returnsDisabledSourceBeforeDomainAllowed`                                                                                                                                                                                      |
| PROC-R2.5-1               | Round 2.5 merge + Trellis handoff                                   | 2026-06-19                | PR #15 → `7ce283a` on `master`                                                                                                                                                                                                                                                |
| R4-API-SEC-1              | `test_apiSecurityContract_isSingleAuthorityForQueryBudget`          | R2.5                      | `test_api_security_contract.py`                                                                                                                                                                                                                                               |
| R4-API-SEC-2              | `test_resourceLimitsApiLimits_matchApiSecurityContract`             | R2.5                      | same                                                                                                                                                                                                                                                                          |
| D4-P3-1                   | Starlette/httpx deprecation warning                                 | PR #11                    | `httpx2` dev dep                                                                                                                                                                                                                                                              |
| R2-HYG-2                  | Windows pytest temp                                                 | `pyproject.toml` basetemp | D1-P3-1                                                                                                                                                                                                                                                                       |
| D3-P3-1                   | Five vendor skeleton adapter classes                                | Round 2 Batch B           | `test_adapter_skeletons.py`                                                                                                                                                                                                                                                   |
| D5-P1-2                   | Manifest protocol uses archived Trellis                             | by design                 | frozen Batch D archive                                                                                                                                                                                                                                                        |
| D1-P3-2                   | GitNexus tooling                                                    | setup                     | `node .gitnexus/run.cjs analyze`                                                                                                                                                                                                                                              |
| R2.6-B1                   | Round2.6 Phase B contract gate tests (016A–016E contracts)          | 2026-06-19                | `tests/test_source_capabilities.py` · `tests/test_source_route_planner.py` · `tests/test_datasource_service.py` · `tests/test_module_boundaries.py` · `tests/test_data_cli_contract.py` · `tests/test_dependency_extras_contract.py` · `tests/test_platform_source_matrix.py` |
| R2.6-B2                   | Module boundary static checker                                      | 2026-06-19                | `scripts/check_module_boundaries.py`                                                                                                                                                                                                                                          |
| R2.6-B3                   | Phase A self-check migrated to Trellis                              | 2026-06-19                | `.trellis/tasks/06-19-round2-6-routing-service-gate/research/phase-a-self-check-migrated.md`                                                                                                                                                                                  |
| R3-EARLY-DB-INSPECT-CLI   | Read-only DB inspect CLI Phase A                                    | 2026-06-20                | `backend/app/ops/db_inspector.py` · `scripts/qmd_ops.py` · `tests/test_ops_db_inspector.py`                                                                                                                                                                                   |
| DB-R3-001                 | Project data root inventory documented via inspect                  | 2026-06-20                | `.trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.3-inspect.json`                                                                                                                                                                                              |
| DB-R3-002                 | Read-only DB open + key table counts                                | 2026-06-20                | same inspect JSON + no-mutation tests                                                                                                                                                                                                                                         |
| DOC-R3-001                | Round 2.6 PASS in `ROUND3_HANDOFF.md`                               | 2026-06-20                | `docs/ROUND3_HANDOFF.md` §Round 2.6 gate                                                                                                                                                                                                                                      |
| DOC-R3-002                | Registry authority on early close plan                              | 2026-06-20                | `ROUND3_EARLY_CLOSE_PLAN.md` authority block                                                                                                                                                                                                                                  |
| R3-PARTIAL-2              | Vendor FetchPort E2E + full_load skeleton closure                   | 2026-06-20                | `tests/test_vendor_fetch_e2e.py::test_vendorFixtureFetch_e2eThroughDataSourceServicePath`; `tests/test_sync_jobs.py::test_syncJob_fullLoad_createdToPlanned_recordsEvent`                                                                                                     |
| R3-EARLY-PROD-SCALE-BENCH | Production-equivalent smoke Batch 1 evidence                        | 2026-06-20                | `.trellis/tasks/06-20-round3-batch1-early-ops/execute-evidence/8.5-smoke-output.json`                                                                                                                                                                                         |

## DEFERRED — Round 3 Batch 1 audit design acceptances (2026-06-20)

Does **not** block finish-work or 017; documented per audit A9 synthesis — must remain visible until closed or superseded.

| ID              | Item                                                              | Resolution phase            | Task hook                        | Blocks 017? | Closure test / evidence                                              |
| --------------- | ----------------------------------------------------------------- | --------------------------- | -------------------------------- | ----------- | -------------------------------------------------------------------- |
| R3-AUDIT-DEF-01 | `KEY_TABLES` / `DEFERRED_ITEM_MAPPING` YAML SSOT vs static tuples | **Round 3 ops hygiene**     | `ops_db_inspect_contract.yaml`   | No          | Contract-driven load + drift test                                    |
| R3-AUDIT-DEF-02 | AC-E2E-1 live vendor soak beyond fixture/skeleton                 | **User-authorized staging** | cross-ref `R2.6-IMPL-8`          | No          | Authorized staging E2E with real vendor fetch                        |
| R3-AUDIT-DEF-03 | Per-subdir scan limit tests (`parquet`/`audit`/`report`)          | **Round 3 ops hygiene**     | `tests/test_ops_db_inspector.py` | No          | Parametrized subdir cap tests or contract documents shared code path |

---

## Verification baseline

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
cd frontend && npm run typecheck && npm run test
```

**Round 3 entry (017):** registry has **no OPEN rows**; all other items DEFERRED with phase or RESOLVED.

---
