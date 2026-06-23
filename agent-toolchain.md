# Agent 工具路由（场景 · 全员必读）

> 不按角色列全表。角色**必做**见：  
> `plan-skill-paths.yaml` · `execute-skill-paths.yaml` · `audit-skill-paths.yaml`  
> 任务上下文见活动任务目录 `implement.jsonl` / `audit.jsonl`。

## GitNexus MCP（按场景）

| 场景                       | 用                                                     | 不用               |
| -------------------------- | ------------------------------------------------------ | ------------------ |
| 不熟模块、找入口           | `query` + skill `gitnexus-exploring`                   | 全库盲 grep        |
| **改函数/类前**            | MCP `impact()` + `gitnexus-impact-analysis`            | 直接改             |
| 提交前看改动面             | MCP `detect_changes()`                                 | 只看 git diff 肉眼 |
| 测试红、栈对不上、回归不明 | `systematic-debugging` → 仍卡住则 `gitnexus-debugging` | 反复猜改           |
| rename / 拆模块 / 提取     | MCP `rename` + `gitnexus-refactoring`                  | find-replace       |
| 不知道 MCP 参数            | `gitnexus-guide`                                       | 乱试工具           |

**阶段锁死（非可选）：** Plan 1a/1b、Execute boot+改码、Audit 7.pre + 各维 ≥1 次 query/context — 见各 phase yaml。

## Skill 歧义（相似项选一）

| 场景                   | 用                                                                   | 不用                  |
| ---------------------- | -------------------------------------------------------------------- | --------------------- |
| Plan 质问需求          | `grill-me` / `interview-me` / `grill-with-docs`（三选一，plan yaml） | `brainstorming`       |
| Plan 垂直切片          | `to-issues` + `planning-and-task-breakdown`                          | 手写 MASTER §8 无切片 |
| Execute 先写失败测试   | `test-driven-development`                                            | 先写实现              |
| Execute 实现与测试规范 | `karpathy-guidelines` + `testing-guidelines`                         | 自创风格              |
| Execute 验规范         | **等 Audit A1**                                                      | `trellis-check`       |
| Audit 对抗性质疑       | 各维 `doubt-driven-development`（冻结在 audit-agent 模板）           | 只走 happy path       |

## Trellis CLI（常用）

| 场景              | 命令                                                              |
| ----------------- | ----------------------------------------------------------------- |
| Plan 冻结         | `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` |
| Execute 步进      | `validate-execute-step` / `validate-execute-handoff`              |
| 刷新 context_pack | `uv run python scripts/context_router.py --task <task-dir>`       |
| 地图/catalog 过期 | `uv run python scripts/loop_maintain.py`（`--fix` 写回）          |

## 读本文件之后

- **Plan** → `trellis-plan` skill + `plan-skill-paths.yaml`
- **Execute** → `implement.jsonl` 每条 + `trellis-execute` + `execute-skill-paths.yaml`
- **Audit** → `AUDIT.plan.md` + `audit-skill-paths.yaml` + 本维 `agents/*.md`
