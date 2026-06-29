# Plan Skill 候选词典

> **读者：Plan agent**（填 plan.freeze §1 / 选 skill 时查阅）  
> **Plan agent 第一步 MUST Read：** `.cursor/skills/trellis-plan/SKILL.md`  
> **路径权威表：** `plan-skill-paths.yaml`

---

## 0. 与 Execute / Audit 的关系

| 阶段        | 入口 Skill      | 冻结位置              | 机器门禁                 |
| ----------- | --------------- | --------------------- | ------------------------ |
| **Plan**    | trellis-plan    | plan.freeze.md §1、§3 | validate-plan-freeze     |
| **Execute** | trellis-execute | MASTER §12            | validate-execute-handoff |
| **Audit**   | —               | AUDIT.plan §1/§2      | Audit A1–A8              |

Plan **不读** execute-skill-registry；Execute **不读** 本文。

---

## 1. Plan 默认必做栈

### v4.1（新复杂任务 · `plan_protocol_version: "4.1"`）

```text
trellis-plan (P0 boot)
→ … Phase 1–4 同 v4 …
→ to-issues (3.5) → research/to-issues-slices.md
→ planning-and-task-breakdown (5a) → research/（Plan Document Template）
→ spec-driven-development (5a') → research/（Spec 模板）
→ context-engineering (5b) → research/plan-context.md
→ doubt-driven-development (5c) → research/plan-doubt-review.md
→ documentation-and-adrs (5c') → docs/decisions/ADR-*.md
→ [条件] trellis-research (1–4) → research/<topic>.md
→ trellis-plan (5e) → 00-EXECUTION-ENTRY + EXTERNAL-INDEX + plan-consolidation
```

**废止：** `writing-plans`（由 to-issues 承载切片 AC/证据）

### v4.0 遗留栈

```text
… → planning-and-task-breakdown (5a) → writing-plans (5b) → trellis-before-dev (5c) → doubt-driven-development (5d)
```

---

## 2. Phase 路由表

| Phase | Skill                                     | 典型产出                                  | Plan 填 freeze §1 |
| ----- | ----------------------------------------- | ----------------------------------------- | ----------------- |
| boot  | trellis-plan                              | plan-boot.md, plan-skill-reads.jsonl      | 必做              |
| 1a    | gitnexus-plan (MCP)                       | project-overview.md（≤1 页）              | 必做              |
| 2a    | trellis-brainstorm                        | prd.md, MASTER §1–3                       | 必做              |
| 2b    | spec-driven-development                   | MASTER §2 AC                              | 必做              |
| 条件  | domain-modeling                           | CONTEXT.md                                | 条件              |
| 3     | grill-me / interview-me / grill-with-docs | research 会话记录                         | 必须选一          |
| 3.5   | to-issues                                 | 垂直切片工单 → MASTER §8                  | 必做              |
| 1b    | gitnexus-plan (MCP)                       | gitnexus-summary.md（需求锚定）           | 必做              |
| 4     | brainstorming                             | MASTER §4                                 | 条件              |
| 4     | api-and-interface-design                  | MASTER §6 契约                            | 有 API 时必做     |
| 4     | codebase-design                           | 深度模块接口设计                          | 条件              |
| 4     | prototype                                 | 可丢弃原型 + 设计决策                     | 条件              |
| 4     | （跳过）                                  | MASTER §0 注明跳过理由（"§8 已足够清晰"） | 条件              |
| 5a    | planning-and-task-breakdown               | MASTER §8 垂直切片顺序                    | 必做              |
| 5b    | writing-plans                             | MASTER §5（含 §5.3 用例设计）+ §9 骨架    | 必做              |
| 5c    | trellis-before-dev                        | implement/check jsonl                     | 必做              |
| 5d    | doubt-driven-development                  | AUDIT §1/§2 修订                          | **必做**          |

---

## 3. 禁止事项

- 未完成 Phase P0 写 MASTER §5–§11
- Plan 同轮运行两个「主笔」skill
- Plan 在 MASTER 内嵌完整测试模块
- **Plan skill 写入 MASTER §11 Execute Skill 表**
- 未 `validate-plan-freeze` 就 `task.py start`
- Execute 阶段重复跑 Plan skill（trellis-before-dev 已在 5c 完成）

---

## 4. 改 Skill 时改哪里

| 改什么               | 文件                                              |
| -------------------- | ------------------------------------------------- |
| Plan skill 默认路径  | `plan-skill-paths.yaml`                           |
| Plan 协议流程        | `.cursor/skills/trellis-plan/SKILL.md`            |
| 候选说明             | 本文                                              |
| 单任务 Plan 记录     | 任务 `plan.freeze.md` §1                          |
| 单任务 Execute skill | 任务 `MASTER.plan.md` §12（Plan 5b/5c 写入）      |
| 机器门禁             | `validate_plan_freeze.py` / `validate_plan_phase` |

---

## 5. plan.freeze §1 行模板

```markdown
| Phase | Skill                                    | 路径                                       | 产出                | 已完成 |
| ----- | ---------------------------------------- | ------------------------------------------ | ------------------- | ------ |
| boot  | trellis-plan                             | .cursor/skills/trellis-plan/SKILL.md       | plan-boot.md        | [ ]    |
| 1a    | gitnexus-plan                            | AGENTS.md + MCP                            | project-overview.md | [ ]    |
| 2a    | trellis-brainstorm                       | .cursor/skills/trellis-brainstorm/SKILL.md | prd.md              | [ ]    |
| 2b    | spec-driven-development                  | 见 plan-skill-paths.yaml                   | MASTER §2 AC        | [ ]    |
| 3     | grill-me / interview-me                  | 见 yaml / mattpocock                       | 质疑记录            | [ ]    |
| 3.5   | to-issues                                | ~/.claude/skills/to-issues/SKILL.md        | 切片工单            | [ ]    |
| 1b    | gitnexus-plan                            | AGENTS.md + MCP                            | gitnexus-summary.md | [ ]    |
| 4     | brainstorming / api-and-interface-design | 见 yaml                                    | MASTER §4–6         | [ ]    |
| 5a    | planning-and-task-breakdown              | 见 yaml                                    | MASTER §5           | [ ]    |
| 5b    | writing-plans                            | 见 yaml                                    | MASTER §8           | [ ]    |
| 5c    | trellis-before-dev                       | .cursor/skills/trellis-before-dev/SKILL.md | jsonl               | [ ]    |
| 5d    | doubt-driven-development                 | 见 yaml                                    | AUDIT §1/§2 修订    | [ ]    |
```
