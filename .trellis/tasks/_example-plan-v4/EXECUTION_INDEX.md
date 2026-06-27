# 执行索引 — Plan v4 参考

> P0i：索引完整（v4 输入清单门禁）

## 0. 冻结元数据

| 字段        | 值                                                  |
| ----------- | --------------------------------------------------- |
| slug        | `_example-plan-v4`                                  |
| source_card | `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` |
| frozen_card | `frozen/GLOBAL_TASK_TEMPLATE.md`                    |

## 1. 步骤与证据（Execute）

| Step | 任务卡锚点 | RED 命令 | GREEN 命令 | 证据路径                               |
| ---- | ---------- | -------- | ---------- | -------------------------------------- |
| 9.0  | Boot       | `true`   | `true`     | `execute-evidence/9.0-{red,green}.txt` |

## 2. AC ↔ 测试 / 验收

| AC   | 测试 / 命令                                            | 通过条件 |
| ---- | ------------------------------------------------------ | -------- |
| AC-1 | `uv run pytest tests/test_execution_index_protocol.py` | 全绿     |

## 3. 必须读原文（manifest · 自动生成 jsonl）

| path                                                 | manifest  | audience | extract        | for       |
| ---------------------------------------------------- | --------- | -------- | -------------- | --------- |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read | execute  | test semantics | §9.0 Boot |

## 4. 已并入冻结任务卡

> Execute **不读** `research/*` Plan 草稿（三件套：frozen + 本文 + implement.jsonl）。

| 来源      | 并入 | 摘要           |
| --------- | ---- | -------------- |
| plan-boot | —    | 样板无额外内联 |

## 5. Audit 追溯集

| 类别   | 文件                             |
| ------ | -------------------------------- |
| frozen | `frozen/GLOBAL_TASK_TEMPLATE.md` |
