# Layer 1 Lineage + WriteManager — 测试设计（§8.5）

## persistence（AC-LINEAGE-1,2）

| 测试名                                          | 断言                                                    |
| ----------------------------------------------- | ------------------------------------------------------- |
| `test_snapshotLineageIncludesAllRequiredFields` | `axis_snapshot_lineage` 行含契约全部 required_fields    |
| `test_snapshotLineageContainsSourceHashes`      | `source_content_hashes` 非空且与 validation_report 一致 |
| `test_incrementalRebuildPreservesAsOfBoundary`  | incremental 重建不越过 as_of                            |

## deterministic + agent（AC-LINEAGE-4）

| 测试名                                                 | 断言                                        |
| ------------------------------------------------------ | ------------------------------------------- |
| `test_snapshotDeterministicRebuild_sameInputsSameHash` | 同 rule_version+parameter_hash → 同业务结果 |
| agent_outputs_not_source                               | `source_dataset_ids` 不含 agent 文本 token  |

## WriteManager（AC-WRIT-1）

| 测试名                                     | 断言                                                                     |
| ------------------------------------------ | ------------------------------------------------------------------------ |
| `test_layer1Snapshot_writeViaWriteManager` | staging→DbValidationGate→WriteManager→clean；`validation_report_id` 必填 |
