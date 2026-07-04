---
name: trellis-plan
description: "Complex-task Plan v4.2 (default). User invokes skills → EXECUTION_PLAN; routing → EXECUTION_INDEX §3."
---

# Trellis Plan（v4.2 · Slim Plan · 默认）

> **读者：Plan agent** · **禁止：** 未完成 P0 即 `task.py start`  
> **原则：** 用户 **手动** 调用 Skill → agent 按 **该 Skill 当次要求** 写/改计划；**禁止** 仓库预设章节模板或 Skill→§ 机械映射  
> **legacy v4.1：** 见本文末「附录 · v4.1 Execution Bundle」

## 必读（按序）

1. 本文件 + **`agent-toolchain.md`** + `plan-skill-paths.yaml` + **`plan-skill-outputs.yaml`** + **`grill-gate.md`**
2. `docs/implementation_tasks/`（P0 原计划包）
3. 协议：`.trellis/spec/guides/complex-task-planning-protocol.md` §0.0.2

**禁止：** 从 `templates/` 复制 `EXECUTION_PLAN` 骨架（仓库 **无** 计划/索引固定模板）。

## P0 Boot

| 产出                      | 动作                                                   |
| ------------------------- | ------------------------------------------------------ |
| 活任务卡 §1–§3 摘要       | Wave 级；**不迁入** `research/`（除非用户 Skill 要求） |
| `research/plan-boot.md`   | Phase P0 complete                                      |
| `context_pack.json`       | `uv run python scripts/context_router.py --task <dir>` |
| `EXECUTION_INDEX.md` 草稿 | 薄：§0 元数据 + §1 步骤指针 + §3 manifest 占位         |

## Plan Skill（v4.2 · 用户调用才跑）

| 典型 Phase | Skill（用户选用）                   | 默认合入位置                |
| ---------- | ----------------------------------- | --------------------------- |
| 1a/1b      | GitNexus                            | `research/`                 |
| 1–4        | **trellis-research**（freeze 必做） | `research/`                 |
| 2–5        | spec / to-issues / planning…        | **`EXECUTION_PLAN.md`**     |
| 3          | 澄清类（可选）                      | `research/*-session` 或 ADR |
| 5e         | **trellis-plan**                    | 打包 + 索引同步             |

**铁律：** 信息不明确 → **grill-gate** block；**禁止** 未经用户调用批量跑 Skill 填计划。

**freeze 必做 skill（机械门）：** GitNexus **1a+1b** + **trellis-research** + **trellis-plan**（见 `freeze_required_skills_v42`）。

## Phase 5e — 打包（必做）

1. **`EXECUTION_PLAN.md`** — 唯一执行计划正文 SSOT
2. **`EXECUTION_INDEX.md`** — §1 步骤 · §3 manifest（从计划摘录外部必读）· §5 Audit 追溯
3. `task.json`：`meta.plan_protocol_version` = `"4.2"` · `meta.execute_entry` = `EXECUTION_PLAN.md`

**禁止：** 将计划全文抄入 `frozen/`；禁止复制 v4.1 的 ENTRY/EXTERNAL/consolidation 包（新任务）。

## 冻结（薄三件套）

```bash
python .trellis/scripts/task.py freeze-task-card <task-dir> --source docs/implementation_tasks/.../NNN_*.md
python .trellis/scripts/task.py generate-manifests <task-dir>
python .trellis/scripts/task.py validate-plan-phase <task-dir> 5e
python .trellis/scripts/task.py validate-plan-freeze <task-dir>
python .trellis/scripts/task.py start <task-dir>
```

**v4.2：** `frozen/*.md` = 薄指针 → `EXECUTION_PLAN.md`；`implement.jsonl` slot1=`frozen/` · slot2=`EXECUTION_PLAN.md`。

`plan-skill-reads.jsonl` 每条 Read 一行。

---

## 附录 · v4.1 Execution Bundle（归档 / 在途任务只读）

> 新复杂任务 **不得** 再建 v4.1 包。在途任务继续读本附录 + `templates/plan.freeze.md` §3.0v4.1。

- 模板：`templates/research/00-EXECUTION-ENTRY.template.md` · `EXTERNAL-INDEX.template.md` · `plan-consolidation.md`
- 样板：`.trellis/tasks/archive/.../06-29-round3h-r3h10-datasource-service-ssot/`
- 5e：`00-EXECUTION-ENTRY` · `EXTERNAL-INDEX` · `plan-consolidation` · 薄 `EXECUTION_PLAN.md`
- Audit Boot：`agents/audit-boot-v4.2.md`（v4.1 legacy：`audit-boot-v4.1.md`）
