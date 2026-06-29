# Repair 计划 — R3H-07 US Trading Calendar

> **读者：Repair 执行者**  
> **输入：** `audit.report.md` §4.1–§4.3 · `research/audit-repair-ledger.md`  
> **原则：** 修根因；ponytail · TDD · 五字段 · GitNexus impact；禁止假绿/绕过  
> **任务目录：** `.trellis/tasks/06-29-round3h-r3h07-us-trading-calendar/`

---

## 0. 元信息

| 字段         | 值                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------ |
| slug         | `06-29-round3h-r3h07-us-trading-calendar`                                                  |
| Audit 报告   | `audit.report.md`（总裁决 FAIL · 23 finding）                                              |
| 基线 commit  | `231b5798`（Plan freeze）                                                                  |
| 已有 hygiene | `8602a8eb` 已修 sync_registry + test_sync_orchestrator；Repair 须复验 A1-P3-01 / A8-P2-002 |

**开场白：**

```text
进入 R3H-07 Repair。读 audit.report.md §4.3 与 research/audit-repair-ledger.md。
按 §1 修复包顺序修根因；正式代码先 RED 再 GREEN；改 symbol 前 GitNexus impact()。
关账：ledger 无待修复 + validate-repair-close exit 0 + uv run pytest -q exit 0。
```

---

## 1. 修复项清单（合并去重 · 23 ID → 6 包）

| 包  | 覆盖 ID                                                                  | P     | 根因修复方案                                                            | 验证命令                                  | 通过条件                    |
| --- | ------------------------------------------------------------------------ | ----- | ----------------------------------------------------------------------- | ----------------------------------------- | --------------------------- |
| R1  | A1-P2-01, A5-P1-001, A8-P1-001, A8-P1-002, A7-P2-01, A7-P2-02, A8-P3-001 | P1/P2 | git add SSOT + test；loop_maintain --fix；gitnexus analyze；impact      | git diff 231b5798 --stat · detect_changes | diff 含 SSOT；GitNexus 命中 |
| R2  | A5-P2-001, A8-P2-001                                                     | P2    | round3h audit §7 CAL-US → CLOSED + evidence 指针                        | rg CAL-US.\*CLOSED                        | registry CLOSED             |
| R3  | A1-P3-01, A8-P2-002                                                      | P2/P3 | 确认 sync_registry 测已绿；若仍红修根因                                 | uv run pytest -q                          | exit 0                      |
| R4  | A8-P2-003, A7-P3-01, A7-P3-02                                            | P2/P3 | loop_maintain --fix；同步 loop_manifest 与 INDEX                        | loop_maintain · manifest                  | loop OK                     |
| R5  | A1-P2-02, A2-P2-01, A2-P2-02, A2-P3-03, A2-P2-05                         | P2    | A1-P2-02 优先：session span cap；抽 helper；去二次 filter；合并 adapter | TDD + CAL-US pytest                       | span cap 绿                 |
| R6  | A2-P2-04, A2-P2-06, A5-P3-001, A5-P3-002                                 | P2/P3 | 合并重复测；service_path_support；补 missing + stooq 测                 | test_us_trading_calendar pytest           | 全绿                        |

**冲突消解：** A2-P2-01 删除 dead code 被 A1-P2-02 接入 span cap 覆盖。

---

## 2. Repair Skill 冻结

| Skill                        | 绑定                          | 已执行 |
| ---------------------------- | ----------------------------- | ------ |
| test-driven-development      | R5/R6 正式代码                | [ ]    |
| gitnexus-impact-analysis     | R5 改 fetch_window / ports 前 | [ ]    |
| testing-guidelines（五字段） | 每个新 test\_\*               | [ ]    |

---

## 3. 批准遗留（Deferred）

无（A9 零阶段外置）。

---

## 4. Repair 完成 DoD

- [ ] §1 六包完成；ledger 23 行 → 已修复
- [ ] validate-repair-close exit 0
- [ ] uv run pytest -q exit 0
- [ ] audit.report.md §5 已填

---

## 5. 派发切片

| Agent              | 包    | 核心文件                                                              |
| ------------------ | ----- | --------------------------------------------------------------------- |
| repair-r1-evidence | R1–R4 | task 工件、docs/quality、loop JSON、generated                         |
| repair-r2-code     | R5–R6 | fetch_window、三 US ports、market_structure、test_us_trading_calendar |

**顺序：** R1–R4 先于 R5–R6。
