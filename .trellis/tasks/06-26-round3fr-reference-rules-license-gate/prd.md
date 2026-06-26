# R3FR-01: Reference rules and license gate (re-execution)

## Goal

重跑参考项目治理：护栏契约、生产补齐覆盖地图边界、下游任务卡可执行性、规划文件业务口径与静态机读验收；**不修改 runtime 代码**，不新建中央 executable inventory。

## Acceptance Criteria (slices A–E)

- [x] **A** `reference_adoption_guardrails.yaml`：任务卡本地执行、`PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 仅为覆盖地图、禁止 runtime import 等 P0 模式
- [x] **B** `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` 首屏边界说明完整
- [x] **C** R3G/R3H/Batch04/Batch05 与 `029` 松散卡 redirect 审计通过
- [x] **D** `PROJECT_IMPLEMENTATION_ROADMAP.md`、`MODULE_COMPLETION_RATING.md`、`docs/implementation_tasks/README.md` 含「地图不是工单；任务卡才是工单」
- [x] **E** `tests/test_reference_adoption_guardrails.py`（含新增 planning/redirect 用例）+ docs index + `loop_maintain.py` 全绿

## Evidence

- 护栏测试：`uv run pytest tests/test_reference_adoption_guardrails.py -q`
- 文档索引：`uv run pytest tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q`
- Loop：`uv run python scripts/loop_maintain.py`

## Notes

- 下一批入口：**R3FR-02 + R3FR-06**（data health 垂直切片）
- SSOT：`specs/contracts/reference_adoption_guardrails.yaml`
