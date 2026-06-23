# Context closure — 020 Layer3 loader

## Upstream wiring

- `PROJECT_ROOT` from `backend/app/config.py` for `STAGED_LAYER3_BUNDLE_DIR`
- Pattern reference: `backend/app/layer2_sensors/sensor_loader.py` (`staged_fixture_only` gate)
- Contract: `specs/contracts/layer3_loader_contract.yaml` (seven hard rules)

## Deferred upstream

- `021` industry_chain_daily_snapshot builder
- lineage persistence / `snapshot_lineage_contract` writes
- production registry under `specs/layer3_global_industry_chains/`
- WriteManager DB sync (optional; not AC)

## Slice boundary

- staged fixture bundle only; no production-live claims
