# Agent 07 — 解耦性、嵌套与工程细节审计报告

审计日期：2026-06-21。角色边界：只审计代码/模块之间的解耦性、嵌套、模块边界与工程细节。按用户要求只报告，不修复。

## 工具与 skill

| skill / 工具          | 用途                              | 命令或依据                                                                                     | 结果                                      |
| --------------------- | --------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------- |
| codebase-design       | seam、interface、deep module 审查 | DataSourceService、Layer1 ingestion                                                            | service seam 清晰，ingestion 外部接口偏重 |
| code-simplification   | 深层嵌套、重复 helper、长函数审查 | `ingestion.py`、evidence helpers                                                               | 可拆分点明显                              |
| module boundary tests | import 边界验证                   | `pytest tests/test_module_boundaries.py -q --basetemp=.audit-sandbox/pytest-9agent-boundaries` | PASS，4 passed                            |
| source route tests    | datasource routing seam 验证      | `pytest tests/test_source_route_planner.py -q --basetemp=.audit-sandbox/pytest-9agent-route`   | PASS，6 passed                            |

## 发现项

| ID       | 等级 | 问题                                                      | 证据                                                        | 影响                           | 状态      | 解决方案                                          |
| -------- | ---- | --------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------ | --------- | ------------------------------------------------- |
| A7-P1-01 | P1   | 解耦审查不能掩盖关键行为失败                              | targeted phase3/4 与 full pytest FAIL                       | 即使边界测试绿，当前不能 PASS  | NOT FIXED | 先修复 evidence 测试                              |
| A7-P2-01 | P2   | `Layer1ObservationIngestionService` 承担过多职责          | `ingestion.py` 同时含 route、fetch、commit、evidence export | 修改一个阶段容易影响其他阶段   | NOT FIXED | 抽出 evidence export、sandbox path、commit 子模块 |
| A7-P2-02 | P2   | Phase evidence 逻辑与业务 ingest 逻辑嵌在同一文件         | phase2/3/4 capture functions 与 service class 同文件        | 审计路径变更会影响业务代码审查 | NOT FIXED | 将证据生成作为独立 internal seam                  |
| A7-P2-03 | P2   | 既有 deferred 中仍有 orchestrator handler registry 未抽取 | registry D7-P1-1、R2-RISK-1                                 | 后续 job 类型扩展耦合风险      | DEFERRED  | 后续提取 handler registry 并加 pytest             |
| A7-P2-04 | P2   | 脚本包装仍有 packaging deferred                           | registry D7-P2-2                                            | 长期工程规范风险               | DEFERRED  | 后续用正式安装入口替代临时路径处理                |
| A7-P3-01 | P3   | 未跟踪临时文件                                            | `backend/app/storage/path_compat.py`                        | diff 噪音                      | NOT FIXED | 手动删除                                          |

## 验证摘要

模块边界测试 PASS，source route planner PASS，raw store PASS；但 full pytest、Layer1 evidence targeted 和 Layer1 E2E 均 FAIL。

## 评分与结论

总分：86/100。FAIL。达到 95 分的最小清单：修复关键测试；拆分 ingestion evidence 逻辑；关闭或重新登记 orchestrator/packaging deferred；清理未跟踪文件。
