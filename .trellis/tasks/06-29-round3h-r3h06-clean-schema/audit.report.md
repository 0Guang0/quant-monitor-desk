# Audit Report — R3H-06 Clean Schema (Wave 1)

> **日期：** 2026-06-29 · **主会话汇总** · 八路对抗审计  
> **总裁决：** **FAIL → 须 Repair 后复审计**  
> **分支：** `feature/round3h-r3h06-clean-schema`

## 维度裁决

| 维  | 报告                          | 裁决                                    |
| --- | ----------------------------- | --------------------------------------- |
| A1  | `research/audit-a1-report.md` | PASS_WITH_FIXES（3 BLOCKING 流程/文档） |
| A2  | `research/audit-a2-report.md` | PASS_WITH_FIXES（0 BLOCKING）           |
| A3  | `research/audit-a3-report.md` | PASS（0 BLOCKING）                      |
| A4  | `research/audit-a4-report.md` | **REQUEST CHANGES**（1 CODE BLOCKING）  |
| A5  | `research/audit-a5-report.md` | **FAIL**（证据链 + macro BLOCKING）     |
| A6  | `research/audit-a6-report.md` | SKIP（0 BLOCKING）                      |
| A7  | `research/audit-a7-report.md` | PASS（0 BLOCKING）                      |
| A8  | `research/audit-a8-report.md` | PASS_WITH_GAPS（P0 测试缺口）           |

## 合并 BLOCKING（Repair 必须先闭合）

| ID        | 来源                   | 摘要                                                                                  |
| --------- | ---------------------- | ------------------------------------------------------------------------------------- |
| **R-B01** | A4-01 / A5-01          | `_non_target_row_count` 对 `axis_observation` 用 `instrument_id` → macro promote 必崩 |
| **R-B02** | A1-B01                 | `PROJECT_IMPLEMENTATION_ROADMAP` §5.0.0 vs §5.0.1 G3/G4/G6 状态矛盾                   |
| **R-B03** | A1-B02                 | 核心交付未 commit（主会话项；Repair 完成后由主会话 commit）                           |
| **R-B04** | A1-B03 / A5-02 / A5-03 | 9.1–9.9 缺 RED 证据；green/full 多为占位                                              |
| **R-B05** | A5-04                  | 全库 pytest 曾 2 failed（sync_orchestrator）；须稳定后重录 9.10                       |

## 合并 IMPORTANT / P0（Repair 必须修复，不得 waive）

| ID    | 来源                        | 摘要                                                          |
| ----- | --------------------------- | ------------------------------------------------------------- |
| R-I01 | A8 P0 / A2-001 / A5-10      | fred→axis_observation promote E2E 测 + 修 FRED bridge 假绿    |
| R-I02 | A4 DOUBT-02 / A5-06 / A8 P2 | OHLCV promote 后 clean 列非空断言                             |
| R-I03 | A4 DOUBT-03 / A5-05 / A8 P1 | cninfo + fred 幂等 duplicate promote 测                       |
| R-I04 | A4 DOUBT-04                 | `to_bar_staging_values` close 回填 OHLCV 文档化或 fail-closed |

## 合并 NON-BLOCKING（Repair 须逐项处理或实现，禁止静默跳过）

完整清单见 `research/audit-repair-ledger.md`（A1–A8 全部发现项 ID 去重）。

## Repair 完成条件

1. R-B01–R-B05 闭合（B03 由主会话 commit）
2. R-I01–R-I04 闭合
3. `research/audit-repair-ledger.md` 每项标 `fixed` + 证据路径
4. `uv run pytest -q` exit 0
5. `uv run python scripts/loop_maintain.py` OK
6. 重跑 A4/A5/A8 关键测
