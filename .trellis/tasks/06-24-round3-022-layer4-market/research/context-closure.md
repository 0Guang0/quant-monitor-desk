# Context closure — 022 Layer4 market structure

## Upstream wiring

- Optional `upstream_snapshot_ids` on `MarketStructureBuilder.build()` (Layer3 snapshot handoff)
- `core/snapshot_lineage.py` — `LINEAGE_REQUIRED_FIELDS` kernel
- Pattern donors: `layer3_chains/snapshot_builder.py` + `lineage.py` (read-only)
- Staged fixture: `tests/fixtures/layer4_staged_market/manifest.yaml` (`source_mode: staged_fixture_only`)

## Deferred (unchanged)

- Full 8× live MarketAdapter implementations
- WriteManager DB sync / clean table persistence
- `ADV-R3X-LINEAGE-001` cross-layer DB lineage persistence
- `R3Y-LINEAGE-VR-001` registry trio hygiene
- FastAPI `GET /api/layer4/*` / CLI `qm sync-layer4`
- Layer5 full instrument history (`023`)

## Slice boundary

- staged-only CN_A fixture; no production-live claims
- no forbidden ops/registry edits
- contract-scoped lineage subset only (not full ADV-R3X closure)
