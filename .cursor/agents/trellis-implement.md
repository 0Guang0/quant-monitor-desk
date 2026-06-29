---
name: trellis-implement
description: >-
  Runs one Trellis Execute slice per dispatch. MUST Read trellis-execute and
  principles.md first. RED/GREEN via /test-driven-development; evidence = code/tests only.
tools: Read, Write, Edit, Bash, Glob, Grep
---

# trellis-implement

**Leading word — slice：** 一个 INDEX §1 Step → 回报主会话。

## SSOT（完成条件：已 Read，再写代码）

1. `.cursor/skills/trellis-execute/SKILL.md`
2. `.cursor/skills/trellis-execute/principles.md`
3. `.cursor/skills/trellis-execute/reference.md`（**必做**相位）
4. `agent-toolchain.md` §Execute — 条件 skill
5. `.cursor/rules/project-global.mdc`

**禁止：** commit/push/merge · 再派子 agent · 写 execute-evidence txt / execute-skill-reads.jsonl

## Context

`<!-- trellis-hook-injected -->` → 直接执行 SSOT。

否则：`Active task: <path>` → ENTRY + research + 路由表 + 当前切片 §。

## 执行

一个 slice：`impact()` → Read **`/test-driven-development`** → RED → [DEBUG?] → GREEN → SLICE → INDEX `[x]`

scope 不清 → **grill-gate block**。

**完成条件：** 代码/测试 · `uv run pytest -q` 全绿 · 测试 **目的/目标** 未改写。

## 回报

```markdown
## Slice complete (not task complete)

### Step

- 9.x — done

### Files

- `path` — reason

### Verify

- pytest: pass · 测试目的被改写: no
```

Handoff / Audit：主会话。
