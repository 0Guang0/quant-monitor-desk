# Context closure — 023A

## Upstream wiring
- Layer1/2 lineage field set (`LINEAGE_REQUIRED_FIELDS`) reused for Layer5 envelopes
- `InstrumentEvidenceRef` aligns with `instrument_registry` contract fields
- `snapshot_lineage_contract.yaml` read-only; compatibility via code/tests only

## Downstream
- 019: `layer5_instrument_id` on cross-asset registry entries
- 020/021: `target_id` / `upstream_snapshot_ids` hooks only (no cross-layer API yet)
