# Agent 02 — 设计偏差审计报告

审计日期：2026-06-21。角色边界：只核对当前实现与设计、契约、计划文档之间的偏差，区分实现偏差与设计缺口。按用户要求只报告，不修复。

## 边界与工具

本次不连接外部真实系统，不改设计文档，不改代码。依据 `docs/ROUND3_HANDOFF.md`、`ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`docs/AUDIT_DEFERRED_REGISTRY.md`、Batch2.5 归档 audit report 与本轮 pytest 结果。

| skill / 工具                        | 用途                         | 命令或依据                                                                                         | 摘要                             |
| ----------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------- |
| code-review-and-quality             | 文档与实现一致性审查         | 设计文档 + 测试结果                                                                                | 发现归档 PASS 与当前测试失败冲突 |
| test-driven-development             | 用测试验证设计 AC 是否落地   | targeted phase3/4 pytest；Layer1 E2E pytest                                                        | evidence artifact AC 失败        |
| registry / staged acceptance review | 判断 deferred 是否为合法缺口 | `docs/AUDIT_DEFERRED_REGISTRY.md`                                                                  | 多项缺口已登记                   |
| 生产等价验证                        | 验证 Batch2.5 gate           | `pytest tests/test_batch25_production_data_gate.py -q --basetemp=.audit-sandbox/pytest-9agent-b25` | PASS：4 passed                   |

## 发现项

| ID       | 等级 | 类型     | 问题                                                           | 证据                                               | 影响                               | 状态      | 解决方案                                                 |
| -------- | ---- | -------- | -------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------- | --------- | -------------------------------------------------------- |
| A2-P1-01 | P1   | 实现偏差 | Batch2.5 phase3/phase4 证据导出当前失败                        | targeted pytest 2 failures                         | 设计 AC 未在当前工作树通过         | NOT FIXED | 修复 evidence sandbox 路径稳定性并重跑全量回归           |
| A2-P2-01 | P2   | 设计缺口 | Batch2.75 外部真实源试点尚未执行                               | registry R3-B2.75-01 DEFERRED                      | 不能宣称外部真实源已验证           | DEFERRED  | 按 Batch2.75 gate 执行或继续显式延期                     |
| A2-P2-02 | P2   | 设计缺口 | `specs/schema/schema.sql` 滞后于 migration 011，缺 `axis_*` 表 | registry B2.5-O-02                                 | schema 读者可能误判 runtime 表结构 | DEFERRED  | 同步 schema.sql 或明确 migration 011 为唯一 runtime 口径 |
| A2-P2-03 | P2   | 设计缺口 | `axis_observation` 时间顺序约束未下沉到 DB CHECK               | registry B2.5-O-03                                 | DB 层不能独立拒绝时间反序          | DEFERRED  | 后续迁移添加 CHECK 或 ADR 接受 app-layer                 |
| A2-P2-04 | P2   | 流程偏差 | runtime contract 要求 `uv.lock`，但根目录 tree 未显示该文件    | `specs/contracts/runtime_versions.md`；根目录 tree | 依赖可复现性低于设计要求           | NOT FIXED | 提交 lockfile 或修订 contract                            |
| A2-P2-05 | P2   | 文档偏差 | 归档 audit report 标记 PASS 但仍有 pending agent output        | `.trellis/.../audit.report.md` §3                  | 复核成本上升                       | NOT FIXED | 补齐 final 摘要或删除 pending 文案                       |
| A2-P3-01 | P3   | 审计污染 | 本轮误创建未跟踪 `backend/app/storage/path_compat.py`          | `show_changes`                                     | diff 审查噪音                      | NOT FIXED | 手动删除，不提交                                         |

## 验证摘要

全量 pytest：FAIL，2 failures。targeted phase3/4：FAIL。Layer1 ingestion E2E：FAIL。Batch2.5 生产等价 gate：PASS，4 passed。前端 typecheck/test/build：PASS。

## 评分与结论

总分：82/100。FAIL。达到 95 分的最小清单：修复 evidence artifact 失败；处理 `uv.lock` 合同；同步 schema/迁移口径；补齐归档 audit 摘要；明确 Batch2.75 状态。
