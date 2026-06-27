---
name: trellis-plan
description: "Complex-task Plan. MUST Read when status=planning. Blocks freeze until P0-index + 5e consolidation + validate-plan-freeze pass."
---

# Trellis Plan（v4 · 薄 skill）

> **读者：Plan agent** · **禁止：** 未完成 P0 即写冻结三件套或 `task.py start`  
> **原则：** `research/*` = Plan 草稿；**Execute 只读** `frozen/*.md` + `EXECUTION_INDEX.md` + `implement.jsonl`

## 必读（按序）

1. 本文件 + **`agent-toolchain.md`**（根目录）+ `.trellis/spec/guides/plan-skill-paths.yaml`
2. **模板：** `templates/EXECUTION_INDEX.md` · `templates/FROZEN_TASK_CARD.md` · `templates/AUDIT.plan.md` · `templates/research/plan-consolidation.md`
3. **填好后的执行计划样板：** `.trellis/tasks/_example-plan-v4/README.md`（v4 产出步骤；**非** Coordinator PLAYBOOK）
4. **遗留 v3：** `templates/MASTER.plan.md`（仅维护旧任务）
5. `docs/implementation_tasks/`（README → GLOBAL×4 → ROUND README/DECISIONS → NNN 任务卡）

## P0-index

| 产出                                            | 动作                                                   |
| ----------------------------------------------- | ------------------------------------------------------ |
| 加固仓库 **活任务卡** §1–§13                    | Plan 各 phase 写入                                     |
| `EXECUTION_INDEX.md` 草稿                       | §0–§6                                                  |
| `research/plan-boot.md` + **Phase P0 complete** | Plan-only                                              |
| `context_pack.json`                             | `uv run python scripts/context_router.py --task <dir>` |

## Plan 专属（草稿 → 5e 合并进 Execute SSOT）

| Phase  | Skill                       | 产出落点                                                  |
| ------ | --------------------------- | --------------------------------------------------------- |
| 3.5    | to-issues                   | 活任务卡 §9 垂直切片                                      |
| 5a     | planning-and-task-breakdown | 活任务卡 §9 + 索引 §1                                     |
| 5b     | writing-plans               | 索引 §1 RED/GREEN + §2 验收                               |
| 5d     | doubt-driven-development    | AUDIT §1/§2 + 索引 §3                                     |
| **5e** | **trellis-plan**            | **`research/plan-consolidation.md` + 活卡 + INDEX §4/§3** |

### Phase 5e（冻结前必做）

1. 填 `research/plan-consolidation.md`（模板），文末 **`Phase 5e complete`**
2. **可无损总结** → 写入**活任务卡**（`freeze-task-card` 后进 frozen）+ **INDEX §4** 登记
3. **不可精简** → `EXECUTION_INDEX` §3 `must-read`；**禁止**把路径只留在 `research/*`
4. **`prd.md`** 压成薄索引（`thin-index: true` 或 ≤25 行且引用 `frozen/`）
5. **禁止**把仅存在于 `research/*` 的可执行决策交付 Execute
6. 按 `templates/research/plan-consolidation.md` 分流表 + 文末自检；`validate-plan-freeze` **Triad gate**（协议 §5e.1）

## 冻结（v4 三件套 · 仅在 5e 之后）

```bash
python .trellis/scripts/task.py freeze-task-card <task-dir> --source docs/implementation_tasks/.../NNN_*.md
python .trellis/scripts/task.py generate-manifests <task-dir>
python .trellis/scripts/task.py validate-plan-phase <task-dir> 5e   # consolidation（freeze 前）
python .trellis/scripts/task.py validate-plan-freeze <task-dir>  # 含 5e 机械门
python .trellis/scripts/task.py start <task-dir>                  # 用户批准后
```

`plan-skill-reads.jsonl` 每条 Read 一行。完整协议：`.trellis/spec/guides/complex-task-planning-protocol.md` §0.0。
