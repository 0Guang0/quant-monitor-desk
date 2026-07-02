# ADR-030: Bounded Backfill Cap and CI Nightly Layering

**Status:** Accepted  
**Date:** 2026-07-02  
**Task:** R3-DCP-09

## Context

增量路径（DCP-01/02/05）已通，但 backfill 仅有 runner 层 `plan_backfill_shards`（31 天/片），缺少：

1. Operator 可执行的 `qmd data backfill` CLI
2. 单次 invocation 的 shard 数量上限（防无界 FullLoad）
3. Wave 3 验收脚本 CI 分层（quick vs nightly network）
4. `wave3_live_production_acceptance.py` findings 硬门禁

台账：`WAVE3-ACC-OPT-01` · `ACC-LIVE-NETWORK-CI-001` · `ACC-LIVE-ACCEPT-NIGHTLY-001` · `LIVE-NETWORK-GATE-001`

## Decision

### 1. 双层 cap

| 层               | 常量 / 参数                      | 默认   |
| ---------------- | -------------------------------- | ------ |
| Per-shard window | `ECO_MAX_BACKFILL_DAYS_PER_TASK` | **31** |
| Per-invocation   | `DEFAULT_MAX_BACKFILL_SHARDS`    | **3**  |
| Hard ceiling     | `ABSOLUTE_MAX_BACKFILL_SHARDS`   | **12** |

- SSOT：`specs/contracts/bounded_backfill_cap.yaml`
- `plan_backfill_shards` 增加可选 `max_shards`；超出时默认 **fail-closed**（`CliFailure`）
- 显式 `--truncate-to-cap` 可截断 `date_end` 至 cap 覆盖范围（须审计日志）

### 2. CLI 金路径

```bash
qmd data backfill --domain cn_equity_daily_bar --source-id baostock \
  --start YYYY-MM-DD --end YYYY-MM-DD [--max-shards N] [--dry-run]
```

- 非 dry-run：须 `QMD_ALLOW_LIVE_FETCH` + 隔离 `QMD_DATA_ROOT` 或 operator 授权
- 调用 `DataSyncOrchestrator.run_backfill` + `DataSourceService`（ADR-025）
- Pilot 首域：`cn_equity_daily_bar`；其余 Tier A 扩展留 Batch 6

### 3. CI nightly 分层

| Profile | 入口                                              | 何时           |
| ------- | ------------------------------------------------- | -------------- |
| PR      | `.github/workflows/ci.yml`（无 `--run-network`）  | 每次 push/PR   |
| Quick   | `wave3_isolated_production_acceptance.py --quick` | PR 可选 / 本地 |
| Nightly | `.github/workflows/nightly.yml`                   | cron + manual  |

Nightly 步骤：

1. `pytest -q -m network tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive`
2. `python scripts/wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL`

文档 SSOT：`docs/ops/nightly_ci.md`

### 4. Findings 门禁

- `--fail-on-severity` 逗号列表；默认 nightly 用 `HIGH,CRITICAL`
- `plan_alignment` 中 `EXPECTED_DEFER` 不触发 exit 1
- `LIVE-ACC-MAIN-DB-POLLUTION` 始终 CRITICAL

## Alternatives Considered

1. **Runner 内硬 cap** — 拒绝：冲击 `BackfillShardRunner` 契约面大
2. **仅文档 nightly** — 拒绝：易漂移；活卡要求可执行 CI
3. **PR 跑 network** — 拒绝：flake 阻塞合并；nightly 专责

## Consequences

- Execute S00–S06 按 `to-issues-slices.md` 交付
- `production_equivalent_smoke` shard benchmark 与 cap 默认对齐
- 无 cap FullLoad 仍为 Batch 6 non-goal
