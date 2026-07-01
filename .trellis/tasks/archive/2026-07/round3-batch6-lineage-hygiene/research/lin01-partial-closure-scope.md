# LIN-S3 — ADV-R3X-LINEAGE-001 partial closure scope

## Closed in B01-LIN (contract + staged envelope)

| Sub-range                                              | Evidence                                                                                              |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| L3 `Layer3LineageBuilder` empty fetch/hash fail-closed | `test_layer3Lineage_rejectsEmptySourceFetchIds`, `test_layer3Lineage_rejectsEmptySourceContentHashes` |
| L3 build lineage `LINEAGE_REQUIRED_FIELDS`             | `test_layer3Snapshot_lineageRequiredFieldsComplete`                                                   |
| L4 build lineage + upstream propagation                | `test_marketSnapshot_lineageRequiredFieldsComplete`, `test_marketSnapshot_lineageUpstreamFromLayer3`  |
| Shared kernel serialization                            | `test_snapshot_lineage_kernel.py -k lineage`                                                          |

## Re-deferred (owner B01-023 / Batch 6 migration)

| Sub-range                                                                    | Reason                                                          |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| L3/L4 production DuckDB lineage table write-back                             | Out of B01-LIN boundary; `layer5_evidence/**` + migration track |
| Full cross-layer `fetch_log → validation_report → axis_snapshot_lineage` E2E | L1 pattern only; L2/L3/L4 staged paths contract-scoped          |

## Registry proposal

`ADV-R3X-LINEAGE-001` → **PARTIAL** (contract pytest green) with residual **re-defer** to 023 for DB persistence sub-range.
