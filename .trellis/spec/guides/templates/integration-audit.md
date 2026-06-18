# Integration Audit — {{slug}} (Plan 5d)

> **读者：Plan agent** · **对抗：** inline 是否丢义；pointer 是否写清；六类关键信息是否全覆盖。

## 1. 用户预期对齐（上下文保真压缩）

| 判据 | 结论 | 证据 |
|------|------|------|
| 能 inline 的已进 MASTER | PASS/FAIL | MASTER §x |
| 不能 inline 的均有 ledger + extract | PASS/FAIL | integration-ledger.md |
| Execute 可不迷失（不裸索引） | PASS/FAIL | implement reason 含 extract/for |
| grill/to-issues 结论已 closure | PASS/FAIL | MASTER §7 / §3.2 |

## 2. 六类关键信息

| 类别 | 覆盖方式 | 缺口 |
|------|----------|------|
| 决策 | | |
| 规则/规范 | | |
| 架构 | | |
| 业务需求 | | |
| 契约 | | |
| wiring/测试/门禁 | | |

## 3. 丢义风险（inline 过度概括）

- （无则写「无」）

## 4. Verdict

**integration-audit: PASS | FAIL**

冻结前须 PASS（与 plan-manifest-audit 并列）。
