---
name: trellis-plan
description: "Complex-task Plan. MUST Read when status=planning. Blocks freeze until P0-index + validate-plan-freeze pass."
---

# Trellis Plan（v4 · 薄 skill）

> **读者：Plan agent** · **禁止：** 未完成 P0 即写冻结三件套或 `task.py start`

## 必读（按序）

1. 本文件 + **`agent-toolchain.md`**（根目录）+ `.trellis/spec/guides/plan-skill-paths.yaml`
2. **模板：** `templates/EXECUTION_INDEX.md` · `templates/FROZEN_TASK_CARD.md` · `templates/AUDIT.plan.md`
3. **遗留 v3：** `templates/MASTER.plan.md`（仅维护旧任务）
4. `docs/implementation_tasks/`（README → GLOBAL×4 → ROUND README/DECISIONS → NNN 任务卡）

## P0-index

| 产出                                            | 动作                                                   |
| ----------------------------------------------- | ------------------------------------------------------ |
| 加固仓库 **活任务卡** §1–§13                    | Plan 各 phase 写入                                     |
| `EXECUTION_INDEX.md` 草稿                       | §0–§6                                                  |
| `research/plan-boot.md` + **Phase P0 complete** | Plan-only                                              |
| `context_pack.json`                             | `uv run python scripts/context_router.py --task <dir>` |

## Plan 专属（不进冻结任务卡 §14 之外）

| Phase | Skill                       | 产出落点                    |
| ----- | --------------------------- | --------------------------- |
| 3.5   | to-issues                   | 活任务卡 §9 垂直切片        |
| 5a    | planning-and-task-breakdown | 活任务卡 §9 + 索引 §1       |
| 5b    | writing-plans               | 索引 §1 RED/GREEN + §2 验收 |
| 5d    | doubt-driven-development    | AUDIT §1/§2 + 索引 §3       |

## 冻结（v4 三件套）

```bash
python .trellis/scripts/task.py freeze-task-card <task-dir> --source docs/implementation_tasks/.../NNN_*.md
python .trellis/scripts/task.py generate-manifests <task-dir>   # 通常 freeze-task-card 已调用
python .trellis/scripts/task.py validate-plan-freeze <task-dir>  # exit 0
python .trellis/scripts/task.py start <task-dir>                  # 用户批准后
```

`plan-skill-reads.jsonl` 每条 Read 一行。完整协议：`.trellis/spec/guides/complex-task-planning-protocol.md` §0.0。
