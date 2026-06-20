# Agent 08 — 性能占用与运行速度审计报告

审计日期：2026-06-21。角色边界：只审计性能占用、运行速度、资源限制与构建体积。按用户要求只报告，不修复。

## 工具与 skill

| skill / 工具                      | 用途                       | 命令或依据                                                                                                                                                        | 结果                                         |
| --------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| performance-optimization          | 先测量再判断瓶颈           | 归档 A6 perf、pytest 时间、frontend build size                                                                                                                    | 归档 A6 性能达标，但当前 evidence gate 失败  |
| observability-and-instrumentation | 检查证据是否能说明运行行为 | phase evidence、ResourceGuard 记录                                                                                                                                | phase3/4 evidence 当前不稳定                 |
| ResourceGuard tests               | 资源 gate 验证             | `pytest tests/test_resource_guard.py tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q --basetemp=.audit-sandbox/pytest-9agent-perf-layer1` | PASS                                         |
| 生产等价验证                      | 替代真实系统验证           | `pytest tests/test_batch25_production_data_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-b25`；归档 A6 audit-prod-path                                       | pytest 4 passed；归档 A6 为 0.444s / 58.09MB |

## 验证摘要

| 命令/证据                                                                                                                                                         | 结果                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `pytest tests/test_resource_guard.py tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q --basetemp=.audit-sandbox/pytest-9agent-perf-layer1` | PASS                              |
| `npm run build --prefix frontend`                                                                                                                                 | PASS；JS 190.75 kB，gzip 60.16 kB |
| 归档 A6 `audit-prod-path`                                                                                                                                         | PASS；elapsed 0.444s；RSS 58.09MB |
| targeted phase3/4 evidence tests                                                                                                                                  | FAIL                              |
| full pytest                                                                                                                                                       | FAIL                              |

## 发现项

| ID       | 等级 | 问题                                                     | 证据                                                         | 影响                                     | 状态      | 解决方案                                        |
| -------- | ---- | -------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------- | --------- | ----------------------------------------------- |
| A8-P1-01 | P1   | 性能路径的证据导出不稳定                                 | phase3/4 targeted FAIL                                       | 无法证明所有关键路径在当前环境可稳定运行 | NOT FIXED | 修复 evidence sandbox 路径后重跑性能与 E2E gate |
| A8-P2-01 | P2   | 归档性能数据通过，但当前工作树未重新跑 A6 benchmark 脚本 | A6 report 为历史证据；本环境脚本命令未在 safe allowlist 执行 | 当前性能只能部分确认                     | NOT FIXED | 在完整 shell 跑 A6 benchmark 并写入新证据       |
| A8-P2-02 | P2   | 前端体积当前可接受但无预算 gate                          | build 输出 190.75 kB / gzip 60.16 kB                         | 后续增长缺少自动拦截                     | NOT FIXED | 添加 bundle budget 或 CI size check             |
| A8-P2-03 | P2   | 外部真实源耗时未验证                                     | Batch2.75 仍 DEFERRED                                        | 无法评估真实网络延迟和重试               | DEFERRED  | Batch2.75 执行授权后的微窗口试点                |
| A8-P3-01 | P3   | 未跟踪临时文件                                           | `backend/app/storage/path_compat.py`                         | 轻微工程噪音                             | NOT FIXED | 手动删除                                        |

## 评分与结论

总分：88/100。FAIL。达到 95 分的最小清单：关键 evidence tests 绿；重新跑 A6 benchmark；添加体积预算；执行或明确延期 Batch2.75；清理未跟踪文件。
