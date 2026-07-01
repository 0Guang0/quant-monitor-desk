# Module Completion Rating

> **Purpose:** operator-facing status snapshot for planning and audit only.  
> **Not a design authority:** design documents, architecture documents, contracts, and rule definitions describe the desired complete product shape. They should not be downgraded with implementation-status labels.  
> **Planning authority:** execution plans and task cards must use this file to avoid claiming a module is complete when only scaffold, staged fixture, or sandbox evidence exists.  
> **Reference adoption:** rating movements for R3FR batches must also satisfy `specs/contracts/reference_adoption_guardrails.yaml` (`license_gate`, max three batches per module).  
> **Machine index:** `specs/context/authority_graph.yaml`（v2，`module_ids` + `rating_index`）· `docs/generated/project_map.generated.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.6 · §8.  
> **Last reconciled:** 2026-07-01（§3 Pass D — Wave 1–3 CLOSED @ `893e6e2b`）；**2026-06-29b** 增补 `specs/` 全量 + `docs/` 交叉核对仍有效。

---

## 1. Rating scale

| Level                               | Meaning                                                                                                                                                           | Can be called complete?         |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `R0_NOT_STARTED`                    | No meaningful runtime implementation beyond placeholder files or planning docs.                                                                                   | No                              |
| `R1_SCAFFOLD`                       | API/module skeleton, contracts, or placeholders exist but no useful executable vertical slice.                                                                    | No                              |
| `R2_MINIMAL_VERTICAL_SLICE`         | A bounded end-to-end slice works with tests, real module boundaries, and no fake success claims. This is the minimum acceptable first implementation batch.       | No, only minimal slice complete |
| `R3_STAGED_FIXTURE_CLOSED`          | The module runs against staged fixtures with validation, lineage/evidence, and negative tests.                                                                    | No, staged implementation only  |
| `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | The module runs against bounded sandbox real-data/evidence or sandbox clean-write rehearsal with explicit caps.                                                   | No, sandbox only                |
| `R5_LIMITED_PRODUCTION_ENTRY`       | Explicitly approved, capped production entry exists with before/after proof, rollback, and regression tests.                                                      | Production-limited only         |
| `R6_FULL_PRODUCTION_STABLE`         | Stable production path, complete target-domain behavior, operational runbooks, monitoring, regression suite, and no open blocker for the module's promised scope. | Yes                             |

---

## 2. Anti-overengineering completion rule

For every module or major feature after this file lands:

1. The **first implementation batch** must deliver at least `R2_MINIMAL_VERTICAL_SLICE`; a pure shell, placeholder, single-field guard, or isolated registry note is not enough.
2. The module must reach `R6_FULL_PRODUCTION_STABLE` in **no more than three implementation batches** for the declared scope.
3. Existing partially implemented modules must use their **next implementation batch** to close the main promised scope directly, unless a written ADR proves that the promise was too broad and narrows the module boundary.
4. Future task cards must distinguish:
   - first vertical slice;
   - production-complete closure;
   - hardening/regression closure.
5. Repeated micro-slices such as “add one metric”, “add one flag”, “add one registry note”, or “add one narrow test” without moving the module to the next rating level are treated as overengineering unless they are part of the same batch PR.
6. Every task card must cite **`Module ID`** from §3 and the intended rating movement (e.g. `R3 → R4`).

**Batch column (`批/3`):** implementation batches already spent toward `R6` for the **declared module scope** (not Trellis task count).

---

## 3. Canonical module inventory

`docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` remains a coverage map only — **not** a work order. 通俗说：**地图不是工单；任务卡才是工单。**

### 3.A Platform foundation

| ID  | Module                                   | Design authority                                                                                   | Rating                      | 批/3 | Close round | Evidence (2026-07-01)                                                                          | Required next movement                                                         |
| --- | ---------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------- | ---- | ----------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| A1  | Project scaffold / config / test harness | `GLOBAL_TESTING_POLICY.md`, `tests/test_catalog.yaml`                                              | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R5          | pytest catalog, config templates, loop_maintain gates                                          | Batch05 release packaging + test-catalog consistency only.                     |
| A2  | DuckDB schema / migration foundation     | `db_platform`, `docs/schema/MIGRATION_COVERAGE.md`                                                 | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R5          | migrations 001–014, `test_schema_migration.py`, `test_migration_coverage.py`                   | Batch05 migration hygiene + drift gate; no endless DDL slices.                 |
| A3  | Storage / evidence primitives            | `core_platform`, `docs/modules/local_file_system.md`                                               | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R3→R5       | **R3H-08 CLOSED** @ 2026-06-29: live fetch evidence on product path; `test_raw_store.py`       | R3-DCP-10 (G5) + R3H-05: schema_hash/content_hash bind; Batch05 lineage audit. |
| A4  | ResourceGuard / performance budget       | `core_platform`, `docs/ops/performance_limits.md`                                                  | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R3→R5       | **R3H-08 CLOSED** @ 2026-06-29: caps on live adapter/sync/API paths; `resource_guard.py` tests | R3-DCP-06 五轴 + Batch05: prove caps on every remaining smoke path.            |
| A5  | Snapshot lineage kernel                  | `core_platform`, `snapshot_lineage_contract.yaml`                                                  | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R4→R5       | `backend/app/core/snapshot_lineage.py`, `test_snapshot_lineage_kernel.py`                      | Bind to Layer snapshot builders + Batch05 regression.                          |
| A6  | Spec migrator (offline registry tool)    | `spec_migrator_contract.yaml`                                                                      | `R1_SCAFFOLD`               | 0/3  | Batch6→R5   | contract defines dry-run migrator; **`tests/test_spec_migrator.py` 未实现**                    | Batch6 hygiene or ADR-wont-fix; runtime loaders stay strict.                   |
| A7  | Platform matrix + dependency extras      | `platform_source_matrix.yaml`, `dependency_extras_contract.yaml`, `06_deployment_and_local_ops.md` | `R2_MINIMAL_VERTICAL_SLICE` | 1/3  | R5          | `test_dependency_extras_contract.py`; deployment matrix in architecture doc                    | Batch05: optional extras + platform posture in release manifest.               |

### 3.B Validation and write path

| ID  | Module                          | Design authority                                | Rating                              | 批/3 | Close round | Evidence                                                                                                | Required next movement                                                                   |
| --- | ------------------------------- | ----------------------------------------------- | ----------------------------------- | ---- | ----------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| B1  | WriteManager + DbValidationGate | `validators`, `docs/modules/write_manager.md`   | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R5       | `write_manager.py` upsert_by_pk + three-domain clean @ R3H-06; transaction gate tests; R3G promote path | Batch 3: main-DB posture + Batch05 integration smoke; **not** silent full-history write. |
| B2  | Data quality validator          | `validators`, `data_quality_rules.yaml`         | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3→R5       | **R3H-08 CLOSED** @ 2026-06-29: profiles on live paths; `market_bar_p0` + DCP-03 inspect                | R3H-05: per-source/domain profile posture before PASS claims.                            |
| B3  | Source conflict validator       | `validators`, `data_validation_and_conflict.md` | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3          | **R3H-08 CLOSED** @ 2026-06-29: live conflict outcomes; `source_conflict.py` + manual_review_queue      | R3H-05: reconcile outcomes per ready source before PASS.                                 |

### 3.C Data sources and routing

| ID  | Module                                       | Design authority                                                       | Rating                              | 批/3 | Close round | Evidence                                                                                                   | Required next movement                                                |
| --- | -------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------- | ---- | ----------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| C1  | Source registry / capability / route planner | `datasources`, `source_route_plan.md`, `source_capability_registry.md` | `R3_STAGED_FIXTURE_CLOSED`          | 2/3  | R3          | `source_registry.yaml`, route/capability tests, R3H-01～04 registry reconcile                              | R3H-05: 25-row final posture; no orphan registry rows.                |
| C2  | DataSourceService facade                     | `datasources`, `datasource_service.md`                                 | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R4       | **R3H-10 CLOSED** @ 2026-06-29: SSOT contract; no bypass on sync/API paths; `test_datasource_service.py`   | R3H-05 registry posture; Wave 4 DCP-05 incremental on Tier A sources. |
| C3  | Vendor adapters / provider fetch ports       | `datasources`, `data_sources.md`, `fetch_ports/*` (29 port modules)    | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R4       | **R3H-08 CLOSED** @ 2026-06-29: 24源 env-gated live→Tier A/B/C; **R3-DCP-01/02** baostock+fred incremental | Wave 4 **R3-DCP-05**: Tier A watermark 扩展；R3H-05 终态审计。        |
| C4  | Provider catalog / auth-license gate         | `provider_catalog.yaml`, `license_gate.py`                             | `R2_MINIMAL_VERTICAL_SLICE`         | 2/3  | R3→R5       | R3FR-05 provider catalog tests @ `6c1a0d37`                                                                | R3H-05: per-source license/auth/resource posture in release manifest. |

### 3.D Sync, scheduling, and task reliability

| ID  | Module                         | Design authority                                             | Rating                              | 批/3 | Close round | Evidence                                                                                                      | Required next movement                                                                                                |
| --- | ------------------------------ | ------------------------------------------------------------ | ----------------------------------- | ---- | ----------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| D1  | Data sync orchestration        | `sync_orchestrator`, `data_sync_orchestrator.md`             | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R5       | **R3-DCP-01/02 CLOSED** @ 2026-06-30: baostock+fred watermark incremental; `watermark.py`, orchestrator tests | Wave 4 **R3-DCP-05** Tier A 扩展 + **R3-DCP-09** 有界 backfill；Batch6: FullLoad/idempotency edge.                    |
| D2  | Task idempotency / retry / DLQ | `docs/ops/idempotency_retry_dlq_policy.md`                   | `R1_SCAFFOLD`                       | 0/3  | Batch6      | Policy doc only; **no** `idempotency_key` runtime in `backend/`                                               | Batch6: store/replay idempotency_key; do not block Round4 if write-level upsert suffices for PASS.                    |
| D3  | Sync scheduler / cron product  | `data_sync_orchestrator.md` §CLI examples                    | `R0_NOT_STARTED`                    | 0/3  | R4→R5       | Design CLI (`quant_monitor.sync`); `run_full_load` deferred; **no** production cron module                    | R3: minimal manual/CLI trigger (D1); R4+: scheduler shell calling same entrypoint — **no new fetch logic in Round4**. |
| D4  | Source health snapshot writer  | `ADR-024`, `data_sources.md` §5.8, `source_health_writer.py` | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3  | Batch6      | isolated-test DDL writer + `test_source_health_snapshot.py`; **no** production migration (D2-P2-1)            | Batch6 + B3F-MIG: merge migration SQL; DH2 path must stay snapshot-free.                                              |

### 3.E Ops, CLI, and sandbox entry

| ID  | Module                                                       | Design authority                                                | Rating                              | 批/3 | Close round | Evidence                                                                                                     | Required next movement                                                                   |
| --- | ------------------------------------------------------------ | --------------------------------------------------------------- | ----------------------------------- | ---- | ----------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| E1  | `qmd data` CLI (health / route / sync-plan / init / promote) | `ops`, `docs/ops/data_health_cli.md`                            | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R5       | **R3-DCP-01/02 CLOSED**: `sync_baostock_incremental`, `_sync_fred_macro_incremental`; `test_qmd_data_cli.py` | Wave 4 DCP-05 Tier A incremental CLI；Batch05 operator packaging.                        |
| E2  | Ops DB inspect + verification matrix                         | `ops`, `docs/ops/db_inspect_cli.md`                             | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R5       | **R3-DCP-03 CLOSED** @ `eff49343`: post-write row count / max(trade_date) / `market_bar_p0` smoke            | Wave 4: replicate inspect pattern for Tier A tables after DCP-05.                        |
| E3  | Production gate + equivalent smoke scripts                   | `ops`, `scripts/production_gate.py`                             | `R2_MINIMAL_VERTICAL_SLICE`         | 1/3  | R5          | `test_production_gate.py`, `production_equivalent_smoke.py`                                                  | Batch05 integration smoke owner; expand only with bounded budgets.                       |
| E4  | Live / staged pilot runners                                  | `ops`, `production_live_pilot_policy.md`                        | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3          | **R3H-08 CLOSED**: `ProductLiveGate` + tier routing; pilot scripts = audit input only                        | R3H-05 convergence; no new pilot feature batches.                                        |
| E5  | Sandbox clean write / limited production entry               | `ops/sandbox_clean_write`, R3G task archive                     | `R5_LIMITED_PRODUCTION_ENTRY`       | 3/3  | R5 confirm  | R3G-01/02/03 @ `23429ad8`; promote quadruple-lock; R3H-06 clean routing                                      | Batch05 release manifest records write posture; no new feature batches unless scope ADR. |
| E6  | Backup / recovery / disk thresholds                          | `docs/modules/ops_and_performance.md`, `backup_and_recovery.md` | `R1_SCAFFOLD`                       | 1/3  | R5          | `performance_limits.md` thresholds documented; partial cache/tmp paths; **no** automated backup runner       | Batch05: backup runbook + optional smoke; not a Round3 blocker.                          |
| E7  | Ops report CLI                                               | `docs/ops/ops_report_cli.md`                                    | `R0_NOT_STARTED`                    | 0/3  | R4→R5       | Design only                                                                                                  | Implement with B04_04 notification/report runtime or defer with ADR.                     |

### 3.F Data health (operator profiles)

| ID  | Module             | Design authority                            | Rating                              | 批/3 | Close round | Evidence                                                                                     | Required next movement                                                      |
| --- | ------------------ | ------------------------------------------- | ----------------------------------- | ---- | ----------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| F0  | Data health engine | `ops/data_health_profiles`, EasyXT profiles | `R4_SANDBOX_REAL_DATA_OR_REHEARSAL` | 2/3  | R3→R5       | **R3-DCP-03 CLOSED**: post-incremental `market_bar_p0` profile smoke; R3H-08 admission paths | Wave 4: expand profiles for Tier A post-DCP-05; Batch05 only if ADR widens. |

### 3.G Modeling layers (Layer1–5)

| ID  | Module                     | Design authority                                   | Rating                      | 批/3 | Close round | Evidence                                                                                      | Required next movement                                                                                     |
| --- | -------------------------- | -------------------------------------------------- | --------------------------- | ---- | ----------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| G1  | Layer1 axes / regime panel | `layer1_axes`, `layer1_global_regime_panel.md`     | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R3→R4       | loader + `test_layer1_*` on **staged** fixtures; 五轴 spec（K2）齐全；**真 clean 五轴未闭合** | **Wave 4 R3-DCP-06**：五轴全绿 **R3→R4** — **PASS 硬门禁**（`PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1）。 |
| G2  | Layer2 cross-asset sensors | `layer2_sensors`, `layer2_cross_asset_sensor.md`   | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R4+         | staged fixtures, snapshot writer, `test_layer2_sensor_loader.py`                              | **Wave 4 R3-DCP-07**：一条 cross-asset 传感器绑真市况源。                                                  |
| G3  | Layer3 industry chains     | `layer3_chains`, `layer3_industry_shock_anchor.md` | `R3_STAGED_FIXTURE_CLOSED`  | 1/3  | R4+         | loader/snapshot builder; `test_layer3_loader.py`, `test_layer3_snapshot_builder.py`           | Round4 初或 ADR-narrow；**非 PASS 硬门禁**。 registries **K3**。                                           |
| G4  | Layer4 market structure    | `layer4_markets`, `layer4_market_structure.md`     | `R3_STAGED_FIXTURE_CLOSED`  | 1/3  | R4+         | **R3H-07 CLOSED** US calendar; CN_A staged fixture; `test_layer4_market_structure.py`         | **Wave 4 R3-DCP-08**：市场结构 + US 日历绑真源。                                                           |
| G5  | Layer5 evidence / security | `layer5_evidence`, `layer5_security_evidence.md`   | `R2_MINIMAL_VERTICAL_SLICE` | 2/3  | R3          | foundation validator, evidence chain, web-evidence no-clean-write tests                       | **Wave 4 R3-DCP-10**：source_fetch_id/content_hash/schema_hash 绑真源；R3H-05 审计。                       |
| G6  | Manual review staging      | `backend/app/evidence/manual_review_staging.py`    | `R3_STAGED_FIXTURE_CLOSED`  | 1/3  | R3          | **R3H-08D CLOSED**: kalshi/polymarket/web_search manual-review live bundle                    | R3H-05 audit posture only; no factual clean write.                                                         |

### 3.H ETL and cold storage

| ID  | Module                       | Design authority               | Rating        | 批/3 | Close round | Evidence                                                     | Required next movement                                                |
| --- | ---------------------------- | ------------------------------ | ------------- | ---- | ----------- | ------------------------------------------------------------ | --------------------------------------------------------------------- |
| H1  | ETL / Parquet archive bridge | `etl`, `duckdb_and_parquet.md` | `R1_SCAFFOLD` | 1/3  | Batch6→R5   | `backend/app/etl/` package stub; `test_duckdb_connection.py` | Batch6: wire sync→Parquet paths per architecture; not Round4 blocker. |

### 3.I Product surface (Round4 primary)

| ID  | Module                      | Design authority                                                              | Rating           | 批/3 | Close round | Evidence                                                                                                      | Required next movement                                                       |
| --- | --------------------------- | ----------------------------------------------------------------------------- | ---------------- | ---- | ----------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| I1  | FastAPI API backend         | `api_platform`, `fastapi_backend.md`, `openapi_contract.md`                   | `R1_SCAFFOLD`    | 0/3  | R4          | `backend/app/api/__init__.py` placeholder; `docs/api/fastapi_routes.md` route catalog                         | B04_01: first bounded read-only HTTP vertical slice (+ envelope/pagination). |
| I2  | Agent runtime + policy      | `agents`, `agent_module.md`, `agent_tool_contracts.md`, `agent_contract.yaml` | `R0_NOT_STARTED` | 0/3  | R4          | package `__init__` only; tool contract doc complete                                                           | B04_02: policy-guarded read-only tool + forbidden-tool rejection.            |
| I3  | Frontend dashboard          | `frontend_dashboard.md`                                                       | `R1_SCAFFOLD`    | 1/3  | R4          | `frontend/` Vite shell + `App.shell.test.tsx`; placeholder UI, no API binding                                 | B04_03 batch 2–3: API-bound page + states (layout user-owned).               |
| I4  | Notifications / reports     | `notifications`, `notification_and_reports.md`                                | `R0_NOT_STARTED` | 0/3  | R4          | package `__init__` only                                                                                       | B04_04: one event→report/notification_log flow.                              |
| I5  | Backtest / review runtime   | `backtest_and_review.md`, `backtest_review_lifecycle.md`                      | `R0_NOT_STARTED` | 0/3  | R4          | planning + R3FR-04 audit input                                                                                | B04_05: frozen loader, no-action guard, runner, report artifact (3 batches). |
| I6  | Backtest / review metrics   | `backtest_metric_contract.yaml`                                               | `R0_NOT_STARTED` | 0/3  | R4          | contracts only                                                                                                | **Sub-scope of I5** — not a separate completion track.                       |
| I7  | Review sandbox API          | `review_sandbox_api.md`, `review_sandbox_contract.yaml`                       | `R1_SCAFFOLD`    | 1/3  | R4          | contract + ops cross-ref; no HTTP server                                                                      | Close with B04_05/B04_01 read-only review endpoints.                         |
| I8  | Diagnostics API (read-only) | `diagnostics_api_contract.yaml`, `fastapi_backend.md` §14                     | `R1_SCAFFOLD`    | 0/3  | R4          | contract lists `/api/diagnostics/*`; **no** routes implemented; **`test_api_security_contract.py` 待 B04_01** | Implement as **subset of I1** in B04_01 (registry/route/guard snapshots).    |

### 3.J Governance, security, and deferred product modules

| ID  | Module                             | Design authority                                         | Rating                      | 批/3 | Close round | Evidence                                                                              | Required next movement                                                  |
| --- | ---------------------------------- | -------------------------------------------------------- | --------------------------- | ---- | ----------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| J1  | Reference adoption governance      | `reference_adoption_guardrails.yaml`, R3FR-01            | `R3_STAGED_FIXTURE_CLOSED`  | 2/3  | R5          | `test_reference_adoption_guardrails.py`, R3FR-07 CLOSED                               | Batch05: no runtime import from deleted reference trees.                |
| J2  | No-action semantics guard          | `agent_module.md` §6, B04 cards                          | `R1_SCAFFOLD`               | 1/3  | R4          | guardrail tests in reference_adoption; no runtime agent                               | B04_02 + B04_05: deny trading/broker semantics across API/Agent/review. |
| J3  | Release / security packaging       | Batch05 cards                                            | `R1_SCAFFOLD`               | 0/3  | R5          | planning + partial CI scripts                                                         | B05-01..03 only — not a feature backlog.                                |
| J4  | Docs / task entrypoint consistency | `MIGRATION_MAP.md`, README manifests                     | `R2_MINIMAL_VERTICAL_SLICE` | 2/3  | R5          | canonical batch folders; loose card redirects                                         | Batch05 docs consistency check + release manifest alignment.            |
| J5  | `web_search` live API (deferred)   | `R3H-WEB-SEARCH` ADR scope                               | `R3_STAGED_FIXTURE_CLOSED`  | 1/3  | Post-R4     | mock/replay port READY @ R3H-04                                                       | **DEFERRED_POST_ROUND4** — only scope ADR before Round4.                |
| J6  | Log audit / structured ops logging | `log_audit_contract.yaml`, `logs_health_audit.md`        | `R1_SCAFFOLD`               | 0/3  | R5          | contract + ops doc; **no** runtime log pipeline in `backend/`                         | Batch05 observability hardening or ADR-narrow to file-based audit only. |
| J7  | User input privacy boundary        | `user_input_privacy_contract.yaml`, `privacy_*` ops docs | `R1_SCAFFOLD`               | 0/3  | R4          | contract + `frontend_security_policy.md`; **`tests/test_privacy_contract.py` 未实现** | Close with I2/I3: local-only import + save-as-evidence disclosure.      |

### 3.K Model input governance (spec-only track)

| ID  | Module                            | Design authority                                           | Rating                     | 批/3 | Close round | Evidence                                                                            | Required next movement                                                          |
| --- | --------------------------------- | ---------------------------------------------------------- | -------------------------- | ---- | ----------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| K1  | Model input whitelist / readiness | `specs/model_inputs/**`, `model_input_readiness_matrix.md` | `R3_STAGED_FIXTURE_CLOSED` | 1/3  | R3→R4+      | YAML whitelists + `test_model_input_whitelist.py`; **spec-only — no runtime fetch** | Layer modules (G1–G5) consume rows; expand only via ADR + closure_test.         |
| K2  | Layer1 five-axis indicator specs  | `specs/layer1_axes/restructured_axes_v1_1/**`              | `R3_STAGED_FIXTURE_CLOSED` | 1/3  | R3→R4       | per-axis indicator_spec + engineering_rules（5 axes）齐全；loader 测 staged only    | **Sub-scope of G1** — **Wave 4 R3-DCP-06**：每轴真 clean 指标引擎 + pytest 绿。 |
| K3  | Layer3 chain registries           | `specs/layer3_global_industry_chains/**`                   | `R3_STAGED_FIXTURE_CLOSED` | 1/3  | R4+         | node/edge/anchor JSON+YAML registries                                               | **Sub-scope of G3** — loader uses staged bundle today.                          |

---

## 3.1 Design doc aliases (not separate completion tracks)

These `docs/modules/*.md` files are **sub-documents or compat indexes** — track completion via the parent **Module ID** above:

| Doc file                                                | Parent ID | Note                                                         |
| ------------------------------------------------------- | --------- | ------------------------------------------------------------ |
| `fastapi_and_frontend.md`                               | I1, I3    | compat index only                                            |
| `data_validation_write_concurrency.md`                  | B1–B3     | compat index only                                            |
| `source_route_plan.md`, `source_capability_registry.md` | C1        | Round2.6 split of C1                                         |
| `datasource_service.md`                                 | C2        |                                                              |
| `qmt_xtdata_adapter.md`                                 | C3        | single-source deep spec                                      |
| `backtest_review_lifecycle.md`                          | I5        | lifecycle contract for I5                                    |
| `README.md` (modules index)                             | —         | navigation only                                              |
| `docs/api/fastapi_routes.md`                            | I1, I8    | route catalog for Round4                                     |
| `docs/api/agent_tool_contracts.md`                      | I2        | agent tool surface                                           |
| `docs/architecture/05_module_map.md`                    | —         | historical module index; **superseded by §3** for completion |
| `specs/layer1_axes/restructured_axes_v1_1/**`           | K2 → G1   | per-axis specs                                               |
| `specs/layer3_global_industry_chains/**`                | K3 → G3   | chain registries                                             |
| `specs/model_inputs/*.yaml`                             | K1        | whitelist rows                                               |
| `specs/frontend/page_contracts.yaml`                    | I3        | page/data-shape contract                                     |

---

## 3.2 Coverage verification log

### Pass A — 2026-06-29（代码 + authority_graph + `docs/modules` + `docs/ops`）

（见上表 `authority_graph` / `backend/app` / `frontend/` 等行。）

### Pass D — 2026-07-01（Wave 1–3 代码闭合 @ `893e6e2b`）

| Wave / 轨  | 规划 ID        | 模块跃迁（摘要）            | 证据                                                |
| ---------- | -------------- | --------------------------- | --------------------------------------------------- |
| Wave 1     | R3H-10, R3H-07 | C2/E4, G4 → R4 边界         | archived `06-29-round3h-r3h10-*` · `r3h07-*`        |
| Wave 2     | R3H-08A–D      | C3, A3, B\*, G6 live 产品化 | archived `06-29-round3h-r3h08-live-productization`  |
| Wave 3     | R3-DCP-01..03  | D1, E1, E2, F0 → R4 边界    | `5dc71c0b` · `5d8d7b0f` · `eff49343`                |
| **未闭合** | **R3-DCP-06**  | **G1, K2 五轴真 clean**     | staged `test_layer1_*` 绿；**PASS 硬门禁待 Wave 4** |

### Pass C — 2026-06-29c（`authority_graph.yaml` v2 ↔ §3 对齐）

| Source                    | Result                                                                                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `rating_index`            | 51 Module ID（A1–A7, B1–B3, … K1–K3）→ 22 graph nodes                                                                         |
| 新增 graph 节点           | `project_scaffold`, `model_inputs`, `frontend_platform`, `source_health`, `backtest_review`, `governance`, `privacy_boundary` |
| 修复                      | `layer3_chains` / `layer4_markets` tests；补全 contracts/docs/tests                                                           |
| `generate_project_map.py` | 输出 `module_ids` + `rating_ssot`                                                                                             |

### Pass B — 2026-06-29b（`specs/` 全量 79 文件 + `docs/` 排除项后）

**扫描范围：**

- `specs/`：全部（contracts 39、registry 3、context 1、model_inputs 6、layer1_axes 20、layer3_chains 9、verification 2、frontend 1、api 1、schema 1）
- `docs/`：**含** `architecture/` 14、`modules/` 26、`ops/` 28、`api/` 2、`adr/` 6、`decisions/` 5、`quality/` 59、`schema/` 2、`generated/` 3
- **排除：** `implementation_tasks/`、`UNRESOLVED_ISSUES_REGISTRY.md`、`AUDIT_DEFERRED_REGISTRY.md`、`DEVELOPER_GUIDE.md`、`INDEX.md`、`OPERATOR_GUIDE.md`、`RESEARCHER_GUIDE.md`、`RESOLVED_ISSUES_REGISTRY.md`、`ROUND3_HANDOFF.md`、`START_HERE.md`

| Source                                                | Result                                                                                                                                                                                                            |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `specs/contracts/*.yaml` + `data_adapter_contract.md` | 全部 39 契约已映射；**本次新增行：** A6 `spec_migrator`、A7 `dependency_extras`、D4 `source_health`、I8 `diagnostics_api`、J7 `user_input_privacy`                                                                |
| `specs/model_inputs/**`                               | → **K1**（与 G1–G5 消费关系）                                                                                                                                                                                     |
| `specs/layer1_axes/**`                                | → **K2** ⊂ **G1**                                                                                                                                                                                                 |
| `specs/layer3_global_industry_chains/**`              | → **K3** ⊂ **G3**                                                                                                                                                                                                 |
| `specs/datasource_registry/**`                        | → **C1** + **C4**                                                                                                                                                                                                 |
| `specs/verification/*`                                | 验收矩阵 → 各模块 AC 引用（非独立模块）                                                                                                                                                                           |
| `docs/architecture/*`                                 | 架构叙事；**05_module_map** 仅历史索引；边界 → **J1** `module_boundary_contract`                                                                                                                                  |
| `docs/adr/*` + `docs/decisions/*`                     | 决策记录；**ADR-024** → **D4**；其余为横切约束不单列模块                                                                                                                                                          |
| `docs/api/*`                                          | → **I1** / **I2**                                                                                                                                                                                                 |
| `docs/quality/*`                                      | 审计/协调产物；**model_input_readiness_matrix.md** → **K1**；**production_live_pilot_policy** → **E4**；gate 文档（如 `BATCH3_STAGED_DOWNSTREAM_GATE`）→ 策略非模块                                               |
| `docs/ops/*`（28 文件）                               | 已映射；**未单列模块的 ops doc → 父模块：** `lock_and_concurrency_policy`→B1；`incident_playbook`/`daily_weekly_monthly_checklist`→E6；`layer3_config_health_check`→G3；`config_secret_policy`→J3；`privacy_*`→J7 |
| `docs/schema/*`                                       | → **A2** migration 计划                                                                                                                                                                                           |
| `docs/generated/*`                                    | 生成索引；`docs_specs_index` 仍含已排除 guide 路径（生成器预期行为）                                                                                                                                              |
| **契约要求但测试缺失**                                | `test_spec_migrator.py`、`test_privacy_contract.py`、`test_api_security_contract.py`（diagnostics 部分）— 已标 **R1** 且记入对应模块                                                                              |
| `backend/app/ops/source_health_writer.py`             | 原遗漏 → **D4**                                                                                                                                                                                                   |

**Intentionally not promoted to standalone modules** (track under parent or Batch6):

- Per-source adapter one-pagers beyond `qmt_xtdata_adapter.md` → C3
- Individual migration files → A2
- Trellis / GitNexus tooling → out of product module rating
- Frontend visual design → user-owned; I3 tracks API binding only
- `docs/quality/audit_evidence/**` → 审计证据归档，非产品模块
- Architecture phase plan (`09_phase_plan.md`) → 历史阶段叙事，执行以根目录 `PROJECT_IMPLEMENTATION_ROADMAP.md` 为准

---

## 3.3 Known stale artifacts to fix elsewhere (not rating SSOT)

| Artifact                                          | Issue                                                                          |
| ------------------------------------------------- | ------------------------------------------------------------------------------ |
| `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` §3 | Still says R3G must prove WriteManager — **R3G CLOSED**; use §3 **B1/E5** here |
| `R3H_PASS_EXECUTION_PLAN.md` §3 wave diagram      | R3H-06 still shown blocking — **CLOSED** @ 2026-06-29                          |
| `project_map.generated.md`                        | Regenerate via `loop_maintain.py --fix` after authority_graph v2               |

---

## 4. Planning consequences

- Design/contract files remain complete-product targets.
- Task cards must state **Module ID** (§3) and which rating movement they deliver.
- A batch that does not move the module at least one rating level must explain why it is a hardening/regression batch, not a feature batch.
- No module may require more than three implementation batches to reach the complete stable shape for the declared scope.
- **Round3 data-plane group** (Wave 1–3 **CLOSED** @ 2026-06-30): sync/live/incremental/inspect — see `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.7. **Remaining PASS blockers:** **Wave 4** `R3-DCP-05..10`（含 **G1/K2 五轴 R3-DCP-06**）+ **Wave 5** `R3H-05-GATE`.
- **Round4 product group:** **I1–I7, J2** — consume Round3 outputs read-only; do not re-implement sync/fetch/write engines.
- No module may move to `R6_FULL_PRODUCTION_STABLE` based on docs, registry rows, staged fixtures, or one sample adapter alone. The required closure is an executable vertical slice plus tests, evidence/lineage binding where applicable, ResourceGuard/security posture, and release-manifest representation. If that cannot be delivered, the correct outcome is ADR-narrowed scope plus release limitation.
