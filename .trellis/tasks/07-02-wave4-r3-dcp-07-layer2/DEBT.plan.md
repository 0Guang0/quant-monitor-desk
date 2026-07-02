# DEBT.plan — 07-02-wave4-r3-dcp-07-layer2

> Plan v4.1 complex · **无新 migration**

## Source of truth

- **规划 ID:** R3-DCP-07
- **活卡:** `R3_DCP_07_LAYER2_CROSS_ASSET.md`
- **INDEX:** `R3_DCP_TO_ISSUES_INDEX.md` §6.3
- **base branch:** `master`
- **target branch:** `feature/wave4-r3-dcp-07-layer2`
- **worktree:** `../quant-monitor-desk-wt-dcp07`

## Boundary

### allowed files

```text
backend/app/layer2_sensors/**
# Execute 新建: tests/test_layer2_*_clean_e2e.py, test_layer2CleanReader_*
docs/decisions/ADR-032-dcp07-layer2-vix-clean-read.md
docs/quality/待修复清单.md          # S02 台账行（主会话）
MODULE_COMPLETION_RATING.md         # S02 G2 评级（主会话）
.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/**
```

### forbidden files

```text
backend/app/sync/incremental_source_registry.py
backend/app/sync/watermark.py
backend/app/ops/sandbox_clean_write/clean_write_targets.py
backend/app/ops/*_incremental_*.py    # DCP-05 所有权
backend/app/datasources/fetch_ports/*.py
backend/app/datasources/adapters/*.py   # DCP-05 按源切片；本轨只读参考
backend/app/db/migrations/**
backend/app/layer1_axes/**            # DCP-06 所有权（只读参考）
backend/app/cli/data_commands.py      # DCP-05 所有权
```

## 阶段外置（S02 登记）

| ID | 路由 |
|----|------|
| `ACC-LAYER-E2E-LIVE-001` L3–L5 | DCP-08/10 + R3H-05-GATE |
| L2-HYG / security_bar_1d 第二传感器 | Wave 5+ |
| L2 全 staging→clean pipeline | Batch 4/5 task 020–022 |
| `B2.5-O-05` | Wave 5 R3F-SH-06 |
