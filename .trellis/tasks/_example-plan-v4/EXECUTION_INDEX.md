# 执行索引 — Plan v4.2 Slim 金样

> **v4.2 计划正文：** `EXECUTION_PLAN.md`  
> **协议：** Slim Plan · 无 `frozen/` · 无 `research/` 冻结工件

## 0. 冻结元数据

| 字段          | 值                                                  |
| ------------- | --------------------------------------------------- |
| slug          | `_example-plan-v4`                                  |
| protocol      | `4.2`                                               |
| execute_entry | `EXECUTION_PLAN.md`                                 |
| source_card   | `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md` |

## 1. 步骤（Execute · v4.2）

| Step | 计划内锚点 | RED 命令 | GREEN 命令 | 完成标记          |
| ---- | ---------- | -------- | ---------- | ----------------- |
| 9.0  | Boot       | 见切片   | 见切片     | `[x]` + 代码/测试 |
| 9.1  | EX-01      | 见切片   | 见切片     | `[x]` + 代码/测试 |

> 证据 = 代码/测试/pytest。

## 2. AC ↔ 测试 / 验收

| AC   | 测试 / 命令                                                                                         | 通过条件 |
| ---- | --------------------------------------------------------------------------------------------------- | -------- |
| AC-1 | `uv run pytest tests/test_trellis_validate_plan.py -k "passesWithArtifacts or passesExamplePlanV4"` | 全绿     |

### 2.1 四层验收（Tier）

| 层  | 命令                                                                                                   | 环境     |
| --- | ------------------------------------------------------------------------------------------------------ | -------- |
| A   | `uv run pytest -q tests/test_trellis_validate_plan.py -k "passesWithArtifacts or passesExamplePlanV4"` | local/ci |

## 3. 必须读原文（manifest · 自动生成 jsonl）

| path                                                 | manifest  | audience | extract        | for       |
| ---------------------------------------------------- | --------- | -------- | -------------- | --------- |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | must-read | execute  | test semantics | §9.0 Boot |
| `tests/test_trellis_validate_plan.py`                | must-read | execute  | AC test        | AC-1      |

## 5. Audit 追溯集（v4.2 Slim）

| 类别     | 文件                | 用途         |
| -------- | ------------------- | ------------ |
| 计划正文 | `EXECUTION_PLAN.md` | AC · 步骤    |
| manifest | 本文 §3             | 外部必读路由 |
