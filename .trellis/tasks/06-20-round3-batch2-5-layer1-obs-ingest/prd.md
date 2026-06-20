# Round 3 Batch 2.5: Layer 1 observation ingestion bridge

## Goal

五阶段受控桥接：staged/授权源 → `axis_observation` → snapshots → lineage（`R3-B2.5-L1-OBS-INGEST` / `018A`）。

## Requirements

- Trellis complex task；Execute 五阶段 + Audit A0–A4 串行签字。
- DataSourceService + WriteManager + validators；禁止 Layer1→adapter。
- 默认 staged/fixture；禁止默认 live QMT/Yahoo/FRED。
- 微摄取：单指标、单 as_of 窗口。

## Acceptance Criteria

- [x] AC-PRE — 前置 gate（Plan 冻结）
- [x] AC-P0-1..4 — Phase 0 contract gate（MASTER §2）
- [x] AC-P1-1..2 — 只读 inventory
- [x] AC-P2-1..3 — route dry-run 无 mutation
- [x] AC-P3-1..3 — micro-fetch staging only
- [x] AC-P4-1..5 — clean write + snapshots + lineage
- [x] AC-TRACE-1, AC-HANDOFF-1, AC-REG-1, AC-GATE

## Notes

- Plan 冻结完成；下一步：对抗审计 → validate-plan-freeze → 用户批准 → Execute。
- 详见 `MASTER.plan.md`、`AUDIT.plan.md`。
