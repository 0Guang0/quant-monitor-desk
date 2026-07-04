# `_example-plan-v4` — Plan v4.2 Slim 金样（只读）

**新复杂任务默认参照本目录。** v4.1 legacy 已归档至 `.trellis/tasks/archive/2026-07/_example-plan-v41-legacy/`。

| 文件                                              | 角色                                     |
| ------------------------------------------------- | ---------------------------------------- |
| `EXECUTION_PLAN.md`                               | Execute 计划正文 SSOT（implement slot1） |
| `EXECUTION_INDEX.md`                              | 机器索引 §1/§3（implement slot2）        |
| `AUDIT.plan.md`                                   | 审计矩阵                                 |
| `implement.jsonl` / `audit.jsonl` / `check.jsonl` | `generate-manifests` 生成                |

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/_example-plan-v4 5e
python .trellis/scripts/task.py generate-manifests .trellis/tasks/_example-plan-v4
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/_example-plan-v4
```
