# Trellis Execute — 工程契约

**Leading words：** `ponytail` · `test-driven-development` · `五字段` · GitNexus · `grill-me`

> **必做 skill / 相位：** 本文件 [reference.md](reference.md) + [principles.md](principles.md) + `execute-skill-paths.yaml`  
> **条件 skill（触发才 Read）：** [agent-toolchain.md](../../agent-toolchain.md) §Execute — 条件 skill

| 约束         | Execute 动作                                  | SSOT                              |
| ------------ | --------------------------------------------- | --------------------------------- |
| **ponytail** | 最简可工作代码；复用 helper；测试只证本步目的 | project-global.mdc §ponytail 细则 |
| **TDD**      | 正式代码 RED→GREEN                            | **`/test-driven-development`**    |
| **五字段**   | 每个 `test_*` docstring                       | `/testing-guidelines`             |
| **GitNexus** | 改 symbol 前 `impact()`                       | project-global.mdc §查代码        |
| **grill-me** | scope 不清 → grill-gate block                 | project-global.mdc §grill-me      |

---

## TDD 分轨（正式代码 vs 测试代码）

| 产物         | 顺序                                           | skill                                                   |
| ------------ | ---------------------------------------------- | ------------------------------------------------------- |
| **正式代码** | RED（失败测）→ GREEN（最小实现）               | Read **`/test-driven-development`**（RED / GREEN 相位） |
| **测试代码** | 不 Read `test-driven-development` 套在自己身上 | `testing-guidelines` + `karpathy-guidelines`            |

**禁止捷径**（绕过根因 · 假完成 · 假澄清 · 分级遗留）→ project-global.mdc **§禁止捷径**。

---

## karpathy + testing-guidelines

| 范围                   | 要求                                                            |
| ---------------------- | --------------------------------------------------------------- |
| **所有代码**（含测试） | Read **`karpathy-guidelines`**                                  |
| **所有测试**           | Read **`testing-guidelines`**；`test_*` 须 **五字段** docstring |

RED 相位：三者同读（`/test-driven-development` · karpathy · testing-guidelines）。  
GREEN 相位：再读 `/test-driven-development`（确认覆盖）+ karpathy + testing-guidelines。

---

## 开工前理解

Boot 读完 **ENTRY + research 登记全文 + 路由表（§A + implement.jsonl）** 后，须能 **口头复述**（不落盘）：

| 来源       | 复述项                   |
| ---------- | ------------------------ |
| ENTRY §1   | 任务目的、价值、完成条件 |
| ENTRY §2   | 架构/约束铁律            |
| 当前切片 § | 本刀范围与 AC            |

**任一说不清 → grill-gate block**（见 project-global.mdc §开工前完成条件）。

---

## 证据纪律

- **唯一可信交付物：** 代码 · 测试 · `pytest` 结果 · INDEX `[x]`
- Skill Read 强化纪律，**不以** jsonl / 长文 / txt 代替完成
- 收尾 **对抗性自检**（可选）：按 ponytail 与 §禁止捷径 收紧；发现问题先修；**不写** audit 表

---

## 修复后

`uv run pytest -q` 全绿方可宣称 Execute 完成。Repair/自检关账 → project-global.mdc **§无遗留**。
