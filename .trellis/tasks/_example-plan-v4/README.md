# Plan v4.1 参考任务

只读样板：演示 **Execution Bundle** 目录布局与 freeze 机械门。

| 项           | 路径                                                          |
| ------------ | ------------------------------------------------------------- |
| Execute 入口 | `research/00-EXECUTION-ENTRY.md`                              |
| 外部索引     | `research/EXTERNAL-INDEX.md`                                  |
| 切片 SSOT    | `research/to-issues-slices.md`                                |
| 活卡试点     | `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/` |

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/_example-plan-v4 5e
python .trellis/scripts/task.py generate-manifests .trellis/tasks/_example-plan-v4
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/_example-plan-v4
```

`implement.jsonl` slot1 = `frozen/` · slot2 = `research/00-EXECUTION-ENTRY.md`

Execute（v4.1）：证据 = 代码/测试/pytest；见 `.cursor/skills/trellis-execute/SKILL.md`。
