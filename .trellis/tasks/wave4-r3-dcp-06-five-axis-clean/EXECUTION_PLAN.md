# EXECUTION_PLAN — R3-DCP-06（薄指针）

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **切片 AC：** `research/to-issues-slices.md`

## Plan GAP（来自 integration-audit）

1. **S00** — `Layer1CleanObservationReader` + no-fallback guard
2. **S01–S05** — 五轴 replay clean e2e（ADR-029 P0 锚点）
3. **S06** — 集成 smoke + K1 + `ACC-LAYER-E2E-LIVE-001` L1 子集关账

## 非 Execute 范围

- DCP-05 sync/registry/migration
- B2.5-O-05 · L3–L5 全链（阶段外置）
