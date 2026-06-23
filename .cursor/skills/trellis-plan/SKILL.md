---
name: trellis-plan
description: "Complex-task Plan. MUST Read when status=planning. Blocks freeze until P0-index + validate-plan-freeze pass."
---

# Trellis Plan（v3 · 薄 skill）

> **读者：Plan agent** · **禁止：** 未完成 P0 即写 MASTER §5–§11 或 `task.py start`

## 必读（按序）

1. 本文件 + **`agent-toolchain.md`**（根目录）+ `.trellis/spec/guides/plan-skill-paths.yaml`
2. **模板：** `.trellis/spec/guides/templates/MASTER.plan.md`
3. **索引模板：** `.trellis/spec/guides/templates/source-index.md`
4. `docs/implementation_tasks/`（README → GLOBAL×4 → ROUND README/DECISIONS → NNN 任务卡）

## P0-index（合并原 P0i/P0o）

| 产出                                            | 动作                                                   |
| ----------------------------------------------- | ------------------------------------------------------ |
| `research/source-index.md` §A–§C + **索引完整** | 血缘 + manifest + 六类                                 |
| `research/plan-boot.md` + **Phase P0 complete** | 用户目标、依赖、AC 草稿                                |
| `context_pack.json`                             | `uv run python scripts/context_router.py --task <dir>` |

## Plan 专属（不进 MASTER §11）

| Phase | Skill                       | 产出                |
| ----- | --------------------------- | ------------------- |
| 3.5   | to-issues                   | 垂直切片工单        |
| 5a    | planning-and-task-breakdown | MASTER §8           |
| 5b    | writing-plans               | MASTER §5 + §9 骨架 |
| 5d    | doubt-driven-development    | AUDIT §2 修订       |

其余 phase → `plan-skill-paths.yaml`。

## 冻结

```bash
python .trellis/scripts/task.py validate-plan-freeze <task-dir>  # exit 0
python .trellis/scripts/task.py start <task-dir>                  # 用户批准后
```

`plan-skill-reads.jsonl` 每条 Read 一行。完整协议：`.trellis/spec/guides/complex-task-planning-protocol.md`。
