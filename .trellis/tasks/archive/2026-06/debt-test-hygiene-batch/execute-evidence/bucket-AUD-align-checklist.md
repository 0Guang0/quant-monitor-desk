# Bucket AUD — Phase A align-checklist

**Branch:** `debt/test-hygiene/bucket-audit-r3x`  
**Phase:** align-ponytail  
**五问：** 1=被测对象 2=验证点 3=失败含义 4=无多余行为 5=复用 helper

## tests/test_audit_fixes.py（7 用例）

| 用例                                                                  | 1   | 2   | 3   | 4   | 5   | ponytail                   |
| --------------------------------------------------------------------- | --- | --- | --- | --- | --- | -------------------------- |
| test_writeManager_defaultTransaction_withDbValidationGate_succeeds    | Y   | Y   | Y   | Y   | Y   | `_market_bar_quality` 去重 |
| test_writeManager_ownTransactionDefault_withDbValidationGate_succeeds | Y   | Y   | Y   | Y   | Y   | 同上                       |
| test_syncJob_invalidStatus_rejectedByDbCheck                          | Y   | Y   | Y   | Y   | Y   | —                          |
| test_apiLimits_enforcesMaxPageSize                                    | Y   | Y   | Y   | Y   | Y   | —                          |
| test_resourceGuard_reusesSnapshotWithinTtl                            | Y   | Y   | Y   | Y   | Y   | —                          |
| test_connection_lowMemoryForcesEcoThreads                             | Y   | Y   | Y   | Y   | Y   | —                          |
| test_resourceGuard_largeCacheDir_completesWithinReasonableTime        | Y   | Y   | Y   | Y   | Y   | `time` 顶栏 import         |

## tests/test_audit_remediation.py（15 用例）

| 用例                                                     | 1   | 2   | 3   | 4   | 5   | ponytail                     |
| -------------------------------------------------------- | --- | --- | --- | --- | --- | ---------------------------- |
| test_validationReport_persistsRuleVersionAndFetchLineage | Y   | Y   | Y   | Y   | Y   | `_patch_guard_ok`            |
| test_sourceConflict_persistsToleranceRuleVersion         | Y   | Y   | Y   | Y   | Y   | 同上                         |
| test_dbRejectsInvalidFetchStatus                         | Y   | Y   | Y   | Y   | Y   | `_migrated_cm`               |
| test_dbRejectsInvalidManualReviewStatus                  | Y   | Y   | Y   | Y   | Y   | 同上                         |
| test_backfillShard_successPath_validatesAndWritesClean   | Y   | Y   | Y   | Y   | Y   | `_BackfillCountAdapter` 顶栏 |
| test_runReconcile_refetchStillDiff_entersManualReview    | Y   | Y   | Y   | Y   | Y   | `_insert_open_conflict`      |
| test_runReconcile_refetchMatches_resolvesByRefetch       | Y   | Y   | Y   | Y   | Y   | 同上                         |
| test_jobEventLog_payloadSchema_isMachineReadable         | Y   | Y   | Y   | Y   | Y   | `_patch_guard_ok`            |
| test_partialSuccess_eachItemWritesAuditEvent             | Y   | Y   | Y   | Y   | Y   | 同上                         |
| test_allowedDomains_dbLoaderRoundTrip                    | Y   | Y   | Y   | Y   | Y   | —                            |
| test_dataQualityLog_persistsRuleVersion                  | Y   | Y   | Y   | Y   | Y   | —                            |
| test_runReconcile_refetchFails_entersManualReview        | Y   | Y   | Y   | Y   | Y   | `_insert_open_conflict`      |
| test_eventPayload_parseMalformed_returnsParseError       | Y   | Y   | Y   | Y   | Y   | —                            |
| test_incrementalJob_emitsItemSuccessEvent                | Y   | Y   | Y   | Y   | Y   | `_patch_guard_ok`            |
| test_backfill_requiresCleanTable                         | Y   | Y   | Y   | Y   | Y   | 同上                         |

## tests/test_r3x_ponytail_pilot_prep_bucket_a.py（10 用例）

| 用例                                                         | 1   | 2   | 3   | 4   | 5   | ponytail             |
| ------------------------------------------------------------ | --- | --- | --- | --- | --- | -------------------- |
| test_ds01_adapterFetchLogDefaultIsNoDbSideEffect             | Y   | Y   | Y   | Y   | Y   | —                    |
| test_ds02_buildAdapterDedupesFactoryPaths                    | Y   | Y   | Y   | Y   | Y   | —                    |
| test_ds03_productionFetchRejectsImplicitTestAdapter          | Y   | Y   | Y   | Y   | Y   | 顶栏 `FetchRequest`  |
| test_sc02_stagedEvidenceRejectsWrongPhase                    | Y   | Y   | Y   | Y   | Y   | 顶栏 duckdb/datetime |
| test_sc02_stagedEvidenceAllowsPhase3Token                    | Y   | Y   | Y   | Y   | Y   | `_test_cm` 单点      |
| test_op02_interfaceProbeUsesMutationProofNotLivePilotPrivate | Y   | Y   | Y   | Y   | Y   | —                    |
| test_sy04_fetchWithGuardUnifiesAdapterAndCallablePaths       | Y   | Y   | Y   | Y   | Y   | `_test_cm`           |
| test_va03_asTextNoneIsNotLiteralString                       | Y   | Y   | Y   | Y   | Y   | —                    |
| test_db03_assertCanWriteSingleEntryWithOptionalCon           | Y   | Y   | Y   | Y   | Y   | —                    |
| test_mutationProof_keyTableCountsEmptyDb                     | Y   | Y   | Y   | Y   | Y   | —                    |

## tests/test_r3x_ponytail_structural_bucket_b.py（18 用例）

| 用例                                                    | 1   | 2   | 3   | 4   | 5   | ponytail                    |
| ------------------------------------------------------- | --- | --- | --- | --- | --- | --------------------------- |
| test_snapshot_lineage_kernel_exports_contract_fields    | Y   | Y   | Y   | Y   | Y   | —                           |
| test_write_manager_rejects_unimplemented_contract_modes | Y   | Y   | Y   | Y   | Y   | `create_test_write_manager` |
| test_health_check_stub_matches_ops_contract_shape       | Y   | Y   | Y   | Y   | Y   | —                           |
| test_live_pilot_modules_under_loc_cap                   | Y   | Y   | Y   | Y   | Y   | `_OPS_DIR`                  |
| test_op03_fetch_port_common_dedupes_recent_window       | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l1_04_resolve_task_sandbox_db_helper               | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l1_06_inventory_lives_under_ops                    | Y   | Y   | Y   | Y   | Y   | `_OPS_DIR`                  |
| test_l1_07_formatters_split_under_ops                   | Y   | Y   | Y   | Y   | Y   | `_LAYER1_DIR`               |
| test_l1_09_with_writer_connection_helper                | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l1_12_axis_loader_observable_defaults_extracted    | Y   | Y   | Y   | Y   | Y   | —                           |
| test_sy02_finalize_staged_on_pipeline_mixin             | Y   | Y   | Y   | Y   | Y   | —                           |
| test_sy06_default_pipeline_config_in_orchestrator       | Y   | Y   | Y   | Y   | Y   | —                           |
| test_sy07_job_transition_extras_table_driven            | Y   | Y   | Y   | Y   | Y   | —                           |
| test_ds04_compat_map_empty                              | Y   | Y   | Y   | Y   | Y   | —                           |
| test_ds06_default_operation_from_capability_registry    | Y   | Y   | Y   | Y   | Y   | —                           |
| test_ds07_source_registry_is_loaded_public_api          | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l2_04_snapshot_writer_module_split                 | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l2_05_staged_observations_helper                   | Y   | Y   | Y   | Y   | Y   | —                           |
| test_l2_06_write_staging_helper                         | Y   | Y   | Y   | Y   | Y   | —                           |

## tests/test_r3x_residual_open_items_closure.py（19 用例）

| 用例                                                      | 1   | 2   | 3   | 4   | 5   | ponytail                   |
| --------------------------------------------------------- | --- | --- | --- | --- | --- | -------------------------- |
| test_advR3xRoute001_validationOnlyPrimaryBlocked          | Y   | Y   | Y   | Y   | Y   | `production_route_planner` |
| test_advR3xRoute003_domainDisabledByDefault               | Y   | Y   | Y   | Y   | Y   | 同上                       |
| test_advR3xRoute004_validationRoleAddsQualityFlag         | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advR3xService001_productionFetchRequiresFileRegistry | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advR3xConflict001_domainAliasThresholdLookup         | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advA2_009_tdxPytdxRegisteredInFactory                | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advA2_004_cninfoSupportsFilingsDomains               | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advA1_001_writeRequestRequiresDataDomain             | Y   | Y   | Y   | Y   | Y   | `_migrated_write_manager`  |
| test_advA5_001_gitignoreSecretPatterns                    | Y   | Y   | Y   | Y   | Y   | `PROJECT_ROOT`             |
| test_advA6_004_viteApiProxy                               | Y   | Y   | Y   | Y   | Y   | 同上                       |
| test_advR3xL1_002_interpretationRejectsForbiddenTerms     | Y   | Y   | Y   | Y   | Y   | 复用 `_history`            |
| test_advR3xCap002_tdxPytdxFactoryParity                   | Y   | Y   | Y   | Y   | Y   | —                          |
| test_defaultOperation_coversAllDomainRoles                | Y   | Y   | Y   | Y   | Y   | `load_yaml`                |
| test_advR3xWrite002_unsupportedWriteModeRejected          | Y   | Y   | Y   | Y   | Y   | `_migrated_write_manager`  |
| test_advA2_002_healthCheckStub                            | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advR3xCap001_compatibilityMapEmpty                   | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advA3_016_orchestratorDeferredRunners                | Y   | Y   | Y   | Y   | Y   | —                          |
| test_advA1_012_minStagingRowsEnforced                     | Y   | Y   | Y   | Y   | Y   | `_migrated_write_manager`  |

**汇总：** 69/69 用例五问全 Y；无注释-代码冲突（见 `bucket-AUD-comment-conflicts.md`）。
