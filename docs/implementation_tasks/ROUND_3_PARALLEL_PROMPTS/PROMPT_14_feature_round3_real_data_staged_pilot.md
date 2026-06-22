# PROMPT_14 — feature/round3-real-data-staged-pilot

Use this prompt in a fresh implementation session. The session must create the branch/worktree first, then execute the controlled real-data staged pilot task.

## 1. Branch / worktree setup

- Branch to create: `feature/round3-real-data-staged-pilot`
- Base branch: latest user-confirmed `master` or `integration/round3`
- Suggested worktree path: `../quant-monitor-desk-wt-feature-r3-real-data-staged-pilot`
- Target merge branch: `integration/round3`

Before creating the branch, confirm:

- Working tree is clean, or existing dirty files are explicitly approved by user/coordinator.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md` exists.
- Current completed batch artifacts from PROMPT_07–10 are visible, or their absence is recorded.
- Data-source routing blockers and DB/write/validation blockers have either been fixed, are not relevant to this pilot slice, or are explicitly documented as risk controls in the plan.

## 2. Mission

Implement a minimal, bounded, staged-only real-data pilot that uses approved no-credential public sources to generate raw/staging/sandbox evidence and expose real route, fetch, schema, validation, conflict, and DB no-mutation behavior.

This is not production-live readiness. This branch must not default to production clean writes.

## 3. Required task card

Read and follow:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`

## 4. Required Plan-stage input index

Read and summarize before writing the plan:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/modules/source_route_plan.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/local_file_system.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/ops/db_inspect_cli.md`
- `docs/ops/data_health_cli.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/runtime_versions.md`
- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- `backend/app/storage/raw_store.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/db/validation_gate.py`
- `backend/app/db/write_manager.py`
- `backend/app/sync/`
- `backend/app/ops/db_inspector.py`
- `backend/app/ops/live_pilot.py`
- `tests/test_datasource_service.py`
- `tests/test_vendor_fetch_e2e.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_source_route_planner.py`
- `tests/test_source_capabilities.py`
- `tests/test_raw_store.py`
- `tests/test_db_validation_gate.py`
- `tests/test_ops_db_inspector.py`
- `tests/test_production_live_pilot_policy.py`

Do not stop at this list. Trace through project maps, source registry, contract authority fields, route planner, adapters, tests, and latest audit reports before selecting pilot scope.

## 5. Current completed batch artifacts to include

User confirmed the current four branches have completed. The pilot must be based on their latest state if available; otherwise record `MISSING_CURRENT_BATCH_EVIDENCE` and explain how the pilot avoids relying on missing material.

Must inspect, when available:

- `feature/round3-019-layer2-sensor`: Layer2 input/output, snapshot lineage, source fields, no-future-data, double_count_guard.
- `feature/round3-023a-evidence-foundation`: evidence identity, source_fetch_ids, source_content_hashes, manual-review flags, Agent-text-not-fact-source.
- `review/round3-019-plan-audit`: final PASS / WARN / BLOCK and required fixes.
- `debt/r3b275-018c-live-manual-probe-plan`: TDX authorization plan and no-live-fetch/no-mutation boundaries. This pilot still must not perform TDX live fetch.
- integration/coordinator artifacts and current-batch audit reports.

## 6. Allowed sources and sample limits

Allowed first pilot sources only:

- `baostock`
- `akshare` as validation-only / staged-only
- `cninfo` metadata only unless plan explicitly justifies a narrower safe slice

Default caps:

```yaml
max_symbols: 1-3
max_trade_days: 5-20
max_rows_per_source_domain: 100
max_network_calls_per_run: 10
production_clean_write: false
```

## 7. Allowed files

Only after the plan names them:

- `backend/app/ops/` pilot runner or source probe module
- `backend/app/datasources/` only for narrow adapter/service fixes required by pilot
- `backend/app/storage/` only for raw/staged evidence handling
- `scripts/` only for a thin wrapper following existing project pattern
- narrow pilot/source/storage/policy tests
- task-local Trellis plan/evidence files

## 8. Forbidden behavior

- No production clean write by default.
- No full market scan.
- No full history backfill.
- No unbounded network calls.
- No TDX live fetch.
- No QMT / xqshare enablement.
- No validation-only source as sole fact source.
- No `tdx_pytdx` Primary or fallback.
- No live FRED.
- No production DB migration.
- No deleting or weakening gates.
- No production-live readiness claim.

## 9. Required evidence

The branch must produce or record:

- route preview matrix
- source fetch attempt summary
- raw evidence manifest
- staging evidence manifest
- validation report summary
- source/domain success/failure taxonomy
- production DB no-mutation proof
- ResourceGuard caps result
- close / re-defer decision

## 10. Verification commands

Run at minimum:

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_data_adapter_contract.py -q
pytest tests/test_raw_store.py -q
pytest tests/test_db_validation_gate.py -q
pytest tests/test_ops_db_inspector.py -q
pytest tests/test_production_live_pilot_policy.py -q
```

If vendor fixture or pilot E2E tests are created/updated:

```bash
pytest tests/test_vendor_fetch_e2e.py -q
```

If docs/spec links changed:

```bash
python scripts/check_doc_links.py
```

## 11. Done criteria

- At least one allowed source/domain produces bounded staged/raw evidence, or each attempted source has clear failure/re-defer reason.
- Route preview explains selected/skipped/disabled states.
- Validation evidence reflects real data quality or explicit implementation gaps.
- Production clean tables remain unmodified by proof.
- Current PROMPT_07–10 completion/evidence is included or explicitly marked missing.
- No production-live readiness claim.
- Merge report lists successful sources, failed sources, field/schema/quality issues, DB/no-mutation status, and next expansion or re-defer recommendations.
