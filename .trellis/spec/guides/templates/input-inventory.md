# Input Inventory — {{slug}} (P0i)

> **读者：Plan agent** · **阶段：P0i（在 2a brainstorm 之前）**  
> **目的：** 枚举本任务「文档宇宙」，区分仓库内已有 / 应列未列 / 仓库缺失，**不是**仅记录「已读」。

## 1. 任务卡展开

| 来源 | 路径 | 状态 |
|------|------|------|
| §3 输入 | `...` | in-repo / missing-in-repo |
| §5 参考 | `...` | in-repo / missing-in-repo |

## 2. 六类关键信息覆盖

| 类别 | 必须覆盖 | 已定位路径 | 缺口 |
|------|----------|------------|------|
| 决策 defer | DECISIONS §9 | | |
| 规则 / 规范 | GLOBAL + Round | | |
| 架构边界 | 03/04/07 | | |
| 业务需求 | 模块 spec + 任务卡 | | |
| 契约 | specs/contracts | | |
| 前置 Batch | handoff + 台账 | | |

## 3. 交叉引用闭包（1-hop）

| 自 | 引用 | 状态 |
|----|------|------|
| `docs/modules/....md` | `...` | required / missing |

## 4. missing-in-repo（须用户确认或写 DECISIONS 后才能继续 Plan）

- （无则写「无」）

## 5. 门禁

- [ ] 任务卡 §3 + §5 已展开
- [ ] 六类关键信息均有路径或已记 missing-in-repo
- [ ] `original-plan-trace.md` manifest 列与本文一致

`P0i complete`
