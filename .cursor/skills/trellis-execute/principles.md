# trellis-execute — 工程契约

> 主流程：[SKILL.md](SKILL.md) · 条件 skill：[reference.md](reference.md) · 澄清门：[grill-gate.md](../../../.trellis/spec/guides/grill-gate.md)

## ponytail（含测试代码；中文注释除外）

在 **不破坏功能、不简化功能、不破坏流程/机制** 的前提下，写 **最简** 能工作的代码。

- 先复用仓库已有 helper/模式，再写新代码
- 禁止为未请求需求加抽象、依赖、样板
- 测试同样 ponytail：只断言本步 **目的/目标** 所需行为，不堆无关 case
- 有意简化须 `ponytail:` 注释并写明天花板与升级路径

## 防御性工程（禁止）

以「不出事、不碰难区、不担责」替代「问题真解决」——命中任一条即违规：

1. **无限延后**：无 owner、无截止、无下一步的「以后再说」
2. **绕过根因**：包一层/吞异常/假数据/只修表象，且未 `ponytail:` 标注天花板与还债路径
3. **假完成**：为通过检查而改测试目的、缩验证、跳过约定 pytest
4. **假澄清**：未走 grill-gate 对话即假设用户意图

**替代**（三选一，必须能说清是哪一种）：

- **真修**：共享处一次 guard，根因一处修（ponytail）
- **有意简化**：`ponytail:` + 明确不做什么 + 升级路径
- **现在做不了**：grill-gate 问用户；写 blocker / owner / 下一步

**完成条件**：根因已消除，或用户已接受带截止的债务；不得留下无出口的绕过。

## `test-driven-development` 分界

| 产物         | 顺序                                           | skill                                          |
| ------------ | ---------------------------------------------- | ---------------------------------------------- |
| **正式代码** | RED（失败测）→ GREEN（最小实现）               | Read **`test-driven-development`**（RED 相位） |
| **测试代码** | 不 Read `test-driven-development` 套在自己身上 | `testing-guidelines` + `karpathy-guidelines`   |

禁止先写正式实现再补测试；禁止为让测试绿而改 **目的/目标**。

## karpathy + testing-guidelines

- **所有代码**（含测试）：Read `karpathy-guidelines`
- **所有测试**：Read `testing-guidelines`；`test_*` 须 **五字段** docstring：

| 字段      | 含义                           |
| --------- | ------------------------------ |
| 覆盖范围  | 场景人话                       |
| 测试对象  | 被测符号或路径                 |
| 目的/目标 | 证明什么（**不可为通过而改**） |
| 验证点    | 断言/异常                      |
| 失败含义  | 回归失去什么保障               |

细则：`.cursor/skills/testing-guidelines/SKILL.md` §9.1

## 代码查询顺序

1. GitNexus：`query` / `context` / `impact`（改 symbol 前 **必须** `impact()`）
2. 不够 → `grep` / Read
3. **禁止** 未查就猜行为或接口

## 开工前理解（先于第一个 slice）

从下列来源能 **逐项复述**（对应 Boot 0a/0b 完成条件）：

| 来源                                      | 复述项                         |
| ----------------------------------------- | ------------------------------ |
| `research/00-EXECUTION-ENTRY.md` §1       | 任务目标、价值、完成条件（AC） |
| `research/to-issues-slices.md` 当前切片 § | 本 slice 范围与 AC             |
| `frozen/*.md` §9 当前步                   | 规则约束、实现边界、架构触点   |

**任一说不清 → [grill-gate block](../../../.trellis/spec/guides/grill-gate.md)**（对话问用户；解除前不进 slice）。伪 session /「用户认为…」见 grill-gate 禁止表。

## 修复后验证

任何正式代码或测试修复后（含 DEBUG 分支修完）：**`uv run pytest -q` 全绿** 方可勾 `[x]` 或交 handoff。

SLICE 步亦跑全量 pytest；本条覆盖 **slice 之外** 的中途修复。
