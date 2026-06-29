# 执行索引 — Plan v4.1 样板（薄指针）

> P0i：索引完整 · Execute 读 `research/00-EXECUTION-ENTRY.md`

## 0. 冻结元数据

| 字段          | 值                                                  |
| ------------- | --------------------------------------------------- |
| slug          | `_example-plan-v4`                                  |
| protocol      | `4.1`                                               |
| execute_entry | `research/00-EXECUTION-ENTRY.md`                    |
| source_card   | `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` |
| frozen_card   | `frozen/GLOBAL_TASK_TEMPLATE.md`                    |

## 1. 步骤与证据（Execute）

| Step | 任务卡锚点 | RED 命令 | GREEN 命令 | 证据路径                               |
| ---- | ---------- | -------- | ---------- | -------------------------------------- |
| 9.0  | Boot       | `true`   | `true`     | `execute-evidence/9.0-{red,green}.txt` |
| 9.1  | EX-01      | 见切片   | 见切片     | `execute-evidence/9.1-{red,green}.txt` |

## 2. AC ↔ 测试 / 验收

| AC   | 测试 / 命令                                            | 通过条件 |
| ---- | ------------------------------------------------------ | -------- |
| AC-1 | `uv run pytest tests/test_execution_index_protocol.py` | 全绿     |

## 3. 必须读原文（manifest · 自动生成 jsonl）

| path                                                 | manifest  | audience | extract        | for       |
| ---------------------------------------------------- | --------- | -------- | -------------- | --------- |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read | execute  | test semantics | §9.0 Boot |

> v4.1：slot2 = `research/00-EXECUTION-ENTRY.md`；包内 `research/*` 由 ENTRY §5.2 路由。

## 4. 已并入冻结任务卡

> v4.1：可执行规格在 **Execution Bundle**；本节仅登记 frozen 薄摘要指针。

| 来源 | 并入 | 摘要                      |
| ---- | ---- | ------------------------- |
| 活卡 | 指针 | GLOBAL_TASK_TEMPLATE 摘要 |

## 5. Audit 追溯集

| 类别   | 文件                             |
| ------ | -------------------------------- |
| frozen | `frozen/GLOBAL_TASK_TEMPLATE.md` |
| entry  | `research/00-EXECUTION-ENTRY.md` |
