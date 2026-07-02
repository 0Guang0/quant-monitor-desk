# GitNexus 1a — R3-DCP-09 子系统概览

> **Query：** backfill shard runner CLI orchestrator  
> **日期：** 2026-07-02

---

## 相关子系统

| 簇            | 符号 / 路径                         | 角色                                   |
| ------------- | ----------------------------------- | -------------------------------------- |
| Sync jobs     | `plan_backfill_shards`              | 日期窗 → task 分片（31 天/片）         |
| Sync runners  | `BackfillShardRunner`               | 分片 fetch → validate → write          |
| Orchestrator  | `DataSyncOrchestrator.run_backfill` | 金路径入口；fail-closed service        |
| CLI           | `data_commands.py`                  | 现有 `sync`；**缺 `backfill` 子命令** |
| Smoke budget  | `production_equivalent_smoke.py`    | shard_count_benchmark 门禁             |
| Wave3 验收    | `wave3_*_production_acceptance.py`  | 隔离库全链；live 连网 profile          |
| CI            | `.github/workflows/ci.yml`          | PR 默认无 network；**缺 nightly**      |

## 执行流（现状）

```text
tests/test_sync_orchestrator.py
  → DataSyncOrchestrator.run_backfill(spec, datasource_service=...)
    → BackfillShardRunner.run
      → plan_backfill_shards(date_start, date_end)  # max_days=31
      → per-shard FetchRequest + ResourceGuard
```

**缺口：** 无 operator CLI；无 invocation-level shard cap；验收脚本无 quick；CI 未接 nightly network。

## 模块边界

- Orchestrator **不**直接写 clean；经 `SyncWritePipeline`
- Production profile **禁止** adapter bypass（`guard_production_datasource_service_required`）
- 主库 `data/duckdb/` 禁止 silent 写（验收脚本 fingerprint 门禁）
