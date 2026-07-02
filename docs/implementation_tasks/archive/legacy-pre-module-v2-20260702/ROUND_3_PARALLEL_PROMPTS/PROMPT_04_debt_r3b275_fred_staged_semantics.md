# PROMPT_04 — debt/r3b275-fred-staged-semantics

Use this prompt in a fresh session for the FRED / macro supplementary staged-semantics debt branch.

## Mission

Ensure `B2.5-O-05` and related Round 3 wording cannot be misread as live FRED or production-live macro evidence. This branch should clarify staged-only semantics and update tests/docs if needed.

## Branch / worktree

- Branch: `debt/r3b275-fred-staged-semantics`
- Base: `integration/round3` if it exists; otherwise `master` at or after `700135ca`
- Suggested worktree path: `../quant-monitor-desk-wt-r3b275-fred-staged`
- Target merge branch: `integration/round3`

## Required reads before planning

1. `AGENTS.md`
2. `.trellis/workflow.md`
3. `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
4. `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
5. `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
6. `docs/ROUND3_HANDOFF.md`
7. `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
8. `docs/quality/production_live_pilot_policy.md`
9. `docs/AUDIT_DEFERRED_REGISTRY.md`
10. `docs/UNRESOLVED_ISSUES_REGISTRY.md`
11. `docs/RESOLVED_ISSUES_REGISTRY.md`
12. `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`
13. `specs/datasource_registry/source_registry.yaml`
14. `specs/datasource_registry/source_capabilities.yaml`
15. `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`
16. `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`

## Source IDs

- `B2.5-O-05`
- Related context: `R3-B2.75-REQ2-EM`, `R3-B3-STAGED-DOWNSTREAM-GATE`

## Allowed files

- staged policy docs
- production pilot policy docs
- Round3 handoff/map wording
- 018A/019 task-card wording if stale
- policy or registry tests that assert staged-only semantics

## Hard boundaries

- Do not add live FRED fetch.
- Do not promote `macro_supplementary` to production-live evidence.
- Do not change route defaults.
- Do not write the project database.
- Do not implement Layer2 or Layer1 runtime logic.

## Workflow

1. Create a Phase 8D lightweight plan.
2. Trace every occurrence of FRED / macro supplementary / staged macro wording.
3. Decide whether `B2.5-O-05` can close or must remain deferred.
4. Update only the minimum docs/tests needed to make staged semantics unambiguous.
5. Run policy and registry tests.
6. Produce a merge report.

## Verification commands

- `pytest tests/test_batch25_production_data_gate.py -q`
- `pytest tests/test_production_live_pilot_policy.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `python scripts/check_doc_links.py`

## Done criteria

- FRED/macro wording cannot imply live production readiness.
- `B2.5-O-05` has close/re-defer status with owner, phase, and closure command.
- No runtime/source behavior changed.
- Merge report lists tests and remaining deferred items.
