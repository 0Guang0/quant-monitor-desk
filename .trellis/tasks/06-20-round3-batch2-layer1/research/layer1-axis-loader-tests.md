# Layer 1 Axis Loader — 测试设计（§8.1–8.2）

> Plan 5b · 正文在 research；MASTER 仅保留 tracer 名

## §8.1 migration

| 测试名                                             | fixture           | 语义断言                                                                |
| -------------------------------------------------- | ----------------- | ----------------------------------------------------------------------- |
| `test_layer1Migration_createsRegistryTables`       | temp DB + init_db | `axis_registry`/`axis_indicator_registry`/`axis_indicator_profile` 存在 |
| `test_layer1Migration_createsSnapshotLineageTable` | 同上              | `axis_snapshot_lineage` 存在且含 `rule_version` 列                      |

## §8.2 loader + guardrails

| 测试名                                                             | 条件                         | 预期                                         |
| ------------------------------------------------------------------ | ---------------------------- | -------------------------------------------- |
| `test_axisSpecLoader_loadsFiveAxes`                                | 正常 spec_root               | 五 `axis_id`；indicator 数 > 0               |
| `test_axisSpecLoader_missingIndicatorId_rejects`                   | 删 indicator_id 的 YAML      | loader 抛错/拒绝                             |
| `test_axisSpecLoader_missingQualityRules_rejects`                  | 删 quality_rules 的 YAML     | loader 抛错/拒绝（module §5.3 超集）         |
| `test_axisSpecLoader_forbiddenIndicator_notObservable`             | forbidden 指标               | `is_observable=false`；无 observation writer |
| `test_axisSpecLoader_blindspot_notObservable`                      | blindspot 指标               | 仅 registry；不可观测                        |
| `test_axisEngineeringGuardrail_rejectsForbiddenSubstitute`         | 触发 forbidden_substitute    | 阻断 + quality 错误                          |
| `test_layer1ShadowDiagnostics_areExplicitlyAllowedButNoTakeover`   | liquidity shadow_diagnostics | 允许诊断；`no_takeover`                      |
| `test_shadowDiagnosticLabels_doNotEnterSourceRegistryRoles`        | SHADOW 标签                  | 不进 source_registry 角色字段                |
| `test_shadowDiagnosticsOutsideGroup_requireExplicitDiagnosticOnly` | SHADOW 不在分组              | 须 `diagnostic_only` 或同等                  |
