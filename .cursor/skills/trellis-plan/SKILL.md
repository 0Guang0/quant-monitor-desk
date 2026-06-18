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
| **P0i** | **文档宇宙审计**（§3+§5+六类+1-hop） | `research/input-inventory.md` 含 **`P0i complete`** | P0i |
| **P0o** | **读原计划包**（见下表；**在 P0i 之后**） | `research/original-plan-trace.md` | freeze |
| P0b | GitNexus 轻量预检（**可选**；深度分析在 **1b**，若跳过须在 plan-boot 注明） | `research/gitnexus-summary.md` 草稿或 defer→1b | freeze + phase 1b |
| P0c | 读 DECISIONS / 前置 Batch / 任务卡 §3+§5 | `research/plan-boot.md` 含 **`Phase P0 complete`** | freeze |

### P0o · 原计划必读（`docs/implementation_tasks/`）

| 顺序 | 路径 | 说明 |
|------|------|------|
| 1 | `docs/implementation_tasks/README.md` | 全局顺序与规则索引 |
| 2–5 | `GLOBAL_*.md`（**4** 个） | 执行/测试/资源/任务模板 |
| 6 | `ROUND_*/README.md` | 本 Round 目标与批次 |
| 7 | `ROUND_*/DECISIONS.md` | 已确认边界（**权威**） |
| 8 | `NNN_*.md` | 本批正式任务卡 |
| 9 | 任务卡 §3 列出的 specs / architecture / modules | 架构与契约 |

**`research/original-plan-trace.md` 最低结构：**

```markdown
# Original Plan Trace — {slug}
## Round / Batch
## 任务卡清单（NNN → 路径）
## AC 映射（任务卡预期结果 → MASTER §2）
## 输入文件已读（specs / architecture）

| 路径 | 类别 | manifest |
|------|------|----------|
| `docs/implementation_tasks/.../NNN_*.md` | 任务卡 | required |
| `docs/modules/....md` | 模块 spec | required |
| `backend/app/....py` | 接线（前置 Batch） | inherited |
| `scripts/sync_....py` | Execute 新建 | deferred |
## 路径纠偏（若任务卡路径与仓库不一致，写明实际路径）
```

**plan-boot.md 最低结构：**

```markdown
# Plan Boot — {slug}
## 用户目标摘要
## 原计划已读（ROUND + NNN 任务卡 + DECISIONS）
## 前置依赖 / Batch 关系
## 预期 AC 草稿（→ MASTER §2）
## Plan Phase 顺序（1a→2→3→3.5→1b→4→5a→5d）
## Phase P0 complete
```

**plan-skill-reads.jsonl**（每 Read 一条）：

```json
{"phase":"boot","skill":"trellis-plan","path":".cursor/skills/trellis-plan/SKILL.md"}
{"phase":"1a","skill":"gitnexus-plan-1a","action":"query+context","artifact":"research/project-overview.md"}
```

---

## Phase 1a–5d · 顺序执行（禁止跳步 · 禁止同轮双主笔）

| Phase | Read Skill | 产出 | 可选 validate |
|-------|------------|------|---------------|
| **1a** | GitNexus MCP（轻量概览） | `research/project-overview.md`（≤1 页） | `validate-plan-phase … 1a` |
| **2a** | trellis-brainstorm | `prd.md`、MASTER §1–3 初稿 | `… 2a` |
| **2b** | spec-driven-development [+ domain-modeling] | MASTER §2 可验证 AC | `… 2b` |
| **3** | grill-me **或** interview-me **或** grill-with-docs（必须选一） | `research/grill-me-session.md` 等、§7 | `… 3` |
| **3.5** | to-issues | 切片工单列表 | `… 3.5` |
| **1b** | GitNexus MCP（需求聚焦深度分析） | `research/gitnexus-summary.md` | `… 1b` |
| **4** | brainstorming / api-and-interface-design [+ codebase-design / prototype] | MASTER §4–6（条件性，跳过须书面理由） | `… 4` |
| **5a** | planning-and-task-breakdown | MASTER §5 切片 | `… 5a` |
| **5b** | writing-plans | MASTER §8 RED/GREEN 列 + `research/*-tests.md` | `… 5b` |
| **5c** | trellis-before-dev | `integration-ledger.md` → `implement.jsonl` / `check.jsonl` | `… 5c` |
| **5d** | doubt-driven-development（**必做·主会话**） | §7/§8/§12 + `plan-manifest-audit` + **`integration-audit`** | `… 5d` |

每 Phase 完成：append `plan-skill-reads.jsonl` + `plan.freeze.md` §1 该行 `[x]`。

**Plan 禁止：** 在 MASTER §8 内嵌 >2 个完整 `def test_*`（正文放 research/）。

---

## Phase P5 · 冻结（`task.py start` 前）

1. 合并 MASTER + `AUDIT.plan.md` + `plan.freeze.md`
2. 填 MASTER §8–§12、§9 四层、§10 Tier；AUDIT §2 无 `{{}}`
3. `implement.jsonl` 第一条 = MASTER（Execute 时第二条 = trellis-execute）
4. `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` → exit 0
5. 用户批准 → `task.py start`

**5c manifest（E12/E5/v3）：** 维护 `integration-ledger.md` → 从 ledger 生成/校验 `implement.jsonl`（pointer 须 `extract:|for:`）→ `validate-plan-phase … 5c`。

**5d audits（E9/v3）：** **`integration-audit.md`（canonical，含 doc-gap + adversarial + closure）**；`plan-manifest-audit.md` 可为 E9 路径 stub。

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

- [ ] `research/original-plan-trace.md` 存在且含任务卡 ↔ AC 映射
- [ ] `plan-boot.md` 含 `Phase P0 complete` 与「原计划已读」
- [ ] `project-overview.md` 存在（≤1 页）或 analysis_waiver: true
- [ ] `gitnexus-summary.md` 存在或 analysis_waiver: true
- [ ] `plan-skill-reads.jsonl` 覆盖 freeze 必做 skill（见 plan-skill-paths.yaml）
- [ ] `plan.freeze.md` §3 全 `[x]`；**Manifest Gate** 全 `[x]`
- [ ] `plan-manifest-audit.md` 存在（E9）
- [ ] `input-inventory.md` P0i + `integration-ledger.md` + `integration-audit.md` PASS（v3）
- [ ] `suggest-implement-context` 缺失 ≤5
