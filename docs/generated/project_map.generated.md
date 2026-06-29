# Project Map (generated)

Do not edit by hand. Regenerate with `uv run python scripts/generate_project_map.py`.

Rating SSOT: `MODULE_COMPLETION_RATING.md`

## project_scaffold

- module_ids: A1, A6, A7
- implementation: tests/\*\*, pyproject.toml, uv.lock
- docs: 2
- contracts: 3
- required_evidence: context_pack.json, loop_manifest.json
- tests: 1

## layer1_axes

- module_ids: G1, K2
- implementation: backend/app/layer1_axes/\*\*
- docs: 4
- contracts: 3
- implementation_tasks: 2
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 9
- forbidden: production-live ready, live production ingestion

## layer2_sensors

- module_ids: G2
- implementation: backend/app/layer2_sensors/\*\*
- docs: 2
- contracts: 3
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 5
- forbidden: production-live ready, live production ingestion

## layer5_evidence

- module_ids: G5, G6
- implementation: backend/app/layer5_evidence/**, backend/app/evidence/**
- docs: 2
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 4
- forbidden: production-live ready

## datasources

- module_ids: C1, C2, C3, C4, J5
- implementation: backend/app/datasources/\*\*
- docs: 5
- contracts: 8
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 7
- forbidden: bypass route readiness gate

## validators

- module_ids: B1, B2, B3
- implementation: backend/app/validators/\*\*, backend/app/db/validation_gate.py, backend/app/db/write_manager.py
- docs: 4
- contracts: 3
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 5
- forbidden: direct table write outside WriteManager

## ops

- module_ids: E1, E2, E3, E4, E5, F0
- implementation: backend/app/ops/**, backend/app/cli/**, scripts/run_staged_pilot.py, scripts/production_gate.py, scripts/check_doc_links.py, scripts/production_equivalent_smoke.py, scripts/init_db.py, scripts/sync_registry.py, scripts/qmd_ops.py
- docs: 10
- contracts: 6
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json, audit_matrix.json
- tests: 11
- forbidden: production-live ready, live production ingestion

## source_health

- module_ids: D4
- implementation: backend/app/ops/source_health_writer.py, backend/app/ops/b3f_sh_registry_guard.py
- docs: 2
- contracts: 1
- required_evidence: context_pack.json, loop_manifest.json
- tests: 1
- forbidden: DH2 creates source_health_snapshot DDL

## db_platform

- module_ids: A2
- implementation: backend/app/db/\*\*, scripts/init_db.py
- docs: 5
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json
- tests: 4

## sync_orchestrator

- module_ids: D1, D2, D3
- implementation: backend/app/sync/\*\*
- docs: 3
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json
- tests: 3

## core_platform

- module_ids: A3, A4, A5
- implementation: backend/app/core/**, backend/app/storage/**, backend/app/util/\*\*
- docs: 3
- contracts: 2
- required_evidence: context_pack.json, loop_manifest.json, evidence_index.json
- tests: 4

## model_inputs

- module_ids: K1
- implementation: specs/model_inputs/\*\*
- docs: 2
- contracts: 5
- required_evidence: context_pack.json, loop_manifest.json
- tests: 1
- forbidden: production-live ready, runtime fetch from whitelist package alone

## layer3_chains

- module_ids: G3, K3
- implementation: backend/app/layer3_chains/\*\*
- docs: 3
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json
- tests: 2

## layer4_markets

- module_ids: G4
- implementation: backend/app/layer4_markets/\*\*
- docs: 1
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json, loop_manifest.json
- tests: 1

## api_platform

- module_ids: I1, I8
- implementation: backend/app/api/\*\*
- docs: 4
- contracts: 2
- implementation_tasks: 1
- required_evidence: context_pack.json
- tests: 1

## agents

- module_ids: I2, J2
- implementation: backend/app/agents/\*\*
- docs: 4
- contracts: 1
- implementation_tasks: 1
- required_evidence: context_pack.json
- tests: 1

## frontend_platform

- module_ids: I3
- implementation: frontend/\*\*
- docs: 3
- contracts: 2
- required_evidence: context_pack.json
- tests: 2

## notifications

- module_ids: I4, E7
- implementation: backend/app/notifications/\*\*
- docs: 2
- contracts: 1
- required_evidence: context_pack.json
- tests: 0

## backtest_review

- module_ids: I5, I6, I7
- implementation:
- docs: 3
- contracts: 4
- implementation_tasks: 1
- required_evidence: context_pack.json
- tests: 0

## governance

- module_ids: J1, J3, J4, J6, E6
- implementation: scripts/check_doc_links.py, scripts/loop_maintain.py, scripts/generate_project_map.py
- docs: 4
- contracts: 5
- required_evidence: context_pack.json, release_manifest.json
- tests: 2

## privacy_boundary

- module_ids: J7
- implementation:
- docs: 3
- contracts: 2
- required_evidence: context_pack.json
- tests: 0

## etl

- module_ids: H1
- implementation: backend/app/etl/\*\*
- docs: 1
- contracts: 0
- required_evidence: context_pack.json
- tests: 1
