# Adversarial Self-Check — Phase 2 Route Dry-Run (post §8.3)

> Date: 2026-06-20 · Lens: 018A §8 Phase 2, MASTER §8.3, `source_route_contract.yaml`, `datasource_service_contract.yaml`, `source_capability_contract.yaml`, `data_sync_quick_reference.md`

## Verdict

**PASS after remediation** — initial Phase 2 implementation met core AC-P2-1..3 but omitted explicit capability gate, ResourceGuard stop documentation, Phase 1 `phase2_gate` enforcement on task evidence, and `intended_as_of_range` in preview artifacts.

## Findings → fixes

| ID       | Severity | Finding                                                                                    | Fix                                                                                                  |
| -------- | -------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| P2-SC-01 | P1       | 018A step 5 (capability registry) not enforced in `preview_routes`                         | `_verify_capability()` calls `assert_source_domain_operation` on selected source or registry primary |
| P2-SC-02 | P1       | ResourceGuard PAUSE/HARD_STOP recorded but not surfaced as stop reason                     | `_enforce_resource_guard()` raises `ResourceGuardBlockedError` (parity with fetch)                   |
| P2-SC-03 | P1       | `capture_task_phase2_evidence` ignored Phase 1 `phase2_gate`                               | `_load_phase2_gate()` blocks when inventory present and unauthorized                                 |
| P2-SC-04 | P2       | 018A step 3 `intended as_of range` missing from evidence                                   | `intended_as_of_range` in preview JSON/MD (single-day eco window)                                    |
| P2-SC-05 | P2       | Task evidence lacked `phase2_gate` cross-reference                                         | `phase2_gate` copied into `phase2_route_preview.json` when inventory exists                          |
| P2-SC-06 | P2       | Plan-time docs not read at Execute: `staged_acceptance_policy`, `data_sync_command_matrix` | **Phase 3 boot mandatory** — see `execute-handoff.md` §8.4 step 3                                    |

## Confirmed in-scope (no change)

- Layer1 does not import `create_adapter` (`datasource_service_contract.yaml` boundary).
- `preview_route` only (`side_effects_allowed: false` contract intent).
- Frozen indicator `ENV-E1-DGS10` + staged `macro_supplementary.fetch_macro_series`; FRED live deferred (B2.5-O-05).
- Forbidden / BlindSpot rejected before route plan.
- DB row counts unchanged (`phase2_no_mutation_proof.md`).
- 018A Phase 2 prerequisite pytest block green.

## New tests (closure)

- `test_layer1Ingestion_routePreview_capabilityDeclaredForSelectedSource`
- `test_layer1Ingestion_routePreview_resourceGuardPauseRaises`
- `test_layer1Ingestion_phase2TaskEvidence_requiresPhase1GateWhenInventoryPresent`

## Residual deferrals (not Phase 2 blockers)

- B2.5-O-05 live FRED path
- B2.5-O-04 WriteManager commit (Phase 4)
- `unit` for ENV-E1-DGS10 defaults `unitless` in axis loader (spec YAML has no unit field)
