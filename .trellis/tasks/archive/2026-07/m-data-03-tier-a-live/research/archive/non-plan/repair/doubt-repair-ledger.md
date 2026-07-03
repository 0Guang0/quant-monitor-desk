# Doubt Repair Ledger — M-DATA-03 R2（回滚后）

> **SSOT：** `research/doubt-repair-m-data-03.md`  
> **R1 关账：** 2026-07-03 — **已作废**（partial F0 + SKIP 与用户 R4 口径冲突）  
> **R2 建账：** 2026-07-03 — 全部 **待修复** 直至 R2 AC 满足

| ID    | P   | Area                | disposition | 证据 / 关闭条件                                     |
| ----- | --- | ------------------- | ----------- | --------------------------------------------------- |
| R2-01 | P0  | F0 full / no SKIP   | 待修复      | 四族 profile 绿；无 `_run_f0_data_health` skip pass |
| R2-02 | P0  | B2 R4 main path     | 待修复      | 11 源 validate_table + MCR B2 R4                    |
| R2-03 | P0  | Evidence contract   | 待修复      | `live_tier_a_evidence_v1.yaml` 实现 + 契约测        |
| R2-04 | P1  | Dispatch dedup      | 待修复      | 无平行 registry；GitNexus impact                    |
| R2-05 | P1  | CI regression       | 待修复      | nightly quick + workflow_dispatch + artifact        |
| R2-06 | P1  | mootdx matrix       | 待修复      | platform_source_matrix + 无 bypass                  |
| R2-07 | P2  | Acceptance JSON     | 待修复      | `--report` schema per contract                      |
| R2-08 | P2  | failure_class + ADR | 待修复      | external 须 ADR 路径                                |
| R2-09 | P2  | Ledger honesty      | 待修复      | 本表全 **已修复** 或 **FAIL_EXTERNAL+ADR**          |
| R2-10 | P0  | 11/11 live R2       | 待修复      | `r2-tier-a-live-accept-evidence.md` exit 0          |

**阶段外置：** 0（用户裁决：本票必须 R4 闭合）
