# Merge gate report — 021 Layer3 snapshot builder

| Gate           | Command                                                                                       | Result                  |
| -------------- | --------------------------------------------------------------------------------------------- | ----------------------- |
| Tier A sync    | `uv sync --locked`                                                                            | PASS exit 0             |
| Tier A L1      | `uv run pytest tests/test_layer3_snapshot_builder.py -q`                                      | PASS 8/8                |
| Tier A L3      | `uv run pytest tests/test_batch3_staged_downstream_gate.py -q`                                | PASS 2/2                |
| Tier A lint    | `uv run ruff check backend/app/layer3_chains tests/test_layer3_snapshot_builder.py`           | PASS                    |
| Tier A compile | `uv run python -m compileall backend/app/layer3_chains tests/test_layer3_snapshot_builder.py` | PASS                    |
| Tier B         | `uv run pytest -q`                                                                            | PASS exit 0 (2 skipped) |
| Handoff        | `validate-execute-handoff`                                                                    | PASS exit 0             |

## AC coverage

- AC-021-1: `test_layer3Snapshot_buildsFromStagedLoaderAndL5_success`
- AC-021-2: `test_layer3Snapshot_lineageRequiredFieldsComplete` + `test_snapshotLineageContainsSourceHashes`
- AC-021-3: `test_snapshotRejectsFutureInput`
- AC-021-4: `test_layer3Snapshot_eventOnly_skipsPriceFields`
- AC-021-5: `test_layer3Snapshot_layer5MappingView_nonEventOnly`
- AC-021-6: `test_layer3Snapshot_nonStagedL5Source_rejects`

## Defer boundaries (unchanged)

- ADV-R3X full cross-layer lineage persistence → 022
- R3Y registry hygiene → separate slice
- No production-live claims
