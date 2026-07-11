# task-17-cli-data-commands

> 流水线 **17**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据 CLI 正式入口（qmd-data data …）**

## 负责什么（业务视角）

运营与验收的正式命令面：`sync` / `backfill` / `full-load` / 相关子命令，统一 `AcceptanceReport` 信封、生产等价验收库接缝；禁止 replay/mock 冒充 live PASS。

## 上下游

| 方向     | 谁                                                               |
| -------- | ---------------------------------------------------------------- |
| **上游** | **task-11～16** Job 均已可调用 · **task-01～09** 管线组件        |
| **下游** | **task-18-scheduler**（调度内部调用同一 CLI 语义）· 运营/CI 验收 |

## 权威设计

- `MIGRATION_MAP.md` → specs/contracts/data_cli_contract.yaml

## 代码主区（实现时收窄）

```text
backend/app/cli/data_commands.py · phase1_acceptance（待正名）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
