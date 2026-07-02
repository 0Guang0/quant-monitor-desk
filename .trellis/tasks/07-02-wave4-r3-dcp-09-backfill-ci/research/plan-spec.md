# Plan Spec — R3-DCP-09

## Objective

Operator 可通过 `qmd data backfill` 跑 **有界** backfill；CI nightly 跑连网子集与 live acceptance。

## Tech Stack

Python 3.11 · Typer/Click CLI（沿用 `data_commands`）· pytest · GitHub Actions

## Commands

```bash
# 本地 replay（隔离库）
uv run python -m backend.app.cli.main data backfill \
  --domain cn_equity_daily_bar \
  --source-id baostock \
  --start 2026-05-01 --end 2026-06-15 \
  --max-shards 3 \
  --dry-run

# nightly 本地复现（须 env）
uv run pytest -q -m network \
  tests/test_batch275_live_pilot_gate.py::test_livePilot_phase3RawOnly_threeRequestsLive

uv run python scripts/wave3_isolated_production_acceptance.py --quick
uv run python scripts/wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL
```

## Project Structure

```text
specs/contracts/bounded_backfill_cap.yaml   # cap SSOT
backend/app/sync/jobs.py                    # plan_backfill_shards + max_shards
backend/app/cli/data_commands.py            # backfill command
.github/workflows/nightly.yml               # scheduled network CI
docs/ops/nightly_ci.md                      # 可执行入口文档
scripts/wave3_*_production_acceptance.py    # quick + findings gate
```

## Testing Strategy

- S00：unit — shard cap 边界
- S01–S02：CLI + replay e2e（mock fetch / 隔离 `QMD_DATA_ROOT`）
- S03–S05：脚本 profile 契约测（不默认跑真网）
- 收尾：`uv run pytest -q`

## Boundaries

**In scope：** 有界 backfill CLI；quick profile；nightly workflow；findings severity gate

**Out of scope：** 无 cap FullLoad；24 源 cron；Tier B/C backfill 矩阵；FRED live primary

## Success Criteria

活卡 §5 全勾 · 四台账关账 · `validate-plan-freeze` exit 0

## ASSUMPTIONS

- 首域 pilot：`cn_equity_daily_bar` + baostock（DCP-05 已通 incremental）
- `ECO_MAX_BACKFILL_DAYS_PER_TASK=31` 保持不变
- PR `ci.yml` 不增加 `--run-network`（仅 nightly）
