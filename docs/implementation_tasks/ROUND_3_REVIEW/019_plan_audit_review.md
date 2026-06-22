# 019_plan_audit_review — Review Branch for Layer2 Plan/Audit

## 1. Round / batch / branch

| Field                | Value                                                                       |
| -------------------- | --------------------------------------------------------------------------- |
| Round                | Round 3                                                                     |
| Batch                | Batch 3 review lane                                                         |
| Branch               | `review/round3-019-plan-audit`                                              |
| Can run in parallel? | Yes. Run beside `feature/round3-019-layer2-sensor` as a read-only reviewer. |
| Must not do          | No implementation, no source fetch, no DB write, no branch merge.           |

## 2. Mission

Review the `feature/round3-019-layer2-sensor` plan and audit materials before or during implementation. The reviewer verifies that the implementation branch is not missing staged-only limits, lineage rules, double-counting rules, evidence boundaries, and data-source constraints.

This branch is a review/audit lane. It should produce findings and recommendations, not runtime code.

## 3. Required Plan-stage input index

The reviewer must read and summarize:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/ROUND3_HANDOFF.md`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/README.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `docs/modules/layer2_cross_asset_sensor.md`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `docs/modules/layer1_axes_and_indicators.md` if present, otherwise the current Layer1 module docs
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/write_manager.md`
- `docs/modules/duckdb_and_parquet.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

If `feature/round3-019-layer2-sensor` has a MASTER.plan.md or AUDIT.plan.md, review those as the primary artifacts.

## 4. Review scope

Check for:

- `R3-B3-STAGED-DOWNSTREAM-GATE` closure is referenced.
- Batch 2.75 closeout `PILOT_FAIL_SOURCE` is not upgraded to production-live readiness.
- `tdx_pytdx` is not used as a production source.
- FRED/macro supplementary remains staged-only.
- Layer2 does not duplicate Layer1 slow variables or Layer3/4/5 responsibilities.
- `double_count_guard` has business-semantics tests.
- snapshot lineage uses as-of visible time and proves no future data.
- WriteManager / ResourceGuard rules are not bypassed.
- tests contain semantic assertions, not only existence checks.

## 5. Allowed files

- task-local review notes or Trellis review task files
- `docs/implementation_tasks/ROUND_3_REVIEW/019_plan_audit_review.md` only if correcting this task card
- optional review report under a dedicated review task path

## 6. Forbidden files / behavior

- No backend implementation.
- No tests added to implementation branch from reviewer branch unless a separate user-approved repair branch is created.
- No production DB mutation.
- No source/network fetch.
- No registry row edits.
- No merging implementation branch.

## 7. Required output

Produce a review report with:

- PASS / BLOCK / WARN result
- reviewed artifacts
- findings grouped by blocker / non-blocker / suggestion
- required fixes for the implementation branch
- explicit statement on staged-only compliance
- explicit statement on data-source boundaries
- explicit statement on snapshot lineage/future-data risk

## 8. Verification commands

Reviewer should run only read-oriented or targeted tests if available:

- `pytest tests/test_batch3_staged_downstream_gate.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_trellis_audit_trace_authority.py -q`

Do not claim full implementation verification unless implementation branch tests were actually run in that branch.
