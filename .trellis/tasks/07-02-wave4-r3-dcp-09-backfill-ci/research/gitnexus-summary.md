# GitNexus 1b — R3-DCP-09 冲击面

> **impact：** `plan_backfill_shards` · `BackfillShardRunner`  
> **risk：** LOW（direct 2 · processes 1）

---

## plan_backfill_shards

| 深度 | 调用方                              | 风险     |
| ---- | ----------------------------------- | -------- |
| d=1  | `BackfillShardRunner.run`           | **WILL** |
| d=1  | `production_equivalent_smoke._collect_scale_metrics` | 指标 only |
| d=2  | `production_equivalent_smoke.main`  | smoke CI |

**变更建议：** 新增 `max_shards` 参数时保持默认行为不变（仅 CLI 传 cap）；impact LOW。

## BackfillShardRunner

| 入站                     | 说明           |
| ------------------------ | -------------- |
| `orchestrator.py`        | 唯一生产入口   |
| `test_sync_orchestrator` | 分片/断点/冲突 |
| structural bucket tests    | mixin 契约     |

## Execute 触点（预计）

| 文件                                          | 切片        |
| --------------------------------------------- | ----------- |
| `backend/app/sync/jobs.py`                    | S00         |
| `backend/app/cli/data_commands.py`            | S01         |
| `specs/contracts/bounded_backfill_cap.yaml`   | S00         |
| `scripts/wave3_isolated_production_acceptance.py` | S03     |
| `.github/workflows/nightly.yml`               | S04         |
| `scripts/wave3_live_production_acceptance.py` | S05         |
| `docs/ops/nightly_ci.md`                      | S04         |
| test_bounded_backfill_cli_e2e（Execute 新建） | S02         |

**警告：** 无 HIGH/CRITICAL；改 `plan_backfill_shards` 签名前须复跑 `test_sync_orchestrator` + smoke budget 测。
