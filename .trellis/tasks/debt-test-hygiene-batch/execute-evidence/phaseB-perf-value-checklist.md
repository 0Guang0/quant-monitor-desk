# Phase B perf-value-checklist

> §1.1 测试价值守恒：所有优化均未删断言、未 mock 网络/live、未缩短验证语义。

| 用例/模块                                                     | 原测试价值（摘自注释）                | 优化手段                                             | 价值仍完整 | network/live |
| ------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------------- | ---------- | ------------ |
| `test_backfillJob_largeRange_splitsIntoTasks`                 | shards≥3；每片≤ECO_MAX；results≥3     | `_BACKFILL_3SHARD_*` 64d 替代 90d（仍≥3 分片）       | Y          | NA           |
| `test_backfillJob_eachShard_callsResourceGuardBeforeFetching` | guard 调用≥3                          | 同上最小 3-shard 区间                                | Y          | NA           |
| `test_backfillJob_midShardFailure_preservesCompletedTasks`    | 部分失败保留已完成分片                | 同上                                                 | Y          | NA           |
| `test_partialSuccess_eachItemWritesAuditEvent`                | events≥3；payload 含 task_id/decision | 同上 backfill 区间                                   | Y          | NA           |
| `test_ingestion_validation_migration` 约束/合法行用例         | DDL CHECK、合法 INSERT、表存在        | module-scoped `validation_module_db`；按 ID 计数断言 | Y          | NA           |
| `test_initDb_runTwice_isIdempotent`                           | 重复 apply 幂等                       | **未改**（仍 per-test fresh DB）                     | Y          | NA           |
| `test_initDb_prodPath_appliesMigration005`                    | ConnectionManager 生产路径            | **未改**                                             | Y          | NA           |
| `test_layer2_sensor_loader` 全模块                            | staged registry 加载                  | `@lru_cache` 只读 fixture 路径                       | Y          | NA           |

## 耗时对比（baseline → Phase B，抽样）

| 用例                                                          | baseline      | Phase B     |
| ------------------------------------------------------------- | ------------- | ----------- |
| `test_backfillJob_largeRange_splitsIntoTasks`                 | 2.30s         | ~2.17s      |
| `test_backfillJob_eachShard_callsResourceGuardBeforeFetching` | 2.30s         | ~2.14s      |
| `test_partialSuccess_eachItemWritesAuditEvent`                | 2.44s         | ~2.08s      |
| `test_ingestion_validation_migration` 多项                    | 1.0–1.4s each | 未进 Top 20 |

## 未做（价值/收益比）

- L23 `conftest` module-scoped `_layer2_cm`（需 MERGE-C 改 conftest；DB 变异用例多）
- `test_batch_d_orchestration_flow` 重复 incremental（注释要求两次 run，不可减）

---

# Phase B 第二轮（B2）

> 逐项分析见 `phaseB2-analysis.md`；耗时见 `phaseB2-pytest-durations.txt`。

| 用例/模块                                                     | 原测试价值                            | 优化手段                                                  | 价值仍完整 |
| ------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------- | ---------- |
| `test_backfillJob_recordsTriggerReason`                       | 1 条 BACKFILL_SHARD 含 trigger_reason | `_BACKFILL_1SHARD_END`（1 分片）                          | Y          |
| `test_backfillJob_midShardFailure_preservesCompletedTasks`    | 第 2 片失败、≥1 completed             | `_BACKFILL_2SHARD_END`（2 分片，非 3）                    | Y          |
| `test_vendorFixtureFetch_e2e*` ×2                             | 真实 orchestrator/service E2E         | `bootstrap_vendor_e2e_db` 共享 migrate+staging+registry   | Y          |
| `test_layer1Ingestion_phase3_phase4_singleFetchLogRegression` | p3/p4 各 fetch_log +1                 | 单 db + `build_staged_fixture_service`，顺序 micro→commit | Y          |

## B2 耗时对比（Phase B → B2，Top 相关项）

| 用例                                    | Phase B | B2                                      |
| --------------------------------------- | ------- | --------------------------------------- |
| `test_backfillJob_recordsTriggerReason` | 1.58s   | 0.98s                                   |
| `test_backfillJob_midShardFailure_*`    | 1.21s   | 1.32s（全 suite 噪声）                  |
| `test_layer1Ingestion_phase3_phase4_*`  | 0.90s   | 跌出 Top 20                             |
| `test_vendorFixtureFetch_e2e*`          | ~1.0s   | ~0.98–1.06s（setup 略减，主路径仍 E2E） |

全量 pytest：**PASS**（exit 0，~124s）
