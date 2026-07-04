---
name: trellis-execute
description: >-
  Executes Trellis complex tasks one slice at a time.
  Boot reads EXECUTION_PLAN (v4.2) or ENTRY bundle (v4.1 legacy) + implement.jsonl + INDEX.
  RED/GREEN via /test-driven-development.
---

# Trellis Execute

**Leading word — slice：** 一次只完成 INDEX §1 的一个 Step。

| 层级           | 文件                                                      |
| -------------- | --------------------------------------------------------- |
| 工程契约       | [principles.md](principles.md)                            |
| **必做 skill** | [reference.md](reference.md) + `execute-skill-paths.yaml` |
| **条件 skill** | `[agent-toolchain.md](../../agent-toolchain.md)` §Execute |
| 全局规则       | [project-global.mdc](../../rules/project-global.mdc)      |
| **TDD**        | `**/test-driven-development`\*\*                          |

**SSOT：** `frozen/*.md` + `EXECUTION_INDEX.md` + `implement.jsonl`  
**v4.2 首读：** `EXECUTION_PLAN.md`（slot2）+ `EXECUTION_INDEX.md`

**证据 = 代码与测试**（`uv run pytest -q`）。不单独落盘 handoff 表、txt、skill-reads jsonl。

---

## Phase 0 Boot（开工前 · 读清再动手）

| #   | 动作                                                                                                     | 完成条件                               |
| --- | -------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 0a  | Read `agent-toolchain.md` + 本 skill + `**reference.md`** + `principles.md` + `**project-global.mdc\*\*` | 必做/条件 skill 已加载                 |
| 0b  | Read **Execute 路由**（见下表 · 按 `task.json` 协议分支）                                                | 本刀范围与 AC 已理解                   |
| 0c  | GitNexus `impact()` 扫将改 symbol                                                                        | blast radius 已心里有数                |
| 0d  | `validate-execute-boot <task-dir>`                                                                       | exit 0（v4.1/v4.2 免 context-closure） |

### 0b 读什么（v4.2 · 默认）

| 层           | 路径                                    | 作用                                   |
| ------------ | --------------------------------------- | -------------------------------------- |
| **计划正文** | `EXECUTION_PLAN.md`                     | AC · 约束 · 切片/步骤 · 架构接缝       |
| **执行索引** | `EXECUTION_INDEX.md`                    | §1 当前 Step · §3 manifest 路由        |
| **机器路由** | `implement.jsonl` **每一行**            | 活卡、ADR、契约 yaml、规则、参考文档等 |
| **当前步**   | INDEX §1 当前 Step + 计划内当前切片锚点 | 本刀范围                               |
| **追溯**     | `frozen/*.md`                           | 审计锚点 + 停止条件                    |

---

## 执行中途（每 slice）

```text
当前切片/Step → impact() → Read /test-driven-development → RED → [DEBUG?] → GREEN → SLICE → 代码/测试 → INDEX [x]
```

- **读：** 当前步计划锚点 · INDEX Step · `implement.jsonl` 本步相关行 · **RED/GREEN 前 Read `/test-driven-development`**
- **写：** 代码 · 测试 · INDEX / frozen 勾 `[x]`
- **禁止中途：** audit 报告 · handoff 长文 · `execute-evidence/*.txt` · `execute-skill-reads.jsonl`

---

## 收尾（全部步 `[x]` 后 · 交 Audit 前）

### 对抗性自检（不落盘表）

对照 `EXECUTION_PLAN`（或 v4.1 ENTRY）+ 当前步 AC + `implement.jsonl` 权威，用代码与测试找遗漏 → 先修 → `uv run pytest -q`

### Handoff 机械门

```bash
python .trellis/scripts/task.py validate-execute-handoff <task-dir>
```

通过：`[x]` · loop 四件套（complex）· **不要** `finish-work` 直到 Audit PASS。

缺口覆盖 → **Audit only** · `agents/audit-coverage-model.md`

---

## 禁止

多 step 一批 · 未 RED/GREEN 就勾 `[x]` · 改测试目的换绿 · slice 间填 audit/Plan 表 · **grill-gate 未解除就写码**
