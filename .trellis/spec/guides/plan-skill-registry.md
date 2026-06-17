# Plan Skill 候选词典

> **读者：Plan agent**（填 plan.freeze §1 / 选 skill 时查阅）  
> **Plan agent 第一步 MUST Read：** `.cursor/skills/trellis-plan/SKILL.md`  
> **路径权威表：** `plan-skill-paths.yaml`

---

## 0. 与 Execute / Audit 的关系

| 阶段 | 入口 Skill | 冻结位置 | 机器门禁 |
|------|------------|----------|----------|
| **Plan** | trellis-plan | plan.freeze.md §1、§3 | validate-plan-freeze |
| **Execute** | trellis-execute | MASTER §12 | validate-execute-handoff |
| **Audit** | — | AUDIT.plan §1/§2 | Audit A1–A8 |

Plan **不读** execute-skill-registry；Execute **不读** 本文。

---

## 1. Plan 默认必做栈（Phase 0–5d）

```text
trellis-plan (P0 boot)
→ GitNexus P1
→ trellis-brainstorm (2a) + spec-driven-development (2b)
→ grill-me OR interview-me (3)
→ brainstorming / api-and-interface-design (4, 按需)
→ planning-and-task-breakdown (5a)
→ writing-plans (5b)
→ trellis-before-dev (5c)
→ doubt-driven-development (5d, 主会话必做)
```

---

## 2. Phase 路由表

| Phase | Skill | 典型产出 | Plan 填 freeze §1 |
|-------|-------|----------|-------------------|
| boot | trellis-plan | plan-boot.md, plan-skill-reads.jsonl | 必做 |
| P1 | gitnexus-plan (MCP) | gitnexus-summary.md | 必做 |
| 2a | trellis-brainstorm | prd.md, MASTER §1–3 | 必做 |
| 2b | spec-driven-development | MASTER §2 AC | 必做 |
| 3 | grill-me / interview-me | research 会话记录 | 二选一 |
| 4 | brainstorming | MASTER §4 | 条件 |
| 4 | api-and-interface-design | MASTER §6 契约 | 有 API 时必做 |
| 5a | planning-and-task-breakdown | MASTER §5 | 必做 |
| 5b | writing-plans | MASTER §8 列 + research tests | 必做 |
| 5c | trellis-before-dev | implement/check jsonl | 必做 |
| 5d | doubt-driven-development | AUDIT §1/§2 修订 | **必做** |

---

## 3. 禁止事项

- 未完成 Phase P0 写 MASTER §8–§12
- Plan 同轮运行两个「主笔」skill（如 brainstorm + writing-plans 同轮）
- Plan 在 MASTER §8 嵌入完整测试模块
- 未 `validate-plan-freeze` 就 `task.py start`（除非 `--force`）
- Execute 阶段重复跑 Plan skill（trellis-before-dev 已在 5c 完成）

---

## 4. 改 Skill 时改哪里

| 改什么 | 文件 |
|--------|------|
| Plan skill 默认路径 | `plan-skill-paths.yaml` |
| Plan 协议流程 | `.cursor/skills/trellis-plan/SKILL.md` |
| 候选说明 | 本文 |
| 单任务 Plan 记录 | 任务 `plan.freeze.md` §1 |
| 单任务 Execute skill | 任务 `MASTER.plan.md` §12（Plan 5b/5c 写入） |
| 机器门禁 | `validate_plan_freeze.py` / `validate_plan_phase` |

---

## 5. plan.freeze §1 行模板

```markdown
| Phase | Skill | 路径 | 产出 | 已完成 |
|-------|-------|------|------|--------|
| boot | trellis-plan | .cursor/skills/trellis-plan/SKILL.md | plan-boot.md | [ ] |
| P1 | gitnexus-plan | AGENTS.md + MCP | gitnexus-summary.md | [ ] |
```
