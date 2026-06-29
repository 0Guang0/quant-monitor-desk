# Integration Audit — {{slug}} (Plan 5c · v4.1)

> **读者：Plan agent** · **对抗：** research 产出是否丢义；ENTRY §5.1 是否登记。

## 1. 用户预期对齐（Execution Bundle）

| 判据                                       | 结论      | 证据                                       |
| ------------------------------------------ | --------- | ------------------------------------------ |
| skill 产出已登记 ENTRY §5.1                | PASS/FAIL | 00-EXECUTION-ENTRY.md §5.1                 |
| 不能 inline 的均有 pointer + extract/for   | PASS/FAIL | plan-context.md / EXTERNAL §B              |
| Execute 可不迷失（§5.2 硬门禁）            | PASS/FAIL | ENTRY §5.2 名单                            |
| grill/to-issues 结论已 closure             | PASS/FAIL | plan-doubt-review.md / to-issues-slices.md |
| §5.1 = 磁盘 research/\*.md（除 plan-boot） | PASS/FAIL | plan-consolidation.md                      |

## 2. 六类关键信息

| 类别             | 覆盖方式                                 | 缺口 |
| ---------------- | ---------------------------------------- | ---- |
| 决策             | ADR + ENTRY §4                           |      |
| 规则/规范        | plan-spec / EXTERNAL §A                  |      |
| 架构             | plan-task-breakdown / reference-adoption |      |
| 业务需求         | to-issues-slices + 活卡（EXTERNAL §A）   |      |
| 契约             | specs/contracts + plan-spec              |      |
| wiring/测试/门禁 | INDEX §2/§2.1 + slices                   |      |

## 3. 丢义风险（摘要过度 / 未下沉 research）

- （无则写「无」）

## 4. Verdict

**integration-audit: PASS | FAIL**

冻结前须 PASS（与 `validate-plan-freeze` 并列）。缺口覆盖关账 → **Audit A1–A8**（`audit-coverage-model.md`）。
