# R3H-01 — PRD（薄索引）

> `thin-index: true` · Plan frozen 2026-06-28

## 目标

Batch 3H 首切片：官方宏观/披露六源 `READY_WITH_EVIDENCE` 或 `ADR_DISABLED_OUT_OF_SCOPE`；首优 **G10** FRED 证据契约合一。

## SSOT

| 文档     | 路径                                                                                                    |
| -------- | ------------------------------------------------------------------------------------------------------- |
| 冻结卡   | `.trellis/tasks/06-28-round3h-r3h01-official-macro/frozen/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md` |
| 执行索引 | `.trellis/tasks/06-28-round3h-r3h01-official-macro/EXECUTION_INDEX.md`                                  |
| 活卡     | `docs/implementation_tasks/.../R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md`                            |
| 3G 输入  | `R3G_MASS_REHEARSAL_OPEN_GAPS.md` G10/G14                                                               |

## 验收

`EXECUTION_INDEX.md` §2；全量 pytest + loop_maintain；**禁止主库写**。

## 状态

`planning` — Plan freeze 完成；待用户批准后 `task.py start`。
