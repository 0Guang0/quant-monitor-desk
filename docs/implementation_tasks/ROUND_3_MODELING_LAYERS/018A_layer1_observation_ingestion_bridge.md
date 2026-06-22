# 018A — Round 3 Batch 2.5 Layer1 observation ingestion bridge

> Status: mandatory Round 3 bridge task after Batch 2 and before Batch 3.
>
> Scope: first controlled ingestion of Layer 1 `axis_observation` from an authorized or staged source path into the local DuckDB clean table.
>
> Protocol: this task **must** be planned as a Trellis complex task. It is not a lightweight patch and not an ad-hoc script run.
>
> Safety rule: do not start live or production-like ingestion until Phase 0 and Phase 1 gates are green and audited.

## 0. Why this bridge exists

Round 3 Batch 2 builds the Layer 1 schema, axis loader, feature engine, interpretation engine, and snapshot lineage path. It intentionally uses fixture or staged observations and explicitly does **not** implement live production fetch orchestration.

That leaves a separate gap:

```text
Layer 1 axis specs / indicator registry
  -> real or authorized source route
  -> fetch evidence
  -> raw/file/fetch_log evidence
  -> validation and conflict checks
  -> clean axis_observation write
  -> feature snapshot
  -> interpretation snapshot
  -> snapshot lineage
```

This file defines the controlled bridge for that gap. It prevents implementers from either:

1. hiding real-data ingestion inside Batch 2, or
2. delaying all real-data ingestion until Batch 6, after later modeling layers have already been built on fixture-only data.

## 1. Decision: still use Trellis complex-task protocol, with stricter gates

This batch must still follow `.trellis/spec/guides/complex-task-planning-protocol.md`.

However, because this is the first bridge from external/staged data into clean Layer 1 observation state, it has stricter handling than an ordinary modeling batch:

1. Plan must create a dedicated `.trellis/tasks/**/MASTER.plan.md` for Batch 2.5.
2. Plan must create a dedicated `AUDIT.plan.md` before Execute starts.
3. Plan must split work into the five phases in this file.
4. Execute must stop after each phase and hand off evidence for audit.
5. Audit must sign off each phase before the next phase starts.
6. No phase may be merged forward by claiming that tests are enough; the audit evidence must include source-route, DB, write-boundary, and lineage checks.
7. If any phase is incomplete, the item remains `DEFERRED` with owner, phase, task hook, and closure test.

Recommended Trellis task name:

```text
round3-batch2-5-layer1-observation-ingestion-bridge
```

## 2. Placement in Round 3

Required order:

```text
Batch 1  -> DB inspect / early real-data proof / service-path evidence
Batch 2  -> Layer 1 tables, loader, feature and interpretation snapshot engines
Batch 2.5 -> this bridge: Layer 1 observation ingestion into clean DB
Batch 3  -> Layer 2 cross-asset sensor
Batch 4  -> Layer 3 industry chain
Batch 5  -> Layer 4/5 downstream evidence
Batch 6  -> general production CLI, backfill, source health, packaging, closeout
```

Batch 2.5 must not be executed before Batch 2 has a green audit for:

- `axis_registry`
- `axis_indicator_registry`
- `axis_indicator_profile`
- `axis_observation`
- `axis_feature_snapshot`
- `axis_interpretation_snapshot`
- `axis_snapshot_lineage`
- no-future-data behavior
- Layer 1 snapshot lineage behavior

Batch 3 may start without Batch 2.5 only if the user explicitly accepts fixture-only Layer 2 planning. Otherwise Batch 2.5 should be treated as the recommended bridge before real downstream modeling.

## 3. Primary objective

Implement a narrow, auditable, local-first ingestion path that proves a small set of Layer 1 indicators can move from a declared data source into `axis_observation` and then into Layer 1 snapshots without violating any data-source, validation, write, resource, lineage, privacy, or no-action boundary.

This task is successful only if the final audit can trace:

```text
indicator_id
  -> source registry / capability declaration
  -> SourceRoutePlan
  -> FetchRequest / FetchResult
  -> raw or staged evidence
  -> file_registry and fetch_log evidence
  -> validation_report
  -> source_conflict decision or no-conflict proof
  -> WriteManager write result
  -> clean axis_observation rows
  -> axis_feature_snapshot rows
  -> axis_interpretation_snapshot rows
  -> axis_snapshot_lineage rows
```

## 4. Non-goals

This batch must not implement or enable:

- full-market ingestion
- full-history ingestion
- broad backfill
- QMT / qmt_xqshare / Yahoo live validation by default
- broker login
- order placement
- account control
- frontend UI
- FastAPI production routes
- Agent writes
- Layer 2, Layer 3, Layer 4, or Layer 5 ingestion
- `source_health_snapshot` write path
- general-purpose production `qmd data` CLI completion
- migration 008 CHECK-constraint closeout, unless the planned phase explicitly narrows and audits it
- any silent fallback path

Batch 6 remains responsible for broad production CLI, full-load/backfill/data-quality runners, source-health snapshots, packaging, and final closeout.

## 5. Required Plan-stage source context

Plan must read every item in this section and summarize it in `MASTER.plan.md` Source Context Index. If Plan decides that a source is not needed at Execute time, it must state why.

### 5.1 Root and protocol sources

| Source                                                   | Type             | Required use                                                                                               |
| -------------------------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `README.md`                                              | root boundary    | Three-layer context model; docs/specs are not implementation paths; old source-role model must not return. |
| `MIGRATION_MAP.md`                                       | project map      | Locate design docs, contracts, implementation directories, and DB/data-source boundaries.                  |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`                     | Round3 batch map | Confirm Batch 2.5 placement between Batch 2 and Batch 3.                                                   |
| `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`  | context bridge   | Preserve Plan -> Execute -> Audit trace discipline.                                                        |
| `.trellis/spec/guides/complex-task-planning-protocol.md` | Trellis protocol | MASTER/AUDIT/REPAIR/manifest rules.                                                                        |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`    | rule             | No WriteManager bypass; no silent fallback; no docs/specs implementation paths.                            |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`     | rule             | Semantic assertions required; call-only tests are insufficient.                                            |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`    | rule             | Eco-mode, no full-market/full-history default scans.                                                       |
| `docs/quality/staged_acceptance_policy.md`               | rule             | Partial delivery and stage-appropriate acceptance.                                                         |
| `docs/quality/PENDING_USER_DECISIONS.md`                 | user decisions   | Do not reopen confirmed decisions, especially source-role and runtime decisions.                           |

### 5.2 Architecture and module design sources

| Source                                                                      | Required use                                                                                                    |
| --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `docs/architecture/03_runtime_flows.md`                                     | Runtime chain: ResourceGuard -> fetch -> raw/staging -> validation -> conflict -> WriteManager -> snapshot.     |
| `docs/architecture/04_data_architecture.md`                                 | Data zones, raw/parquet/file_registry, clean tables, and Layer 1 observation/snapshot data placement.           |
| `docs/architecture/module_boundary_matrix.md`                               | Data source module may provide raw/staging/fetch_log; clean writes must not come directly from source module.   |
| `docs/modules/layer1_global_regime_panel.md`                                | Layer 1 data flow, `axis_observation`, feature snapshot, interpretation snapshot, FORBIDDEN/BlindSpot behavior. |
| `docs/modules/data_sources.md`                                              | Source roles, adapter behavior, fetch evidence, source_metric_observation context if relevant.                  |
| `docs/modules/source_capability_registry.md`                                | Capability gate before fetch.                                                                                   |
| `docs/modules/source_route_plan.md`                                         | Explicit routing and no silent fallback.                                                                        |
| `docs/modules/datasource_service.md`                                        | Production fetch facade; only DataSourceService calls adapter factory.                                          |
| `docs/modules/data_sync_orchestrator.md`                                    | Orchestrator runner relationship to DataSourceService/fetch callable/job events.                                |
| `docs/modules/data_validation_and_conflict.md`                              | DataQualityValidator and SourceConflictValidator semantics.                                                     |
| `docs/modules/write_manager.md`                                             | Clean write boundary and WriteManager responsibilities.                                                         |
| `docs/modules/duckdb_and_parquet.md`                                        | DuckDB/parquet storage design and clean/staging/raw split.                                                      |
| `docs/modules/local_file_system.md`                                         | `data/raw`, `data/parquet`, `data/audit`, `data/reports`, and local-first file boundaries.                      |
| `docs/ops/data_sync_quick_reference.md`                                     | Safe user-facing data sync behavior, dry-run, route-preview, no auto-enable QMT/xqshare.                        |
| `docs/ops/data_sync_command_matrix.md`                                      | Command matrix and default write behavior.                                                                      |
| `docs/ops/db_inspect_cli.md`                                                | Read-only DB/data-root inspection pre/post evidence.                                                            |
| `docs/ops/qmt_xqshare_setup.md`                                             | Optional source authorization boundary.                                                                         |
| `docs/ops/privacy_data_flow.md`                                             | Local-only privacy and data-flow rules.                                                                         |
| `docs/ops/performance_limits.md`                                            | Resource and performance ceilings.                                                                              |
| `docs/ops/lock_and_concurrency_policy.md`                                   | DB lock/write concurrency concerns.                                                                             |
| `docs/decisions/ADR-001-ingestion-validation-write-transaction-boundary.md` | Validation/write transaction boundary and `COMPLETED` semantics.                                                |
| `docs/decisions/ADR-002-db-check-vs-app-validation.md`                      | DB CHECK vs app-layer validation split.                                                                         |
| `docs/adr/ADR-0001-use-duckdb-local-first.md`                               | DuckDB local-first and single-writer/multi-reader rule.                                                         |
| `docs/adr/ADR-0003-layer1-standardization-only.md`                          | Full standardization belongs to Layer 1 only.                                                                   |

### 5.3 Contract, schema, registry, and definition sources

| Source                                                     | Required use                                                              |
| ---------------------------------------------------------- | ------------------------------------------------------------------------- |
| `specs/schema/schema.sql`                                  | Target table definitions and schema contract expectations.                |
| `backend/app/db/migrations/004_ingestion_sources.sql`      | `source_registry` and `fetch_log` actual migration.                       |
| `backend/app/db/migrations/005_ingestion_validation.sql`   | validation/conflict/manual-review actual migration.                       |
| `backend/app/db/migrations/006_ingestion_sync.sql`         | sync job and job event actual migration.                                  |
| `backend/app/db/migrations/008_lineage_version_fields.sql` | lineage fields in validation reports.                                     |
| `backend/app/db/migrations/010_lineage_not_null.sql`       | lineage hardening constraints.                                            |
| `backend/app/db/migrations/011_layer1_tables.sql`          | Layer 1 tables actual migration.                                          |
| `specs/datasource_registry/source_registry.yaml`           | Source IDs and Primary / Validation / FallbackPolicy roles.               |
| `specs/datasource_registry/source_capabilities.yaml`       | Domain/operation capability declarations.                                 |
| `specs/contracts/source_capability_contract.yaml`          | Capability gate and auth requirements.                                    |
| `specs/contracts/source_route_contract.yaml`               | SourceRoutePlan required fields, statuses, and forbidden silent fallback. |
| `specs/contracts/datasource_service_contract.yaml`         | DataSourceService required steps and call boundaries.                     |
| `specs/contracts/data_adapter_contract.md`                 | FetchRequest/FetchResult/adapter contract.                                |
| `specs/contracts/data_cli_contract.yaml`                   | Safe CLI dry-run and route-preview behavior.                              |
| `specs/contracts/data_quality_rules.yaml`                  | Data-quality rule basis.                                                  |
| `specs/contracts/source_conflict_rules.yaml`               | Primary/validation conflict behavior.                                     |
| `specs/contracts/write_contract.yaml`                      | Required WriteRequest fields and clean write rejection rules.             |
| `specs/contracts/snapshot_lineage_contract.yaml`           | Required snapshot lineage fields and no-future-data constraints.          |
| `specs/contracts/runtime_flow_contract.yaml`               | Runtime flow sequencing and ResourceGuard checkpoints.                    |
| `specs/contracts/resource_limits.yaml`                     | Resource limits and safety thresholds.                                    |
| `specs/contracts/ops_db_inspect_contract.yaml`             | Pre/post DB inspect output requirements.                                  |
| `specs/contracts/platform_source_matrix.yaml`              | Platform/source availability and optional source constraints.             |
| `specs/contracts/reference_adoption_guardrails.yaml`       | No external reference adoption that violates project boundaries.          |

### 5.4 Original tasks and registry sources

| Source                                                                                                                           | Required use                                                                      |
| -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`                                          | Batch 2 upstream dependency.                                                      |
| `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md`                              | Batch 2 upstream dependency.                                                      |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/011_implement_source_registry.md`                                   | Source registry implementation context.                                           |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/012_implement_data_adapter_contract.md`                             | Adapter/fetch contract context.                                                   |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/013_implement_core_adapter_skeletons.md`                            | Existing adapter skeleton and test-only source context.                           |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md`                            | Orchestrator job context.                                                         |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/015_implement_data_quality_validator.md`                            | Validator context.                                                                |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/016_implement_source_conflict_validator.md`                         | Conflict validator context.                                                       |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/ROUND2_GAPS_AND_DEVIATIONS.md`                                      | Known real-data/full-load/backfill gaps.                                          |
| `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md`                                                       | Existing deferred semantics, especially backfill not writing clean unless closed. |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016A_define_source_capability_registry.md`                 | Source capability design task.                                                    |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016B_define_source_route_plan_and_datasource_service.md`   | SourceRoutePlan and DataSourceService design task.                                |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016D_define_data_sync_quick_reference_and_error_guides.md` | Safe CLI/error guide context.                                                     |
| `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/016F_define_prod_equivalent_scale_benchmark.md`            | Production-equivalent benchmark context.                                          |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                                                                                | Required open/deferred/resolved item trace.                                       |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                                                                                             | Operator-facing unresolved/deferred items.                                        |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                                                                               | Already closed items and evidence not to reopen.                                  |

### 5.5 Code reference sources Plan must inspect

Plan must inspect the actual code paths before writing MASTER. Execute must read originals only when MASTER marks them must-read.

| Path                                             | Required reason                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| `backend/app/config.py`                          | `DATA_ROOT`, default DB path, resource profile.                          |
| `backend/app/db/connection.py`                   | reader/writer semantics and read-only DB open.                           |
| `backend/app/db/write_manager.py`                | clean write path and audit behavior.                                     |
| `backend/app/db/validation_gate.py`              | validation gate behavior before clean writes.                            |
| `backend/app/core/resource_guard.py`             | ResourceGuard decisions and profiles.                                    |
| `backend/app/storage/raw_store.py`               | raw file saving.                                                         |
| `backend/app/storage/file_registry.py`           | file registry write path.                                                |
| `backend/app/storage/evidence_ports.py`          | storage port abstraction if adapter decoupling is needed.                |
| `backend/app/datasources/source_registry.py`     | source registry load/sync behavior.                                      |
| `backend/app/datasources/capability_registry.py` | capability checks.                                                       |
| `backend/app/datasources/route_planner.py`       | SourceRoutePlan implementation.                                          |
| `backend/app/datasources/route_models.py`        | route model fields.                                                      |
| `backend/app/datasources/service.py`             | DataSourceService facade.                                                |
| `backend/app/datasources/fetch_result.py`        | FetchRequest/FetchResult model.                                          |
| `backend/app/datasources/fetch_log.py`           | fetch_log write behavior.                                                |
| `backend/app/datasources/base_adapter.py`        | Base fetch template.                                                     |
| `backend/app/datasources/adapters/*.py`          | Adapter-supported domain boundaries; no direct use from Layer modules.   |
| `backend/app/sync/jobs.py`                       | Job types and statuses.                                                  |
| `backend/app/sync/orchestrator.py`               | run_incremental/backfill/reconcile behavior and gaps.                    |
| `backend/app/sync/pipeline.py`                   | validation/write pipeline.                                               |
| `backend/app/sync/runners.py`                    | service-based fetch path.                                                |
| `backend/app/validators/data_quality.py`         | validation report and lineage fields.                                    |
| `backend/app/validators/source_conflict.py`      | conflict behavior.                                                       |
| `backend/app/layer1_axes/*.py`                   | Batch 2 Layer 1 loader, feature, interpretation, lineage code.           |
| `backend/app/ops/db_inspector.py`                | pre/post DB inspect behavior.                                            |
| `scripts/qmd_ops.py`                             | transitional ops inspect command only; not the main ingestion path.      |
| `scripts/init_db.py`                             | DB initialization and migration behavior.                                |
| `scripts/production_equivalent_smoke.py`         | service-path smoke evidence; not a replacement for production ingestion. |

## 6. The five gaps this batch must address

This batch exists to close or narrow the following gaps before broader real-data use.

| Gap                                                                  | Current risk                                                                                                                        | Required Batch 2.5 treatment                                                                                                                                       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| G1: no real production data rows                                     | DB/schema exist, but fetch/job/validation/write evidence can still be empty.                                                        | Create a narrow, audited micro-ingestion path; prove row counts and evidence before/after.                                                                         |
| G2: production CLI not complete                                      | `qmd data` remains broader Batch 6 scope.                                                                                           | Do not finish full CLI here; use internal service/orchestrator path or a narrow dev command only if MASTER approves. CLI must still support dry-run if introduced. |
| G3: no Layer1 observation batch                                      | Batch 2 computes snapshots from fixture/staged observations.                                                                        | Add this explicit bridge before Batch 3.                                                                                                                           |
| G4: full_load/backfill/data_quality runners not fully productionized | Broad backfill/full-load could bypass validation/write rules or become too large.                                                   | Use only micro-ingestion/incremental-style path; broad runners stay Batch 6 unless explicitly narrowed.                                                            |
| G5: tests green does not equal production safety                     | Fixture tests do not prove live/staged source authorization, route, validation, write, lineage, and DB inventory evidence together. | Require phase-by-phase audit, DB inspect before/after, row-count assertions, and trace evidence.                                                                   |

## 7. Implementation scope

### 7.1 Allowed implementation targets

The Plan may choose names, but implementation must stay within mapped runtime/test directories.

Likely implementation targets:

| Area                                           | Candidate paths                                                                                                                    |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Layer 1 ingestion orchestration                | `backend/app/layer1_axes/ingestion.py` or `backend/app/sync/runners.py` narrow Layer1 runner                                       |
| Layer 1 observation writer                     | `backend/app/layer1_axes/observation_writer.py` if a separate writer is needed; it must call WriteManager                          |
| Data-source path reuse                         | `backend/app/datasources/service.py`, `backend/app/sync/pipeline.py`, `backend/app/sync/orchestrator.py`, only if needed           |
| Storage evidence                               | `backend/app/storage/raw_store.py`, `backend/app/storage/file_registry.py`, only if a gap is found                                 |
| Validation/conflict path                       | `backend/app/validators/data_quality.py`, `backend/app/validators/source_conflict.py`, only if a Layer1-specific rule gap is found |
| Tests                                          | `tests/test_layer1_observation_ingestion.py`, `tests/test_layer1_ingestion_gates.py`, plus existing tests below                    |
| Optional narrow CLI only if approved by MASTER | `scripts/qmd_layer1_ingest.py` or successor console script; must default to dry-run and must not replace Batch 6 CLI               |

### 7.2 Forbidden implementation targets and patterns

- Do not implement runtime code under `docs/` or `specs/`.
- Do not call `backend.app.datasources.adapters.create_adapter` from `backend.app.layer1_axes`.
- Do not import vendor adapter classes into Layer 1 modules.
- Do not write clean `axis_observation` with raw SQL outside WriteManager.
- Do not write snapshots from Agent prose.
- Do not skip DataQualityValidator.
- Do not skip SourceConflictValidator when a validation source exists or conflict rule applies.
- Do not set `source_used` after fetch; it must be traceable to SourceRoutePlan and FetchResult.
- Do not change Validation into Primary without explicit fallback quality flag and contract support.
- Do not default-enable QMT, qmt_xqshare, Yahoo, broker terminals, network live fetches, or account/login behavior.
- Do not implement broad `qmd data` production CLI here.
- Do not make tests assert only that a function was called; assert DB rows, status, route fields, evidence hashes, and lineage.

## 8. Required phase model

Each phase must have a Trellis child deliverable, acceptance criteria, evidence output, and audit sign-off. Execute must not proceed to the next phase until Audit records PASS for the current phase.

### Phase 0 — Pre-ingestion DB/design/contract gate

**Purpose:** prove the project is safe to attempt any Layer1 real/staged ingestion.

**Execute actions:**

1. Inspect all sources in Sections 5.1-5.5.
2. Produce `phase0_source_context_matrix.md` listing every design/contract/rule/code source, its relevance, and whether it is summarized or must-read original.
3. Produce `phase0_db_contract_gate.md` comparing:
   - `specs/schema/schema.sql`
   - migrations `004`-`011`
   - `write_contract.yaml`
   - `snapshot_lineage_contract.yaml`
   - `source_route_contract.yaml`
   - `datasource_service_contract.yaml`
   - `data_cli_contract.yaml`
   - actual code paths.
4. Run schema, route, data-source, DB inspect, and Layer1 tests listed below.
5. Record any mismatch as BLOCKER, DEFERRED, or OUT_OF_SCOPE with exact file and line or code path.

**Required tests / commands:**

```bash
pytest tests/test_schema_migration.py tests/test_schema_contract.py -q
pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_cli_contract.py -q
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q
```

**Required pass conditions:**

- No failing tests in the command set above.
- `axis_observation` exists in schema/migration contract after Batch 2.
- `source_registry` roles are still `Primary / Validation / FallbackPolicy`; `Shadow` and `Emergency` are not source roles.
- SourceRoutePlan contract still forbids silent fallback.
- DataSourceService is still the only production path allowed to call adapter factory.
- Clean writes still require WriteManager.
- Snapshot lineage still requires `source_fetch_ids` and `source_content_hashes`.
- Any known gap is explicitly classified before Phase 1.

**Audit checklist:**

- Audit must verify that Plan did not ignore any Section 5 source.
- Audit must inspect the actual code references, not only docs.
- Audit must check test logs and exact command outputs.
- Audit must fail Phase 0 if any DB/schema/write/source-route mismatch is unresolved and not explicitly re-deferred.

### Phase 1 — Read-only current DB and data-root inventory

**Purpose:** prove the starting DB/data state before ingestion.

**Execute actions:**

1. Run read-only DB inspect against the target local DB or a copied sandbox DB.
2. Record table list and key row counts.
3. Record raw/parquet/audit/report file counts.
4. Record latest fetch/job/validation/conflict/manual-review/write evidence.
5. Create `phase1_before_ingestion_inventory.json` and `phase1_before_ingestion_inventory.md`.
6. If using a sandbox copy, record the copy source and checksum/size before use.

**Required evidence fields:**

- DB path
- DB file exists
- DB read-only open result
- DB file size
- data root path
- raw/parquet/audit/report file counts
- table list
- key table row counts, at minimum:
  - `schema_version`
  - `source_registry`
  - `file_registry`
  - `fetch_log`
  - `data_sync_job`
  - `job_event_log`
  - `validation_report`
  - `data_quality_log`
  - `source_conflict`
  - `manual_review_queue`
  - `write_audit_log`
  - `resource_guard_log`
  - `axis_observation`
  - `axis_feature_snapshot`
  - `axis_interpretation_snapshot`
  - `axis_snapshot_lineage`

**Required pass conditions:**

- DB opens in read-only mode.
- The pre-ingestion inventory is saved as evidence.
- The report clearly states whether the DB currently contains real data or only schema/config/fixture evidence.
- If existing data is present, the plan must stop and classify whether it is fixture, staged, user-provided, or production evidence before Phase 2.
- No mutation occurs during Phase 1.

**Audit checklist:**

- Audit must verify the inspect command or inspect API used read-only mode.
- Audit must compare evidence against `ops_db_inspect_contract.yaml`.
- Audit must explicitly approve the DB baseline before Phase 2.

### Phase 2 — Route/capability dry-run and no-mutation bridge design

**Purpose:** prove that selected Layer 1 indicators can be routed without fetching or writing.

**Execute actions:**

1. Select a tiny allowlist of Layer 1 indicators for first ingestion.
2. Each indicator must be `is_enabled=true`, not `is_forbidden`, not `is_blindspot`, and observable.
3. For each selected indicator, map:
   - `indicator_id`
   - `axis_id`
   - `data_domain`
   - `operation`
   - `frequency`
   - `primary_source`
   - `validation_source`
   - `fallback_policy`
   - required fields/unit
   - intended `as_of` range.
4. Generate SourceRoutePlan in dry-run/preview mode for each selected indicator.
5. Verify capability registry declares the operation and source.
6. Verify ResourceGuard permits the requested tiny window.
7. Verify no fetch, raw write, DB write, or clean write occurs.
8. Produce `phase2_route_preview_matrix.md` and `phase2_route_preview.json`.

**Required pass conditions:**

- Every selected indicator has a route plan.
- Route status must be `READY` for staged/authorized execution, or the phase must stop with a documented reason.
- Disabled/unauthorized sources return `DISABLED_SOURCE` or `USER_AUTH_REQUIRED`, never silent fallback.
- QMT/qmt_xqshare/Yahoo/live validation remains disabled unless the user explicitly authorized this specific phase.
- `fetch_log`, `file_registry`, `axis_observation`, and snapshot row counts do not change.

**Required tests / commands:**

```bash
pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py tests/test_data_cli_contract.py -q
```

New tests should be added if missing:

- `test_layer1Ingestion_routePreview_noMutation`
- `test_layer1Ingestion_forbiddenIndicator_rejectedBeforeRoute`
- `test_layer1Ingestion_blindspot_rejectedBeforeFetch`
- `test_layer1Ingestion_disabledSource_returnsRouteStatusWithoutFetch`
- `test_layer1Ingestion_noSilentFallback`

**Audit checklist:**

- Audit must inspect the selected indicator allowlist.
- Audit must verify no forbidden or BlindSpot indicator can enter the ingestion path.
- Audit must verify route output includes candidate skip reasons.
- Audit must verify DB row counts before and after dry-run are unchanged.

### Phase 3 — Micro-ingestion into evidence/staging only

**Purpose:** prove a tiny source fetch can produce local evidence without yet committing clean `axis_observation`.

**Execute actions:**

1. Use only a staged source, fixture source, or explicitly user-authorized real source.
2. Run one tiny ingestion window, for example one indicator and one as-of day, or the smallest valid source response.
3. Use DataSourceService or an orchestrator runner that depends on DataSourceService/fetch callable.
4. Generate and persist route evidence before adapter construction.
5. Call adapter fetch only through approved boundary.
6. Write raw/staged evidence and fetch_log.
7. Register file evidence in `file_registry` if raw evidence is emitted.
8. Do **not** write clean `axis_observation` in this phase.
9. Produce `phase3_micro_fetch_evidence.json` and `phase3_no_clean_write_proof.md`.

**Required pass conditions:**

- Fetch uses DataSourceService path, not direct adapter factory from Layer 1.
- SourceRoutePlan exists before fetch.
- FetchResult includes source, status, row count, and evidence metadata.
- `fetch_log` has exactly the expected row delta.
- `file_registry` has expected row delta if raw evidence file exists.
- `axis_observation` row count remains unchanged in Phase 3.
- ResourceGuard was checked before fetch.
- No external source was enabled without user authorization.

**Required tests:**

Existing tests to keep green:

```bash
pytest tests/test_datasource_service.py tests/test_sync_orchestrator.py tests/test_vendor_fetch_e2e.py tests/test_sync_jobs.py -q
```

New tests should be added if missing:

- `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch`
- `test_layer1MicroIngestion_persistsRoutePlanBeforeFetch`
- `test_layer1MicroIngestion_writesFetchLogAndRawEvidence`
- `test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation`
- `test_layer1MicroIngestion_resourceGuardPauseStopsBeforeFetch`

**Audit checklist:**

- Audit must verify no direct adapter factory import exists in Layer1 ingestion code.
- Audit must verify source route evidence predates fetch evidence.
- Audit must verify row-count deltas are exactly expected.
- Audit must verify raw/file evidence stays under configured data root.

### Phase 4 — Validate/conflict/write clean observation and build snapshots

**Purpose:** move the tiny, audited evidence into clean `axis_observation`, then prove Layer 1 snapshots consume it safely.

**Execute actions:**

1. Convert staged/fetched rows into Layer 1 observation rows using an explicit mapping function.
2. Run DataQualityValidator and create a `validation_report`.
3. Run SourceConflictValidator when a validation source exists or conflict rules apply.
4. Reject clean write if validation failed, severe conflict exists, manual review is required, schema hash changed without approval, or route/fetch lineage is missing.
5. Write clean `axis_observation` only through WriteManager.
6. Build `axis_feature_snapshot` from clean `axis_observation`.
7. Build `axis_interpretation_snapshot` from feature snapshot.
8. Build `axis_snapshot_lineage` using real fetch IDs and content hashes from validation/fetch evidence; test fallback lineage must not masquerade as production lineage.
9. Run post-ingestion read-only DB inspect and compare to Phase 1 baseline.
10. Produce `phase4_clean_write_and_snapshot_evidence.json` and `phase4_inventory_delta.md`.

**Required pass conditions:**

- `validation_report` row delta is expected and status is passing.
- `source_conflict` row delta is zero or expected with non-severe status; severe conflicts stop clean write.
- `write_audit_log` records successful write to `axis_observation` and any snapshot tables written through WriteManager.
- `axis_observation` row delta is exactly expected.
- `axis_feature_snapshot` row delta is exactly expected.
- `axis_interpretation_snapshot` row delta is exactly expected, unless MASTER explicitly splits interpretation into a later sub-phase.
- `axis_snapshot_lineage` includes non-empty `source_fetch_ids`, `source_content_hashes`, `rule_version`, `parameter_hash`, `resource_profile`, and correct `as_of_timestamp`.
- No observation has `as_of_timestamp` after allowed visibility/publish timestamp.
- FORBIDDEN and BlindSpot indicators do not enter `axis_observation`.
- Post-inspect evidence matches expected row deltas and shows no unexpected table mutations.

**Required tests:**

Existing tests to keep green:

```bash
pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
pytest tests/test_schema_migration.py tests/test_schema_contract.py -q
pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q
```

If actual test filenames differ, Plan must map equivalent tests in MASTER Source Context Index.

New tests should be added if missing:

- `test_layer1Observation_cleanWrite_requiresValidationReport`
- `test_layer1Observation_cleanWrite_usesWriteManager`
- `test_layer1Observation_validationFailure_blocksCleanWrite`
- `test_layer1Observation_severeConflict_blocksCleanWrite`
- `test_layer1Observation_manualReview_blocksNonManualPatchWrite`
- `test_layer1Observation_lineageIncludesFetchIdsAndHashes`
- `test_layer1Observation_noFutureDataRejected`
- `test_layer1Observation_forbiddenAndBlindspotNeverPersisted`
- `test_layer1Observation_postInspectShowsExpectedDeltasOnly`

**Final required validation command:**

```bash
pytest -q
```

**Audit checklist:**

- Audit must compare Phase 1 and Phase 4 DB inventories.
- Audit must verify every row-count delta is expected.
- Audit must verify clean writes go through WriteManager.
- Audit must verify lineage is not synthetic unless the phase is explicitly marked fixture-only.
- Audit must verify no out-of-scope tables changed.
- Audit must verify no external live source was enabled without explicit user authorization evidence.

## 9. Final batch pass/fail rules

The batch is PASS only when all conditions below are true:

1. Phase 0, 1, 2, 3, and 4 each have separate evidence and audit sign-off.
2. No phase depends on uncited memory or unindexed sources.
3. `MASTER.plan.md` contains a complete Source Context Index.
4. `AUDIT.plan.md` contains a complete Audit Source Trace.
5. `implement.jsonl`, `audit.jsonl`, and `check.jsonl` are curated; they do not dump every original task or every docs/spec file by default.
6. The selected ingestion scope is tiny, explicit, and user-authorized if it touches live/staged external data.
7. Route preview works and is read-only.
8. SourceRoutePlan exists before fetch.
9. DataSourceService is used for production fetch path.
10. ResourceGuard is checked before fetch and before clean merge.
11. Raw/staged/fetch evidence is recorded before clean write.
12. Clean `axis_observation` write requires passing validation and no blocking conflict.
13. Clean `axis_observation` write uses WriteManager.
14. Feature and interpretation snapshots consume clean observations, not raw external payloads.
15. Snapshot lineage includes real source fetch IDs and content hashes for non-fixture data.
16. DB inspect before/after evidence proves only expected row-count deltas.
17. Full `pytest -q` is green.
18. Any remaining limitations are recorded in `docs/AUDIT_DEFERRED_REGISTRY.md` and `docs/UNRESOLVED_ISSUES_REGISTRY.md` with phase, owner/task hook, and closure test.

The batch is FAIL if any of the following occurs:

- Direct adapter factory call from Layer 1 production code.
- Any silent fallback.
- Any clean `axis_observation` write outside WriteManager.
- Any clean write without validation report.
- Any severe conflict or manual-review-required row written as normal clean data.
- Any live source enabled without user authorization.
- Any full-market/full-history scan triggered by default.
- Any DB mutation during read-only inventory or route-preview phases.
- Any out-of-scope Layer2/3/4/5/API/Agent work hidden in this batch.
- Any docs/spec path used as implementation path.

## 10. Required audit structure

Audit must be split into at least five passes:

| Audit pass | Covers                                                 | Required verdict                                      |
| ---------- | ------------------------------------------------------ | ----------------------------------------------------- |
| A0         | Phase 0 contract and DB design gate                    | PASS required before Phase 1                          |
| A1         | Phase 1 read-only DB/data-root inventory               | PASS required before Phase 2                          |
| A2         | Phase 2 route/capability dry-run and no-mutation proof | PASS required before Phase 3                          |
| A3         | Phase 3 micro-fetch evidence/staging only              | PASS required before Phase 4                          |
| A4         | Phase 4 clean write/snapshot/lineage/post-inspect      | PASS required for batch completion                    |
| A5         | Final cross-phase regression and registry closeout     | PASS required before Batch 3 uses real Layer1 outputs |

Audit must inspect at least:

- route plan fields and status
- fetch log rows and error/status mapping
- file registry rows and paths
- validation report rows and status
- source conflict rows and severity
- write audit rows and target tables
- clean `axis_observation` row deltas
- snapshot row deltas
- snapshot lineage fields
- ResourceGuard evidence
- DB inspect before/after reports
- source authorization evidence
- forbidden import/static boundary checks

## 11. Required evidence artifact names

The Trellis task should create an `execute-evidence/` directory containing at least:

```text
phase0_source_context_matrix.md
phase0_db_contract_gate.md
phase0_test_output.txt
phase1_before_ingestion_inventory.json
phase1_before_ingestion_inventory.md
phase2_route_preview.json
phase2_route_preview_matrix.md
phase2_no_mutation_proof.md
phase3_micro_fetch_evidence.json
phase3_no_clean_write_proof.md
phase3_test_output.txt
phase4_clean_write_and_snapshot_evidence.json
phase4_inventory_delta.md
phase4_test_output.txt
final_pytest_output.txt
final_registry_update.md
```

If a phase is intentionally fixture-only or staged-only, evidence names must include that fact and the audit report must not call it production live ingestion.

## 12. Registry and closeout requirements

Before final PASS:

1. If this batch proves the first clean Layer1 observation bridge, add or update a resolved record that says exactly what source type was used: fixture, staged, user-authorized live, or production live.
2. If production CLI remains incomplete, keep `R2.6-IMPL-6` / `D2-P1-3` deferred to Batch 6 with closure tests.
3. If broad backfill/full_load/data_quality runners remain incomplete, keep their deferred IDs visible.
4. If source-health snapshot remains incomplete, keep `D2-P2-1` deferred.
5. If the bridge is only staged/fixture and not real live production, do not mark live source validation closed.
6. If a real source is used, record user authorization evidence path and scope.

## 13. Handoff to Batch 3

Batch 3 may treat Layer 1 as real-data-ready only if the final Batch 2.5 audit states:

```text
Layer 1 observation ingestion bridge: PASS
Ingestion type: staged / user-authorized live / production live
Allowed downstream use: yes/no
Allowed indicator scope: <explicit list>
Allowed as_of window: <explicit window>
Remaining data limitations: <explicit list>
```

If Batch 2.5 closes only a fixture/staged micro-ingestion, Batch 3 must still label downstream real-data claims as not proven and must rely on fixture/staged semantics.

**`B2.5-O-05` (FRED primary vs `macro_supplementary`):** Layer 1 specs declare `FRED:DGS10` for `ENV-E1-DGS10`, but the Batch 2.5 bridge and Batch 2.75 Request 3 use staged `macro_supplementary.fetch_macro_series` via `akshare`. That route is **supplementary macro shape evidence only** — not live FRED primary and not production-live macro readiness. Downstream batches must not upgrade Request 3 success to FRED primary closure.

## 14. 未闭合项覆盖补充（Plan 不得遗漏）

执行 Batch2.5 follow-up、ingestion bridge refactor 或 Batch6 hygiene 计划前，必须读取 `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`，并核对：

| ID                        | 归属阶段                              | 本任务卡处理要求                                                                                                           |
| ------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `R3-B25-HYG-01`           | Batch6 hygiene / post-B2.5 PR-R2b-R2d | ingestion split R2b/R2c/R2d 必须按 `docs/architecture/layer1_ingestion_refactor_rollback_plan.md`，不能被 Batch2.75 吸收。 |
| `R2.6-IMPL-6` / `D2-P1-3` | Batch6 ops                            | 若 production CLI 仍不完整，必须继续 deferred 并写 closure tests。                                                         |
| `D2-P2-1`                 | Batch6 source-health                  | source-health snapshot 未完成时必须继续 deferred。                                                                         |
