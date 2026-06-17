---
name: trellis-plan
description: "Complex-task Plan Phase P0 boot + Phases 1–5 protocol. MUST Read first when task.json status=planning and MASTER.plan.md is being authored. Blocks MASTER freeze until boot artifacts exist."
---

# Trellis Plan Protocol (v2)

> **读者：Plan agent** · **触发：** `task.py create` 后、`status=planning`、编写/冻结 `MASTER.plan.md` 前  
> **禁止：** 未完成 Phase P0 即冻结 §8–§12 或运行 `task.py start`

Skill 路径表：`.trellis/spec/guides/plan-skill-paths.yaml`  
候选词典：`.trellis/spec/guides/plan-skill-registry.md`

---

## Phase P0 · Boot（planning 开始后 — 禁止写 MASTER §8–§12）

| # | 动作 | 产出 | validate |
|---|------|------|----------|
| P0a | **Read 本文件** + `plan-skill-paths.yaml` | `plan-skill-reads.jsonl` 首行 | freeze |
| P0b | GitNexus `query` + `context`（改 symbol 前 `impact`） | `research/gitnexus-summary.md` | freeze + phase P1 |
| P0c | 读 DECISIONS / 前置 Batch 文档（implement.jsonl 若已有） | `research/plan-boot.md` 含 **`Phase P0 complete`** | freeze |

**plan-boot.md 最低结构：**

```markdown
# Plan Boot — {slug}
## 用户目标摘要
## 前置依赖 / Batch 关系
## 预期 AC 草稿（→ MASTER §2）
## Plan Phase 顺序（P1→P5d）
## Phase P0 complete
```

**plan-skill-reads.jsonl**（每 Read 一条）：

```json
{"phase":"boot","skill":"trellis-plan","path":".cursor/skills/trellis-plan/SKILL.md"}
{"phase":"P1","skill":"gitnexus-plan","action":"query+context","artifact":"research/gitnexus-summary.md"}
```

---

## Phase P1–P5 · 顺序执行（禁止跳步 · 禁止同轮双主笔）

| Phase | Read Skill | 产出 | 可选 validate |
|-------|------------|------|---------------|
| **P1** | GitNexus MCP | `research/gitnexus-summary.md` | `validate-plan-phase … P1` |
| **2a** | trellis-brainstorm | `prd.md`、MASTER §1–3 初稿 | `… 2a` |
| **2b** | spec-driven-development | MASTER §2 可验证 AC | `… 2b` |
| **3** | grill-me **或** interview-me（二选一） | `research/grill-me-session.md` 等、§7 | `… 3` |
| **4** | brainstorming [+ api-and-interface-design] | MASTER §4–6 | `… 4` |
| **5a** | planning-and-task-breakdown | MASTER §5 切片 | `… 5a` |
| **5b** | writing-plans | MASTER §8 RED/GREEN 列 + `research/*-tests.md` | `… 5b` |
| **5c** | trellis-before-dev | `implement.jsonl` / `check.jsonl` spec 路径 | `… 5c` |
| **5d** | doubt-driven-development（**必做·主会话**） | §7/§8/§12 + AUDIT §1/§2 修订 | `… 5d` |

每 Phase 完成：append `plan-skill-reads.jsonl` + `plan.freeze.md` §1 该行 `[x]`。

**Plan 禁止：** 在 MASTER §8 内嵌 >2 个完整 `def test_*`（正文放 research/）。

---

## Phase P5 · 冻结（`task.py start` 前）

1. 合并 MASTER + `AUDIT.plan.md` + `plan.freeze.md`
2. 填 MASTER §8–§12、§9 四层、§10 Tier；AUDIT §2 无 `{{}}`
3. `implement.jsonl` 第一条 = MASTER（Execute 时第二条 = trellis-execute）
4. `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` → exit 0
5. 用户批准 → `task.py start`

---

## 与 Execute 边界

| Plan 冻结 | Execute 证明 |
|-----------|--------------|
| §8 RED/GREEN **命令** + tracer 名 | `execute-evidence/{step}-red/green.txt` |
| §12 Skill **表** | skill-reads + 逐步 Read |
| §10 Tier **命令** | 跑命令 + 证据 |

Plan **不跑** RED/GREEN pytest。

---

## 自检（validate-plan-freeze 前）

- [ ] `plan-boot.md` 含 `Phase P0 complete`
- [ ] `gitnexus-summary.md` 存在
- [ ] `plan-skill-reads.jsonl` 覆盖 freeze 必做 skill（见 plan-skill-paths.yaml）
- [ ] `plan.freeze.md` §3 全 `[x]`
