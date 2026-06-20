# Layer 1 Feature + Interpretation — 测试设计（§8.3–8.4）

## §feature（AC-018-1,2,4,5; AC-RES-1）

| 测试名                                                     | 条件                  | 语义断言                                               |
| ---------------------------------------------------------- | --------------------- | ------------------------------------------------------ |
| `test_axisFeatureEngine_insufficientHistory_noFakeZ`       | valid_obs < min       | `state_bucket=insufficient_history`；z/percentile NULL |
| `test_axisFeatureEngine_robustZUnavailable_whenMadZero`    | MAD=0                 | `robust_z_score` NULL；`ROBUST_Z_UNAVAILABLE`          |
| `test_axisFeatureEngine_sourceSwitched_recordsQualityFlag` | fallback 路径 fixture | `SOURCE_SWITCHED` in quality_flags                     |
| `test_axisFeatureEngine_resourceGuard_ecoProfile`          | mock 低资源           | ResourceGuard 拒绝或 eco 降级                          |
| `test_snapshotRejectsFutureInput`                          | publish > as_of       | 抛错/空快照；no_future_data                            |

字段全集：module §7.1（见 MASTER AC-018-1）。

## §interpretation（AC-018-3,6）

| 测试名                                                | 条件             | 预期                            |
| ----------------------------------------------------- | ---------------- | ------------------------------- |
| `test_axisInterpretation_rejectsForbiddenActionTerms` | 模板含「买入」   | `needs_human_review` 或拒绝写入 |
| `test_layer2ValueCannotWritebackToLayer1`             | 模拟 L2 写 L1 表 | 守卫抛错/拒绝                   |
