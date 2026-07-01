# Lineage cluster test-depth report (R3Y-TEST-DEPTH-001 / AUD-07 L05)

**Scope:** lineage 簇 only — not full PROMPT_15 73-item umbrella.

## Runtime-strong (upgraded this Execute)

| ID / gap                       | Test                                                                                                    | Depth                                                               |
| ------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| R3-B6-021-O-01                 | `test_layer3Snapshot_malformedBarElement_rejects`                                                       | Runtime-strong — build path raises on non-dict `bars[]`             |
| R3-B6-021-O-02                 | `test_layer3Snapshot_deterministicRebuild_sameInputsSameHash`                                           | Runtime-strong — full row tuple + lineage fields                    |
| ADV-R3X-LINEAGE-001 (contract) | `test_layer3Lineage_rejectsEmpty*`, `test_marketSnapshot_lineageUpstreamFromLayer3`                     | Runtime-strong — builder API + L3→L4 propagation                    |
| R3Y-LINEAGE-VR-001             | `test_layer2Snapshot_lineageIncludesFetchIdsAndHashes`, `test_layer2Snapshot_lineageVrMismatch_rejects` | Runtime-strong — WM write + DB `axis_snapshot_lineage` JSON columns |
| OPEN-05 roll writer gate       | `test_layer2RollEvent_rejectsMissingValidationReport`                                                   | Runtime-strong negative — missing VR fail-closed                    |
| AUD-07 L05-W1 (L2 VR drift)    | `test_layer2Snapshot_lineageVrMismatch_rejects`                                                         | **New** runtime-strong negative                                     |

## Already runtime-strong (pre-existing, unchanged)

| Test                                                      | Notes            |
| --------------------------------------------------------- | ---------------- |
| `test_layer1Observation_lineageIncludesFetchIdsAndHashes` | L1 E2E reference |
| `test_layer3Snapshot_lineageRequiredFieldsComplete`       | L3 staged build  |
| `test_marketSnapshot_lineageRequiredFieldsComplete`       | L4 staged build  |
| `test_snapshot_lineage_kernel.py`                         | Shared kernel    |

## Wont-fix (out of B01-LIN boundary)

| ID / gap                                               | Owner                | Rationale                                           |
| ------------------------------------------------------ | -------------------- | --------------------------------------------------- |
| ADV-R3X-SYNC-001                                       | Batch 6 / sync track | Not lineage cluster                                 |
| PROMPT*15 structural umbrella (`test_r3x_residual*\*`) | Main session         | AUD-07 scope explicitly excludes expanding umbrella |
| L5 lineage / evidence foundation depth                 | B01-023              | `layer5_evidence/**` forbidden to B01-LIN           |
| ADV-R3X-LINEAGE-001 DB write-back E2E                  | B01-023              | Migration + L5 track                                |
| CAP/mutation structural tests                          | Other Batch 6 agents | Listed wont-fix per DEBT.plan LIN-S5                |

## AUD-07 L05-W2

Addressed by pairing positive DB read (`lineageIncludesFetchIdsAndHashes`) with negative VR mismatch — satisfies «at least 1 new runtime-strong or documented wont-fix» for lineage gaps.
