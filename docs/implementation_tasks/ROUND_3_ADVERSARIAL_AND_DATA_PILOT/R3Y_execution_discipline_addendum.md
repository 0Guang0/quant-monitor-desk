# R3Y_execution_discipline_addendum — 下一批执行纪律补充

本补充适用于以下三张任务卡与对应 PROMPT：

- `R3Y_post_r3x_strict_adversarial_audit.md` / `PROMPT_18_review_round3_post_r3x_strict_adversarial_audit.md`
- `R3Y_real_data_staged_pilot_v2.md` / `PROMPT_19_feature_round3_real_data_staged_pilot_v2.md`
- `R3Y_readonly_data_health_v1.md` / `PROMPT_20_feature_round3_readonly_data_health_v1.md`

## 1. 必须使用 /to-issues skill

任务拆分必须使用 `/to-issues` skill。切片必须遵守 tracer-bullet vertical slice 原则：

- 每个 issue 是一条端到端薄切片，不是按单一层级横切。
- 每个 issue 必须能独立领取、独立验证、独立产出 evidence。
- 每个 issue 必须写明：标题、建设/验证内容、验收标准、依赖项、证据输出、测试或验证计划。
- 若 issue 存在依赖，必须先执行 blocker issue。
- 执行计划不得只写总目标；必须逐 issue 说明实现范围、边界、测试和 done criteria。

## 2. 代码实现纪律

任何正式代码实现必须遵守：

- `/karpathy-guidelines`
- `/tdd`
- `/ponytail` full

要求：

- 任何正式代码实现前必须先写或补 RED test。
- RED evidence 必须保存到 task-local `execute-evidence/`。
- 实现必须保持最小、清晰、可读，避免横向大改。
- 必须优先减少重复、合并重复路径、维护单一权威入口。
- 不得为绕过失败而删除 guard、降低约束或扩大默认权限。

## 3. 测试纪律

任何新增或修改测试必须遵守 `/testing-guidelines`。

要求：

- 每个新增或修改的测试函数必须用 docstring 或就近注释说明：覆盖范围、测试对象、目的/目标。
- 测试必须覆盖行为和 runtime path，不得只覆盖 import、存在性或表面字段。
- 可以修复测试表达方式，但不能改变测试原始目的/目标来换取通过。
- 代码修复后必须运行完整测试套件；如果因环境限制无法运行，必须记录命令、失败原因和风险。
- 定向测试和完整测试都必须进入 merge gate report。

## 4. 文档语言

文档、任务卡、执行计划、审计结论尽量使用中文。涉及代码、路径、命令、契约字段、branch 名称、source_id、domain、rule_id、status 等专用用语时可以保留英文。
