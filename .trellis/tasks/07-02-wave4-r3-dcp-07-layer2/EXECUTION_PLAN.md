# EXECUTION_PLAN — R3-DCP-07（薄指针）

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **切片 AC：** `research/to-issues-slices.md`

## Plan GAP（来自 integration-audit）

1. **S00** — `Layer2CleanObservationReader` + registry P0 clean mode + no-fallback guard
2. **S01** — L2-VIX VIXCLS replay clean e2e（ADR-032）
3. **S02** — `ACC-LAYER-E2E-LIVE-001` L2 子集关账 + G2 评级

## 非 Execute 范围

- DCP-05 sync/registry/migration
- Layer1 五轴（DCP-06）
- L2 全资产矩阵 · L3–L5 全链（阶段外置）
- B2.5-O-05
