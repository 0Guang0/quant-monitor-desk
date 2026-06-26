# Original plan trace — R3FR_05 → EXECUTION_INDEX

| 活任务卡             | AC     | Step    | 测试                                                                  |
| -------------------- | ------ | ------- | --------------------------------------------------------------------- |
| §4 全量条目          | AC-1   | 9.2     | test_everyRegistrySource_hasCatalogEntry                              |
| §4 字段              | AC-1,2 | 9.1,9.2 | test_catalogRequiredFields_present                                    |
| §5 enum              | AC-2   | 9.2     | test_catalogEnums_matchSchemaCheck                                    |
| §5 production fields | AC-3   | 9.2     | test_productionDefaultCandidate_distinctFromEnabled                   |
| §5 proposed external | AC-3   | 9.2     | test_proposedExternalSources_notProductionEnabled                     |
| §5 fred/TDX/QMT      | AC-4   | 9.2     | test_fredAndLocalTerminalPosture                                      |
| §5 openbb            | AC-5   | 9.5     | test_openbbReference_noRuntimeCopy, test_r3fr05ProviderCatalogClosure |
| §3 contracts         | AC-7   | 9.4     | test_provider_catalog_contractRefs                                    |
| §5 gates             | AC-6   | 9.6     | full pytest + loop --fix                                              |
| capability 对齐      | —      | 9.2     | test_catalogStatus_matchesCapabilityRegistry                          |
| registry 对齐        | —      | 9.2     | test_catalogEnabledByDefault_notLooserThanRegistry                    |
