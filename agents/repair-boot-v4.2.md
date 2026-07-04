# Repair Boot — Plan v4.2

> **Leading word — 无遗留：** Repair 关账须 ledger 全覆盖 + `uv run pytest -q` 全绿。  
> **legacy v4.1：** `agents/repair-boot-v4.1.md`（ENTRY 包任务）

## Boot 读序

| #   | 文件                                                   | 用途         |
| --- | ------------------------------------------------------ | ------------ |
| 1   | `agent-toolchain.md`                                   | 工具路由     |
| 2   | `research/audit-repair-ledger.md` 或 audit.report §4.1 | findings 源  |
| 3   | `REPAIR.plan.md`                                       | §1 修复行    |
| 4   | `repair-skill-registry.md`                             | Skill 栈     |
| 5   | `EXECUTION_PLAN.md`                                    | 计划 AC/约束 |
| 6   | `EXECUTION_INDEX.md` §2.1                              | 复验命令     |

## 收尾复验（必做）

```bash
uv run pytest -q   # exit 0
python .trellis/scripts/task.py validate-repair-close <task-dir>   # exit 0
```

规则同 v4.1：修根因 · A9 建账/关账 · 阶段外置登记两份文档。
