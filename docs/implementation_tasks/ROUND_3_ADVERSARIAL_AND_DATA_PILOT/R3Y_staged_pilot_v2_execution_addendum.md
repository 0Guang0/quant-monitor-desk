# R3Y_staged_pilot_v2_execution_addendum

适用任务卡：`R3Y_real_data_staged_pilot_v2.md`。

执行 `feature/round3-real-data-staged-pilot-v2` 前，必须读取并遵守本补充。

## /to-issues skill

Plan 阶段必须使用 `/to-issues` skill。每个 issue 必须是 tracer-bullet vertical slice：

- 可独立领取
- 可独立验证
- 端到端覆盖相关集成行为
- 包含标题、建设内容、验收标准、依赖项、证据输出、测试计划

不得只写总目标，也不得按单一技术层级横切。

## 实现纪律

任何正式代码实现必须遵守：

- `/karpathy-guidelines`
- `/tdd`
- `/ponytail` full

正式代码实现前必须先写或补 RED test，并保存 RED/GREEN evidence。

## 测试纪律

任何新增或修改测试必须遵守 `/testing-guidelines`。

每个新增或修改测试必须注明：

- 覆盖范围
- 测试对象
- 目的或目标

代码修复后必须运行完整测试套件。可以修正测试表达方式，但不能改变测试目的或目标。

## 文档语言

文档和计划尽量使用中文；代码、路径、命令、branch 名称、source_id、domain、rule_id、status 等专用用语可以保留英文。
