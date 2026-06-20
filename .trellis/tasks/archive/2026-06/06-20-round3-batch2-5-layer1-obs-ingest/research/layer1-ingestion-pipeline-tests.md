# Layer 1 Ingestion Pipeline Tests (Phase 1–4 Execute)

> Plan 5b · 018A §8 Phase 1–4

## Phase 1 — read-only inventory（8.2）

| 测试名                                                                    | 语义                                        |
| ------------------------------------------------------------------------- | ------------------------------------------- |
| `test_layer1Ingestion_phase1_inventory_readOnly`                          | 只读 open；产出 inventory json/md           |
| `test_layer1Ingestion_phase1_inventory_requiredTableKeys`                 | 含 018A §8 Phase 1 关键表行数字段           |
| `test_layer1Ingestion_phase1_zeroMutation`                                | 前后 hash/行数 + data-root fingerprint 不变 |
| `test_layer1Ingestion_phase1_copyProvenanceWhenSandbox`                   | sandbox copy 时含 source/checksum           |
| `test_layer1Ingestion_phase1_classify_fixtureOrStagedEvidence`            | fetch_log → fixture/staged + gate 阻断      |
| `test_layer1Ingestion_phase1_classify_productionLikeData`                 | axis_observation → production + gate 阻断   |
| `test_layer1Ingestion_phase1_classify_userProvidedData`                   | file_registry 无 fetch → user_provided      |
| `test_layer1Ingestion_phase1_phase2Gate_blocksUntilReview`                | 018A stop 规则矩阵                          |
| `test_layer1Ingestion_phase1_captureDoesNotCallWriterOrMigrations`        | safety_invariants                           |
| `test_layer1Ingestion_phase1_taskEvidenceUsesProjectTargetPaths`          | QMD_DATA_ROOT 目标路径 + synthetic baseline |
| `test_layer1Ingestion_phase1_taskEvidenceSandboxCopyPath`                 | 目标 DB 存在时 sandbox copy + provenance    |
| `test_layer1Ingestion_phase1_enrichedInventory_hasRegistryAndFileSamples` | source_registry 快照 + data_root 文件样本   |
| `test_layer1Ingestion_phase1_operatorMemoFlipsPhase2Gate`                 | 分类 memo 翻转 `phase2_authorized`          |
| `test_layer1Ingestion_phase1_warnStatusDoesNotImplyUnsafeWhenSchemaOnly`  | WARN 与 Phase 2 授权解耦                    |

## Phase 2 — route preview（8.3）

| 测试名                                                                           | 语义                                               |
| -------------------------------------------------------------------------------- | -------------------------------------------------- |
| `test_layer1Ingestion_routePreview_noMutation`                                   | dry-run 前后 `axis_observation`/fetch_log 行数不变 |
| `test_layer1Ingestion_forbiddenIndicator_rejectedBeforeRoute`                    | forbidden 不进 route                               |
| `test_layer1Ingestion_blindspot_rejectedBeforeFetch`                             | blindspot 不进 fetch                               |
| `test_layer1Ingestion_disabledSource_returnsRouteStatusWithoutFetch`             | DISABLED_SOURCE / USER_AUTH_REQUIRED               |
| `test_layer1Ingestion_noSilentFallback`                                          | route 含 skip reason                               |
| `test_layer1Ingestion_routePreview_capabilityDeclaredForSelectedSource`          | capability registry gate (018A step 5)             |
| `test_layer1Ingestion_routePreview_resourceGuardPauseDocumentsStopReason`        | ResourceGuard PAUSE documented                     |
| `test_layer1Ingestion_phase2TaskEvidence_requiresPhase1GateWhenInventoryPresent` | phase2_gate blocks task evidence                   |

## Phase 3 — micro-fetch staging（8.4）

| 测试名                                                             | 语义                              |
| ------------------------------------------------------------------ | --------------------------------- |
| `test_layer1MicroIngestion_usesDataSourceServiceBeforeFetch`       | 经 service 非 layer1 直调 adapter |
| `test_layer1MicroIngestion_persistsRoutePlanBeforeFetch`           | route evidence 先于 fetch_log     |
| `test_layer1MicroIngestion_writesFetchLogAndRawEvidence`           | fetch_log + file_registry delta   |
| `test_layer1MicroIngestion_phase3DoesNotWriteCleanAxisObservation` | `axis_observation` 不变           |
| `test_layer1MicroIngestion_resourceGuardPauseStopsBeforeFetch`     | guard pause 阻断                  |

## Phase 4 — clean write + snapshots（8.5）

**Prerequisite tests（018A §8 Phase 4 — 须保持绿）：**

```bash
uv run pytest tests/test_write_manager.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q
```

| 测试名                                                          | 语义                          |
| --------------------------------------------------------------- | ----------------------------- |
| `test_layer1Observation_cleanWrite_requiresValidationReport`    | 无 validation_report 拒绝     |
| `test_layer1Observation_cleanWrite_usesWriteManager`            | write_audit_log 有记录        |
| `test_layer1Observation_validationFailure_blocksCleanWrite`     | 失败阻断                      |
| `test_layer1Observation_severeConflict_blocksCleanWrite`        | severe 阻断                   |
| `test_layer1Observation_manualReview_blocksNonManualPatchWrite` | manual review 阻断            |
| `test_layer1Observation_lineageIncludesFetchIdsAndHashes`       | lineage 非空 fetch ids/hashes |
| `test_layer1Observation_noFutureDataRejected`                   | as_of 安全                    |
| `test_layer1Observation_forbiddenAndBlindspotNeverPersisted`    | 持久化边界                    |
| `test_layer1Observation_postInspectShowsExpectedDeltasOnly`     | inspect delta                 |

## Fixture 策略

- 默认：`tests/fixtures/layer1_macro_observation_fixture.json`（Execute 新建）+ `FixtureFetchPort` / `macro_supplementary.fetch_macro_series`
- Live：仅 MASTER 记录用户授权路径时启用
