# EXECUTION_PLAN — M-DATA-03（GAP only）

> **Execute SSOT：** `research/00-EXECUTION-ENTRY.md`  
> **切片 SSOT：** `research/to-issues-slices.md`

## GAP（freeze 前）

| GAP                          | 负责命令                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| `context_pack.json`          | `uv run python scripts/context_router.py --task .trellis/tasks/m-data-03-tier-a-live` |
| `EXECUTION_INDEX.md` §0 定稿 | Plan freeze 时                                                                        |
| `frozen/*.md`                | `task.py freeze-task-card`                                                            |
| `implement.jsonl`            | `task.py generate-manifests`                                                          |
| `AUDIT.plan.md`              | freeze 后或 Execute 末                                                                |
| Execute 代码/测试            | **不在 Plan 阶段**                                                                    |

## 下一步（用户批准后）

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/m-data-03-tier-a-live 5e
python .trellis/scripts/task.py freeze-task-card .trellis/tasks/m-data-03-tier-a-live --source docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md
python .trellis/scripts/task.py generate-manifests .trellis/tasks/m-data-03-tier-a-live
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/m-data-03-tier-a-live
python .trellis/scripts/task.py start .trellis/tasks/m-data-03-tier-a-live
```
