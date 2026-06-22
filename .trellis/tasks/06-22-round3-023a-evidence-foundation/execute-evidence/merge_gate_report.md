# Merge gate report — `feature/round3-023a-evidence-foundation`

## Changed files (allowed scope)

- `backend/app/layer5_evidence/models.py`
- `backend/app/layer5_evidence/foundation.py`
- `backend/app/layer5_evidence/lineage.py`
- `backend/app/layer5_evidence/__init__.py`
- `tests/test_layer5_evidence_foundation.py`
- `specs/contracts/layer5_evidence_contract.yaml` (foundation additions only)

## Forbidden scope honored

- No full `023` / bars / events / financials ingestion
- No production DB mutation or source/network fetch
- No edit to `specs/contracts/snapshot_lineage_contract.yaml` (019 owner)

## Compatibility (019 / 020 / 021)

- **019**: `InstrumentEvidenceRef` matches instrument_registry required fields; lineage uses same `LINEAGE_REQUIRED_FIELDS` as Layer1/2.
- **020**: `EvidenceFoundationRecord.target_id` / `target_type` ready for chain anchor references.
- **021**: `Layer5LineageBuilder` accepts `upstream_snapshot_ids` for Layer4 snapshot lineage.

## Deferred

- Full `023` → `feature/round3-023b-evidence-chain-full`
- `R3-PARTIAL-4` severe manual-review queue UX
