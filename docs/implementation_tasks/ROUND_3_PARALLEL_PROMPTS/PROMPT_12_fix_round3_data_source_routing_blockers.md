# PROMPT_12 — fix/round3-data-source-routing-blockers

Use this prompt in a fresh implementation session. The session must create the branch/worktree first, then execute the minimal data-source routing blocker repair task.

## 1. Branch / worktree setup

- Branch to create: `fix/round3-data-source-routing-blockers`
- Base branch: latest user-confirmed `master` or `integration/round3`
- Suggested worktree path: `../quant-monitor-desk-wt-fix-r3-data-source-routing-blockers`
- Target merge branch: `integration/round3`

Before creating the branch, confirm:

- Working tree is clean, or existing dirty files are explicitly approved by user/coordinator.
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md` exists.
- Current completed batch artifacts from PROMPT_07–10 are visible, or their absence is recorded.

## 2. Mission

Fix the minimal data-source, registry, capability, route planner, and DataSourceService blockers that prevent a trustworthy real-data staged pilot.

This task does not enable production-live data access. It must preserve disabled-by-default and validation-only boundaries.

## 3. Required task card

Read and follow:

- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_data_source_routing_blockers.md`

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
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/runtime_versions.md`
- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- `tests/test_source_capabilities.py`
- `tests/test_source_route_planner.py`
- `tests/test_datasource_service.py`
- `tests/test_data_adapter_contract.py`
- `tests/test_platform_source_matrix.py`

Do not stop at this list. Trace through project maps, contract authority fields, imports, adapters, route planner, tests, and latest audit reports to identify all files needed before changing code.

## 5. Current completed batch artifacts to include

User confirmed the current four branches have completed. Include their source/route implications if present; otherwise record `MISSING_CURRENT_BATCH_EVIDENCE`.

Must inspect, when available:

- `feature/round3-019-layer2-sensor`: source/domain dependencies and snapshot source fields.
- `feature/round3-023a-evidence-foundation`: source_fetch_ids, source_content_hashes, evidence identity compatibility.
- `review/round3-019-plan-audit`: PASS / WARN / BLOCK findings about source misuse, live/FRED misuse, production-readiness claims.
- `debt/r3b275-018c-live-manual-probe-plan`: tdx_pytdx authorization, route preview, disabled validation-only preservation.
- integration/coordinator artifacts and current-batch audit reports.

## 6. Allowed files

Only after the plan names them:

- `specs/contracts/data_adapter_contract.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/source_route_contract.yaml` only if contract gap is proven
- `backend/app/datasources/`
- `backend/app/datasources/adapters/`
- narrow source/route tests
- task-local Trellis plan/evidence files

## 7. Forbidden behavior

- No production-live readiness claim.
- No live source fetch.
- No production DB writes.
- No enabling `tdx_pytdx` by default.
- No making `tdx_pytdx` Primary or fallback.
- No enabling QMT / xqshare / Yahoo by default.
- No validation source silent promotion to Primary.
- No silent fallback.
- No closing Eastmoney hist Request 2.
- No broad real-data pilot implementation in this branch.

## 8. Required safeguards

- Start with RED tests for the exact drift being fixed.
- FetchResult status union must match contract and implementation.
- Every declared domain must either route preview cleanly or produce an explicit disabled/deferred reason.
- `selected_source_id` must remain null unless route status is READY.
- DataSourceService must route before adapter construction.
- Override/skip behavior must be auditable and not silent.

## 9. Verification commands

Run at minimum:

```bash
pytest tests/test_source_capabilities.py -q
pytest tests/test_source_route_planner.py -q
pytest tests/test_datasource_service.py -q
pytest tests/test_data_adapter_contract.py -q
pytest tests/test_platform_source_matrix.py -q
pytest tests/test_production_live_pilot_policy.py -q
```

If interface probe behavior changed:

```bash
pytest tests/test_interface_probe_018c.py -q
```

If docs/spec links changed:

```bash
python scripts/check_doc_links.py
```

## 10. Done criteria

- Source/domain route blockers are fixed or explicitly deferred with evidence.
- Disabled/validation-only source boundaries remain intact.
- Current PROMPT_07–10 completion/evidence is included or explicitly marked missing.
- Tests prove no silent fallback, no disabled source selection, and no validation source promotion.
- Merge report lists changed files, tests, ResourceGuard/DB mutation status, and remaining deferred source/domain items.
