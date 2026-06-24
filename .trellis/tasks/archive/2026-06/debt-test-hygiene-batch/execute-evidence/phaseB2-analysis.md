# Phase B 第二轮 — Top 20 逐项深度分析

> 约束：§1.1 测试价值守恒；/ponytail — 只减 setup 冗余或缩至注释允许的最小区间，不删断言、不 mock 网络/live、不弱 E2E。

## 图例

| 标记        | 含义                                     |
| ----------- | ---------------------------------------- |
| ✅ 可优化   | 有明确 ponytail 手段且语义不变           |
| ⚠️ 边际     | 理论可动但收益 < 全 suite 噪声或改动面大 |
| ❌ 不可优化 | 注释/语义锁死完整路径                    |

---

## Top 20 逐项

| #   | 用例                                                                          | 耗时  | 判定 | 理由                                                                                                |
| --- | ----------------------------------------------------------------------------- | ----- | ---- | --------------------------------------------------------------------------------------------------- |
| 1   | `test_partialSuccess_eachItemWritesAuditEvent`                                | 2.25s | ❌   | 注释要求 events≥3、多分片 audit；已用 `_BACKFILL_3SHARD_*`（≥3 分片最小 64d）                       |
| 2   | `test_backfillJob_eachShard_callsResourceGuardBeforeFetching`                 | 2.21s | ❌   | 注释 guard 调用 ≥3；必须 ≥3 分片                                                                    |
| 3   | `test_backfillJob_largeRange_splitsIntoTasks`                                 | 2.20s | ❌   | 注释 shards≥3、results≥3；已最小化                                                                  |
| 4   | `test_incrementalJob_repeatRun_noDuplicatePrimaryKey`                         | 1.73s | ❌   | 注释要求连续两次 incremental run；减 run 次数即改测试目的                                           |
| 5   | `test_backfillJob_recordsTriggerReason`                                       | 1.58s | ✅   | 只需 1 条 BACKFILL_SHARD 含 trigger_reason；当前 Feb15=2 分片，可缩至 Jan15=1 分片                  |
| 6   | `test_backfillJob_midShardFailure_preservesCompletedTasks`                    | 1.21s | ✅   | `_BackfillFailOnSecondAdapter` 第 2 次失败；2 分片（Jan1–Feb15）足够，不必 3 分片                   |
| 7   | `test_validationReport_persistsRuleVersionAndFetchLineage`                    | 1.00s | ❌   | 完整 incremental E2E + 校验报告字段；无冗余 setup                                                   |
| 8   | `test_vendorFixtureFetch_e2eThroughDataSourceServicePath`                     | 1.00s | ✅   | migrate+staging+registry 与 #9 重复模式；提取共享 bootstrap                                         |
| 9   | `test_backfillShard_successPath_validatesAndWritesClean`                      | 0.99s | ⚠️   | 单次 backfill 分片 E2E；已 1 月区间，边际低                                                         |
| 10  | `test_vendorFixtureFetch_e2eOrchestratorPath`                                 | 0.98s | ✅   | 同 #8，共享 bootstrap                                                                               |
| 11  | `test_incrementalJob_happyPath_writesCleanAndCompletes`                       | 0.98s | ❌   | batch_d 完整 happy path；两次 DB 写+校验不可省                                                      |
| 12  | `test_jobEventLog_payloadSchema_isMachineReadable`                            | 0.96s | ❌   | 事件 schema 回归；完整 orchestrator 路径                                                            |
| 13  | `test_incrementalJob_emitsItemSuccessEvent`                                   | 0.95s | ❌   | 单次 incremental 事件链；无多余分片                                                                 |
| 14  | `test_layer1Ingestion_phase3_phase4_singleFetchLogRegression`                 | 0.90s | ✅   | 两次 `_init_db`（phase3.duckdb + phase4.duckdb）；同一 service+db 顺序 p3→p4 仍满足 fetch_log 各 +1 |
| 15  | `test_plannedJobWritesRoutePlanBeforeFetching`                                | 0.90s | ⚠️   | 真实 planned job 路径；~0.9s 接近噪声                                                               |
| 16  | `test_contextRouter_cli_taskFlag_writesContextPack`                           | 0.88s | ❌   | 注释要求真实 subprocess CLI；不可 mock                                                              |
| 17  | `test_backfillJob_severeConflict_blocksCleanWriteAndPersistsConflictReportId` | 0.86s | ⚠️   | 已 Jan1–Jan15 单分片；冲突校验路径固有成本                                                          |
| 18  | `test_layer1Ingestion_phase4_taskEvidenceArtifacts`                           | 0.85s | ❌   | `@pytest.mark.slow` 完整 evidence 管道                                                              |
| 19  | `test_r3ySync001_testHookAllowsAdapterBypassUnderPytest`                      | 0.84s | ⚠️   | hook 语义需真实 orchestrator；收益低                                                                |
| 20  | `test_sourceConflict_persistsToleranceRuleVersion`                            | 0.82s | ⚠️   | 冲突持久化 E2E；已较 lean                                                                           |

---

## 本轮实施（✅ 项）

1. **backfill 常量分层**：`_BACKFILL_1SHARD_END`（trigger reason）、`_BACKFILL_2SHARD_END`（mid-shard failure）；保留 `_BACKFILL_3SHARD_*` 给 ≥3 断言族。
2. **vendor E2E**：`service_path_support.bootstrap_vendor_e2e_db` — 一次 migrate + staging + registry sync。
3. **layer1 phase3+4**：单 db + `build_staged_fixture_service` datasource，顺序 micro_fetch → commit。

## 明确不做

- 减 `repeatRun` 的 run 次数、减 ≥3 分片 backfill 断言、module-scoped 污染性 DB fixture（L23 conftest）、mock vendor/orchestrator 主路径。
