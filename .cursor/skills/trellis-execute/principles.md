# trellis-execute — 工程契约

> 主流程：[SKILL.md](SKILL.md) · 条件 skill：[reference.md](reference.md) · 澄清门：[grill-gate.md](../../../.trellis/spec/guides/grill-gate.md)

## ponytail（含测试；中文注释除外）

不破坏功能/流程/机制前提下 **最简** 能工作代码。先复用仓库模式；禁止未请求抽象；测试只断言本步 **目的/目标**；有意简化标 `ponytail:`。

## `test-driven-development` 分界

| 产物         | 顺序                             | skill                                          |
| ------------ | -------------------------------- | ---------------------------------------------- |
| **正式代码** | RED（失败测）→ GREEN（最小实现） | Read **`test-driven-development`**（RED 相位） |
| **测试代码** | 不套 TDD 在自己身上              | `testing-guidelines` + `karpathy-guidelines`   |

禁止先实现后补测；禁止为通过改测试 **目的/目标**。

## karpathy + testing-guidelines

所有代码 Read `karpathy-guidelines`。所有 `test_*` Read `testing-guidelines` + **五字段** docstring（覆盖范围 · 测试对象 · 目的/目标 · 验证点 · 失败含义）。细则：`.cursor/skills/testing-guidelines/SKILL.md` §9.1

## 代码查询

GitNexus `query` / `context` / `impact`（改 symbol 前 **必须** `impact()`）→ 不够再 grep。**禁止** 未查就猜。

## 开工前 + 澄清

从 ENTRY §1、当前切片、frozen §9 能复述：目标、价值、AC、边界、架构触点。

**说不清 → [grill-gate block](../../../.trellis/spec/guides/grill-gate.md)**（对话问用户；解除前不进 slice）。

## 修复后

`uv run pytest -q` 全绿方可勾 `[x]` 或 handoff。
