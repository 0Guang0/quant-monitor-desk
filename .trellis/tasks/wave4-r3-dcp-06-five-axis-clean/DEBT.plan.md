# DEBT.plan — wave4-r3-dcp-06-five-axis-clean

> Plan v4.1 complex · **无新 migration**

## Source of truth

- **规划 ID:** R3-DCP-06
- **活卡:** `R3_DCP_06_LAYER1_FIVE_AXIS_CLEAN.md`
- **INDEX:** `R3_DCP_TO_ISSUES_INDEX.md` §6.2
- **base branch:** `master`
- **target branch:** `feature/wave4-r3-dcp-06-five-axis-clean`
- **worktree:** `../quant-monitor-desk-wt-dcp06`

## Boundary

### allowed files

```text
backend/app/layer1_axes/**
# Execute 新建: tests/test_layer1_*_clean_e2e.py, test_layer1_five_axis_panel_clean_smoke.py
specs/model_inputs/layer1_source_whitelist.yaml
docs/decisions/ADR-029-*.md
docs/quality/待修复清单.md          # S06 台账行（主会话）
MODULE_COMPLETION_RATING.md         # S06 评级（主会话）
.trellis/tasks/wave4-r3-dcp-06-five-axis-clean/**
```

### forbidden files

```text
backend/app/sync/incremental_source_registry.py
backend/app/ops/sandbox_clean_write/clean_write_targets.py
backend/app/db/migrations/**
backend/app/cli/data_commands.py      # DCP-05 所有权
```

## 阶段外置（S06 登记）

| ID                             | 路由                       |
| ------------------------------ | -------------------------- |
| `ACC-LAYER-E2E-LIVE-001` L3–L5 | DCP-07/08/10 + R3H-05-GATE |
| tiingo 流动性主路径            | Batch 6+                   |
| `B2.5-O-05`                    | Wave 5 R3F-SH-06           |
