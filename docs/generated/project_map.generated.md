# Project Map (generated)

Do not edit by hand. Regenerate with `uv run python scripts/generate_project_map.py`.

## layer1_axes
- implementation: backend/app/layer1_axes/**
- docs: 3
- contracts: 3
- tests: 9
- forbidden: production-live ready, live production ingestion

## layer2_sensors
- implementation: backend/app/layer2_sensors/**
- docs: 2
- contracts: 3
- tests: 5
- forbidden: production-live ready, live production ingestion

## layer5_evidence
- implementation: backend/app/layer5_evidence/**
- docs: 2
- contracts: 2
- tests: 2
- forbidden: production-live ready

## datasources
- implementation: backend/app/datasources/**
- docs: 4
- contracts: 4
- tests: 6
- forbidden: bypass route readiness gate

## validators
- implementation: backend/app/validators/**, backend/app/db/validation_gate.py, backend/app/db/write_manager.py
- docs: 3
- contracts: 3
- tests: 5
- forbidden: direct table write outside WriteManager

## ops
- implementation: backend/app/ops/**, backend/app/cli/**, scripts/run_staged_pilot.py, scripts/production_gate.py, scripts/check_doc_links.py, scripts/production_equivalent_smoke.py, scripts/init_db.py, scripts/sync_registry.py, scripts/qmd_ops.py
- docs: 7
- contracts: 3
- tests: 10
- forbidden: production-live ready, live production ingestion

## db_platform
- implementation: backend/app/db/**, scripts/init_db.py
- docs: 3
- contracts: 2
- tests: 4

## sync_orchestrator
- implementation: backend/app/sync/**
- docs: 2
- contracts: 1
- tests: 3

## core_platform
- implementation: backend/app/core/**, backend/app/storage/**, backend/app/util/**
- docs: 2
- contracts: 2
- tests: 3

## layer3_chains
- implementation: backend/app/layer3_chains/**
- docs: 1
- contracts: 1
- tests: 0

## layer4_markets
- implementation: backend/app/layer4_markets/**
- docs: 1
- contracts: 1
- tests: 0

## api_platform
- implementation: backend/app/api/**
- docs: 2
- contracts: 0
- tests: 0

## agents
- implementation: backend/app/agents/**
- docs: 1
- contracts: 0
- tests: 0

## notifications
- implementation: backend/app/notifications/**
- docs: 1
- contracts: 0
- tests: 0

## etl
- implementation: backend/app/etl/**
- docs: 1
- contracts: 0
- tests: 1

