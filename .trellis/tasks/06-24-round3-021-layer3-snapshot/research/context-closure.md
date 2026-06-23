# Context closure — 021 Layer3 snapshot builder

## Upstream wiring

- `IndustryChainLoader` (`020`) → `IndustryChainLoadResult` anchors
- `core/snapshot_lineage.py` — `LINEAGE_REQUIRED_FIELDS` kernel
- Pattern: `layer2_sensors/snapshot_builder.py` + `lineage.py` (read-only reference)
- Staged L5 bars: `tests/fixtures/layer3_l5_staged_bars/manifest.yaml`

## Deferred (unchanged)

- Layer4 market snapshots (`022`)
- Full Layer5 evidence chain / live fetch (`023`)
- `ADV-R3X-LINEAGE-001` cross-layer persistence
- `R3Y-LINEAGE-VR-001` registry hygiene rows
- WriteManager DB sync / FastAPI / CLI

## Slice boundary

- staged-only; `source_mode: staged_fixture_only` on L5 manifest
- no production-live claims; no lineage contract writes
