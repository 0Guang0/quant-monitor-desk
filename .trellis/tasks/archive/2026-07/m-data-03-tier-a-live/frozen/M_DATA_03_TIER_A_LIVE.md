<!-- FROZEN: Plan protocol v4.1 · thin pointer · Plan R2 @ 2026-07-03 -->

# FROZEN — M-DATA-03 — 11 源 Tier A R4 真网验收（Plan R2）

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **用户 AC：** `research/plan-revision-r2.md` §2  
> **禁止：** 复制 `to-issues-slices.md` 或 research 全文

## 8. 边界

见 ENTRY §2 · 活卡「不在范围」；**禁止 SKIP 当过关**；**禁止阶段外置**。

## 9. Plan R2 切片（Execute 步骤）

| 切片          | 说明                           |
| ------------- | ------------------------------ |
| S-R2-EVIDENCE | `live_tier_a_evidence_v1` 实现 |
| S-R2-F0       | 四族 profile；无 SKIP          |
| S-R2-B2       | validate_table 主路径          |
| S-R2-DISPATCH | 去重 + mootdx matrix           |
| S-R2-ACCEPT   | 11/11 live + report JSON       |
| S-R2-CI       | nightly + workflow_dispatch    |

AC 细节：`research/to-issues-slices.md`  
证据契约：`specs/contracts/live_tier_a_evidence_v1.yaml`

## 10. R1 基线

已交付 replay/live harness。非 Plan 证据：`research/archive/non-plan/execute/`。
