# Repair Boot — Plan v4.1

> **Leading word — 无遗留：** Repair 关账须 ledger 全覆盖 + `uv run pytest -q` 全绿。

## Boot 读序（按序）

| #   | 文件                                                   | 用途        |
| --- | ------------------------------------------------------ | ----------- |
| 1   | `agent-toolchain.md`                                   | 工具路由    |
| 2   | `research/audit-repair-ledger.md` 或 audit.report §4.1 | findings 源 |
| 3   | `REPAIR.plan.md`                                       | §1 修复行   |
| 4   | `repair-skill-registry.md`                             | Skill 栈    |
| 5   | `EXECUTION_INDEX.md` §2.1                              | 复验命令    |
| 6   | ENTRY + §5.1 触及模块的 research 原文                  | 根因上下文  |

## Repair 规则

1. **修根因**，禁止 wrapper/假绿/静默降级
2. A9 建账：每项 disposition ∈ {**待修复**, **阶段外置**}
3. 关账：无 **待修复** 残留；每项 disposition ∈ {**已修复**, **阶段外置**}
4. **阶段外置**：关账前在 **`docs/quality/待修复清单.md`** + **`PROJECT_IMPLEMENTATION_ROADMAP.md`** 各新增一行；`audit.report.md` §4.4 与 ledger `登记位置` 一致
5. 证据 = 代码 + pytest，不写 handoff 长文

## 收尾复验（必做）

```bash
uv run pytest -q   # exit 0
python .trellis/scripts/task.py validate-repair-close <task-dir>   # exit 0
# + INDEX §2.1 Tier（与 REPAIR.plan 一致）
# 触 backend/docs/specs/authority_graph 时：uv run python scripts/loop_maintain.py
```

更新 `audit.report.md` §5 · `research/audit-repair-ledger.md`（**无待修复**；每条 disposition ∈ {已修复, 阶段外置}）。

## Boot 完成条件

- [ ] §4.3 / ledger 每项 disposition ∈ {已修复, 阶段外置}；**无** 待修复
- [ ] 凡 **阶段外置**：`docs/quality/待修复清单.md` + `PROJECT_IMPLEMENTATION_ROADMAP.md` 已新增行；§4.4 / ledger `登记位置` 可 diff 核对
- [ ] INDEX §2.1 + pytest 全绿
- [ ] 未改测试 purpose/目标换绿
