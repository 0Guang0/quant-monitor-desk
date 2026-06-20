# Agent 03 — Ponytail / 简化冗余审计报告

审计日期：2026-06-21。角色边界：只按 ponytail/code-simplification 理念审计已实现代码是否可简化、是否过度冗余，不评价业务完成度本身。按用户要求只报告，不修复。

## 边界与工具

当前环境未暴露可执行的独立 `ponytail` CLI。项目文档说明在 CLI 不可用时，以 `ponytail-review` / `code-simplification` skill 作为等价路径。本报告采用该等价路径，并用 pytest 结果约束“不得为简化改变行为”。

| skill / 工具             | 用途                                               | 命令或依据                                                                      | 摘要                                                             |
| ------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| code-simplification      | Chesterton's Fence、长函数、重复逻辑、深层嵌套审查 | 已读取 skill；审查 `backend/app/layer1_axes/ingestion.py`、mapper、raw store 等 | 发现 ingestion facade 过长且证据函数路径逻辑重复                 |
| ponytail-review 等价路径 | 过度工程/可删减审查                                | `docs/decisions/README.md` 对 ponytail 等价路径的说明；归档 A2 audit            | CLI 不可用，不计入；skill 等价路径计入                           |
| pytest regression        | 防止建议破坏行为                                   | targeted phase3/4、Layer1 E2E、全量 pytest                                      | 当前已有失败，任何简化前必须先修正行为                           |
| static search/read       | 查找重复路径和巨型模块                             | `CodexPro.search/read`                                                          | `ingestion.py` 约 1506 行，多个 phase evidence helper 在同一文件 |

## 发现项

| ID       | 等级 | 问题                                               | 证据                                                                                                            | 影响                                              | 状态      | 解决方案                                                                           |
| -------- | ---- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------- | ---------------------------------------------------------------------------------- |
| A3-P1-01 | P1   | 当前关键测试失败，任何简化都不能安全进行           | targeted phase3/4 FAIL；全量 pytest FAIL                                                                        | 不满足“Preserve Behavior Exactly”前提             | NOT FIXED | 先修复 evidence artifact，再做简化重构                                             |
| A3-P2-01 | P2   | `backend/app/layer1_axes/ingestion.py` 职责过多    | 文件约 1506 行，含 route preview、micro fetch、commit、evidence export、markdown/json formatting                | 新成员理解成本高，局部修复易引发副作用            | NOT FIXED | 分离 phase evidence writer、route preview facade、commit service；保持外部接口不变 |
| A3-P2-02 | P2   | Phase3/Phase4 sandbox 路径与 evidence 写入逻辑重复 | `capture_task_phase3_evidence` 与 `capture_task_phase4_evidence` 都构建 sandbox、DB、data_root、fixture service | 路径策略不一致时容易出现本次 Windows 深层路径失败 | NOT FIXED | 抽取共享 sandbox path builder 与 evidence IO helper，增加 regression tests         |
| A3-P2-03 | P2   | 归档 ponytail/PASS 证据不够直达                    | audit.report 仍有 pending agent output                                                                          | 复核者需要多跳追踪 research 子文件                | NOT FIXED | 在归档 report 中内联 A2 final summary                                              |
| A3-P3-01 | P3   | 本轮误创建未跟踪临时文件                           | `backend/app/storage/path_compat.py`                                                                            | diff 噪音                                         | NOT FIXED | 手动删除，不提交                                                                   |

## 验证摘要

- `pytest tests/test_layer1_observation_ingestion.py::...phase3... ...phase4...`：FAIL。
- `pytest tests/test_layer1_ingestion_gates.py tests/test_layer1_observation_ingestion.py`：FAIL。
- `pytest tests/test_raw_store.py`：PASS，15 passed。
- `pytest tests/test_module_boundaries.py`：PASS，4 passed。

## 评分与结论

总分：84/100。FAIL。扣分依据：核心行为测试失败；大模块可简化空间明显；sandbox/evidence 路径逻辑重复。达到 95 分的最小清单：先修复 P1 行为失败，再以行为不变方式拆分 evidence/sandbox helper，补齐归档 ponytail 摘要并全量回归通过。
