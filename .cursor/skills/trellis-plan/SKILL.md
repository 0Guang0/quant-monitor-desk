---
name: trellis-plan
description: "Complex-task Plan v4.1. MUST Read when status=planning. Execution Bundle: skill outputs in research/ + 5e package + validate-plan-freeze."
---

# Trellis Plan（v4.1 · Execution Bundle）

> **读者：Plan agent** · **禁止：** 未完成 P0 即 `task.py start`  
> **原则：** Skill 产出按 **`plan-skill-outputs.yaml`** 结构写入 `research/`；**freeze 后 Execute 仍读包内原文**；`frozen/` + `EXECUTION_INDEX.md` 仅薄指针

## 必读（按序）

1. 本文件 + **`agent-toolchain.md`** + `.trellis/spec/guides/plan-skill-paths.yaml` + **`plan-skill-outputs.yaml`** + **`grill-gate.md`**（`.trellis/spec/guides/`）
2. 模板：`templates/research/00-EXECUTION-ENTRY.template.md` · `EXTERNAL-INDEX.template.md` · `plan-consolidation.md`
3. 样板：`.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/`（v4.1 试点）
4. `docs/implementation_tasks/`（P0 原计划包）
5. 协议：`.trellis/spec/guides/complex-task-planning-protocol.md` §0.2

## P0 Boot

| 产出                      | 动作                                                   |
| ------------------------- | ------------------------------------------------------ |
| 活任务卡 §1–§3 摘要       | Wave 级；**不迁入** `research/`                        |
| `research/plan-boot.md`   | Phase P0 complete                                      |
| `context_pack.json`       | `uv run python scripts/context_router.py --task <dir>` |
| `EXECUTION_INDEX.md` 草稿 | 薄：§0 步骤指针 + §3 包路径（冻结时定稿）              |

## Plan 加固 Skill（v4.1 · 必做）

| Phase      | Skill                            | 产出（结构跟 SKILL.md，文件名登记 §5.1）                                                |
| ---------- | -------------------------------- | --------------------------------------------------------------------------------------- |
| **3.5**    | **to-issues**                    | `research/to-issues-slices.md`（+ 可选 `bypass-baseline-matrix.md`）                    |
| **5a**     | **planning-and-task-breakdown**  | `research/plan-task-breakdown.md`（或等价）                                             |
| **5a'**    | **spec-driven-development**      | `research/plan-spec.md`（或等价）                                                       |
| **5b**     | **context-engineering**          | `research/plan-context.md`                                                              |
| **5c**     | **doubt-driven-development**     | `research/plan-doubt-review.md`                                                         |
| **5c'**    | **documentation-and-adrs**       | `docs/decisions/ADR-NNN-*.md` + ENTRY §4                                                |
| **1–4**    | **trellis-research**（**必做**） | `research/<topic>.md` · `reference-adoption-*.md`                                       |
| **2a / 3** | **澄清类（可选）**               | 需求不明：`grill-me` 等 → 先 **grill-gate** block 问用户 → 再写 `research/*-session.md` |

**铁律：** 信息不明确 → **grill-gate** block（对话问用户）；**禁止** 用 session 文件代替用户回复。见 `.trellis/spec/guides/grill-gate.md`。

**必做（v4.1 freeze）：** GitNexus **1a+1b** + **trellis-research** + 上表加固 skill。

**已废止（v4.1 新任务）：** `writing-plans` — 由 **to-issues** 承载切片 AC；RED/GREEN 证据列写在 `to-issues-slices.md` 各切片。

## Phase 5e — 打包（必做）

1. `research/00-EXECUTION-ENTRY.md` — 总路由（§5.1 登记**全部** `research/*.md`）
2. `research/EXTERNAL-INDEX.md` — §A/B/C
3. `research/plan-consolidation.md` — 分流 + **`Phase 5e complete`**
4. `EXECUTION_PLAN.md` — 仅 GAP + 指向 ENTRY
5. `task.json` `meta.execute_entry` = `research/00-EXECUTION-ENTRY.md`
6. `task.json` `meta.plan_protocol_version` = `"4.1"`（新任务）

**禁止：** 将 `to-issues-slices.md` 全文抄入 `frozen/`。

## 冻结（薄三件套）

```bash
python .trellis/scripts/task.py freeze-task-card <task-dir> --source docs/implementation_tasks/.../NNN_*.md
```

**v4.1：** `freeze-task-card` 写入 **薄 frozen**（审计锚点 + 指向 ENTRY），**不**复制活卡/research 全文。  
**v4.0：** 仍复制活卡全文（遗留任务）。

```bash
python .trellis/scripts/task.py generate-manifests <task-dir>
python .trellis/scripts/task.py validate-plan-phase <task-dir> 5e
python .trellis/scripts/task.py validate-plan-freeze <task-dir>
python .trellis/scripts/task.py start <task-dir>
```

`implement.jsonl`：slot1 = `frozen/`；slot2 = `research/00-EXECUTION-ENTRY.md`。

`plan-skill-reads.jsonl` 每条 Read 一行。
