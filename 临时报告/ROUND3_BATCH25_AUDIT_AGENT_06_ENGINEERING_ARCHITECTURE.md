# Agent 06 — 规范性、工程质量与架构设计审计

## 1. 独立角色边界

本 agent 仅审计工程规范、执行规则、模块边界、架构设计一致性与发布卫生；不替代业务完成度、性能或数据库专项判断。

## 2. 使用的有效 skill / 工具

| 名称                              | 用途                                            | 执行命令或依据                                                                                                                                     | 结果                                                                     |
| --------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| codebase-design skill             | 深模块、seam、interface、adapter 边界审计       | 已加载；对照 SourceRoutePlan/DataSourceService/WriteManager/Layer1                                                                                 | 关键 seam 存在，但 Layer1 ingestion 模块过深且混责                       |
| documentation-and-adrs skill      | ADR/registry/任务文档规范性审计                 | 已加载；读取 018A/018B/registry/final update                                                                                                       | registry 有 trace，但 schema authority 与 live pilot deferred 需显式继承 |
| api-and-interface-design skill    | 契约优先、接口稳定性审计                        | 已加载；检查 source route/service/write contract                                                                                                   | 接口方向正确；schema contract drift 降分                                 |
| pytest 工程规范套件               | 执行规则、manifest、module boundary、docs index | `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q` | exit 0                                                                   |
| CodexPro show_changes/read/search | 检查工作区、架构文档、异常路径                  | `show_changes`; read/search docs/code                                                                                                              | 工作区非 clean，有异常 untracked 路径                                    |

## 3. 测试与验证

| 类型          | 命令                                                                                                                                               | 结果                                                 |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 工程规范/边界 | `pytest tests/test_module_boundaries.py tests/test_global_execution_rules.py tests/test_documentation_index.py tests/test_manifest_protocol.py -q` | exit 0                                               |
| 全量回归      | `pytest -q`                                                                                                                                        | exit 0；收集 589 项；1 skip observed                 |
| 前端工程      | `npm run typecheck`; `npm test`; `npm run build`                                                                                                   | 全部 exit 0                                          |
| 工作区检查    | `show_changes`                                                                                                                                     | 非 clean；存在 modified/untracked 文件与报告新增文件 |

## 4. P0/P1/P2/P3

### P0

无。

### P1

| ID        | 问题                                                            | 证据                                                    | 影响                                             | 当前阶段可修复?             | 修复状态 | 解决方案                                                                 |
| --------- | --------------------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------ | --------------------------- | -------- | ------------------------------------------------------------------------ |
| A06-P1-01 | 架构状态不能从 Batch2.5 直接跳到 production-ready Batch3        | `018B` 与 policy 要求 Batch2.75；`R3-B2.75-01` DEFERRED | 会让后续 Layer2+ 建立在未验证 live-source 假设上 | 否，需独立 Batch2.75        | 未修复   | Batch3 前执行或 re-defer Batch2.75，并在 MASTER 中继承 staged limitation |
| A06-P1-02 | 规范 authority 分裂：migration 011 vs `specs/schema/schema.sql` | `schema.sql` 无 axis 表；migration 011 有 axis 表       | 工程实现可运行，但规范入口不完整                 | 是，但用户禁止文档/代码变更 | 未修复   | 修复 schema spec 或在 MIGRATION_COVERAGE/ADR 中明确 migration authority  |

### P2

| ID        | 问题                                                          | 证据                                            | 影响                                                      | 当前阶段可修复?                   | 修复状态 | 解决方案                                             |
| --------- | ------------------------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------- | --------------------------------- | -------- | ---------------------------------------------------- |
| A06-P2-01 | 工作区非 clean 且含异常 untracked `=`, `frontend/=` 路径      | `show_changes`                                  | release/merge review 难以区分审计报告、测试产物、业务变更 | 是                                | 未修复   | release 前清理或记录保留原因；报告文件与测试产物分组 |
| A06-P2-02 | `ingestion.py` 同时包含 runtime service 与 evidence generator | A2 ponytail report                              | 架构分层不够清晰                                          | 是                                | 未修复   | 运行时模块与证据生成模块分离                         |
| A06-P2-03 | live pilot policy 已存在但实施任务仍未完成                    | `018B` status planning task card；`R3-B2.75-01` | 架构路线完整但执行不闭环                                  | 否，需要授权和独立 implementation | 未修复   | 创建/执行 Batch2.75 implementation task              |

### P3

| ID        | 问题                                                                          | 影响                         | 解决方案                            |
| --------- | ----------------------------------------------------------------------------- | ---------------------------- | ----------------------------------- |
| A06-P3-01 | `docs/ROUND3_HANDOFF.md` 中旧 narrative 仍可能被误读为 Batch2.5 execute-ready | 用户已纠正；归档 task 是权威 | 在总报告中明确以 archived task 为准 |

## 5. 评分

**90 / 100 — FAIL**

扣分依据：Batch2.75 未闭环 -4；schema authority drift -3；workspace hygiene -2；runtime/evidence layering -1。

## 6. 达到 95+ 的最小修复清单

1. Batch2.75 状态必须明确：执行 live pilot 或正式 re-defer 且禁止生产假设。
2. 修复 schema authority 分裂。
3. 清理/解释工作区异常 untracked 路径和审计产物。
4. 拆分 Layer1 ingestion runtime/evidence 层。

## 7. 结论

本维度 **FAIL**。工程门禁测试通过，但架构/规范层仍有足以阻止 95+ 的 gate 与 authority 问题。
