# Plan consolidation — R3-DCP-05

> Phase 5e · Skill 产出对照与分流

---

## Skill 对照表

| Skill                          | 产出文件                                                                                                                                                                                                                                                                           | 状态 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| P0 Boot                        | `plan-boot.md`                                                                                                                                                                                                                                                                     | ✅   |
| GitNexus 1a                    | `project-overview.md`                                                                                                                                                                                                                                                              | ✅   |
| GitNexus 1b                    | `gitnexus-summary.md`                                                                                                                                                                                                                                                              | ✅   |
| trellis-research               | `reference-adoption-dcp05.md`                                                                                                                                                                                                                                                      | ✅   |
| to-issues 3.5                  | `to-issues-slices.md`                                                                                                                                                                                                                                                              | ✅   |
| planning-and-task-breakdown 5a | `plan-task-breakdown.md`                                                                                                                                                                                                                                                           | ✅   |
| spec-driven-development 5a'    | `plan-spec.md`                                                                                                                                                                                                                                                                     | ✅   |
| context-engineering 5b         | `plan-context.md`                                                                                                                                                                                                                                                                  | ✅   |
| doubt-driven-development 5c    | `plan-doubt-review.md`                                                                                                                                                                                                                                                             | ✅   |
| documentation-and-adrs 5c'     | `docs/decisions/ADR-028-*.md`                                                                                                                                                                                                                                                      | ✅   |
| trellis-plan 5e                | `00-EXECUTION-ENTRY.md`, `EXTERNAL-INDEX.md`, 本文件                                                                                                                                                                                                                               | ✅   |
| 活卡                           | `R3_DCP_05_TIER_A_INCREMENTAL.md`                                                                                                                                                                                                                                                  | ✅   |
| trellis-execute / audit        | `execute-reference-read-evidence-s01-s08.md` · `execute-reference-read-evidence-s02-s06.md` · `execute-reference-read-evidence-s07-s11.md` · `parallel-dispatch-protocol.md` · `integration-audit.md`                                                                              | ✅   |
| trellis audit / repair         | `gitnexus-audit-summary.md` · `audit-a1-report.md` · `audit-a2-report.md` · `audit-a3-report.md` · `audit-a4-report.md` · `audit-a5-report.md` · `audit-a6-report.md` · `audit-a7-report.md` · `audit-a8-report.md` · `audit-repair-ledger.md` · `contract-compliance-evidence.md` | ✅   |

## 分流

| 内容             | 落点                          | 不进 frozen 全文 |
| ---------------- | ----------------------------- | ---------------- |
| 切片 AC          | `to-issues-slices.md`         | ✅               |
| 11/11 clean 矩阵 | ADR-028                       | ✅               |
| 参考 L 梯        | `reference-adoption-dcp05.md` | ✅               |
| 活卡 §1–§3       | 包外活卡                      | ✅               |

## ENTRY §5.1 核对

`research/*.md`（除 plan-boot 可选）均已登记于 `00-EXECUTION-ENTRY.md` §5.1。

## Phase 5e complete

- [x] `00-EXECUTION-ENTRY.md`
- [x] `EXTERNAL-INDEX.md`
- [x] `plan-consolidation.md` 本文件
- [x] `EXECUTION_PLAN.md` 薄指针
- [x] `task.json` `meta.execute_entry`
- [x] ADR-028 索引 §4

### Execute GAPs（PASS_WITH_GAPS 承接）

| GAP                        | 切片    |
| -------------------------- | ------- |
| migration 015              | S00     |
| baostock live mock         | S01     |
| 9 源 incremental ops + e2e | S03–S11 |
| CLI 11 源路由              | S12     |
| registry + 东财 SSOT       | S13     |
