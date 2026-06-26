# R3FR-01: Reference rules and license gate

## Goal

把参考项目采纳规则固化到 `reference_adoption_guardrails.yaml`，用 pytest 机读验收；不新建中央 `reference_adoption_inventory.md` 执行依赖。

## Acceptance Criteria

- [x] `reference_adoption_guardrails.yaml`：`status=active_round3fr`，含完整 `license_gate` + `completion_rules` + `required_tests`
- [x] `tests/test_reference_adoption_guardrails.py` 覆盖 R3FR-01 §5 + 对抗审计补强（scripts 扫描、AST trading def、任务卡 `reference_project`）
- [x] `README.md` / `PROJECT_IMPLEMENTATION_ROADMAP.md` / `MODULE_COMPLETION_RATING.md` 交叉引用护栏 SSOT
- [x] R3FR-02..07 采纳卡含 `reference_project:` 块

## Notes

- 分支：`chore/round3fr-reference-rules-license-gate`
- 源路由边界仍由 `test_module_boundaries` / datasource contracts 覆盖，不在本批重复
- 下一批：R3FR-02 + R3FR-06（data health + CLI 垂直切片）
