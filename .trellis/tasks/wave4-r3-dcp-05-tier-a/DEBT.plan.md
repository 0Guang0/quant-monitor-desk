# DEBT.plan — wave4-r3-dcp-05-tier-a

> Plan v4.1 复杂轨 · 含 migration 015（ADR-028）  
> **用户裁决：** 11/11 Tier A clean upsert

## Source of truth

- **规划 ID:** R3-DCP-05
- **活卡:** `R3_DCP_05_TIER_A_INCREMENTAL.md`
- **INDEX:** `R3_DCP_TO_ISSUES_INDEX.md` §7
- **base branch:** `master`
- **target branch:** `feature/wave4-r3-dcp-05-tier-a`
- **worktree:** `../quant-monitor-desk-wt-dcp05`

## Boundary

### allowed files

```text
backend/app/db/migrations/015_dcp05_tier_a_clean.sql
backend/app/sync/incremental_source_registry.py
backend/app/sync/watermark.py
backend/app/ops/*_incremental_*.py
backend/app/ops/sandbox_clean_write/clean_write_targets.py
backend/app/cli/data_commands.py
backend/app/cli/main.py
backend/app/datasources/fetch_ports/*.py          # 按源切片
backend/app/datasources/adapters/*.py             # 按源切片
tests/test_*incremental*
tests/test_qmd_data_sync_*
tests/test_schema_migration.py                    # 若 015 触发
tests/test_catalog.yaml
docs/schema/MIGRATION_COVERAGE.md
docs/decisions/ADR-028-*.md
docs/architecture/06_deployment_and_local_ops.md  # S13
specs/datasource_registry/*.yaml                  # 主会话 S13
.trellis/tasks/wave4-r3-dcp-05-tier-a/**
```

### forbidden files

```text
backend/app/layer1_axes/**                        # DCP-06
backend/app/sync/orchestrator.py                  # 共享；仅协调极小补丁
data/duckdb/quant_monitor.duckdb
参考项目/**
```

### production/data boundary

- `--no-dry-run` 仅隔离 `QMD_DATA_ROOT`
- Live：`QMD_ALLOW_LIVE_FETCH=1` + 源 key
- 禁止 canonical 主库 silent 写

### explicit non-goals

- FRED live primary（B2.5-O-05）
- 五轴 G12（DCP-06）
- Tier B/C 增量

## Vertical slices

见 `research/to-issues-slices.md` S00–S13（SSOT）。

## Merge gate

```bash
uv run pytest tests/test_*incremental* tests/test_qmd_data_sync_tier_a_router.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py
```

## Execute Boot 必读

1. `research/00-EXECUTION-ENTRY.md`
2. `research/to-issues-slices.md`
3. `research/reference-adoption-dcp05.md`
4. ADR-028
5. `EXTERNAL-INDEX.md` §D → `execute-reference-read-evidence.md`（RED 前）
