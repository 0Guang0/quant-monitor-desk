# Plan Input Context Bridge

> 本文件供 **Plan 阶段** 使用，用于把 `docs/implementation_tasks/**` 原始执行任务、原设计文档、规则、契约、定义与 `.trellis/tasks/**` 冻结详细计划建立追溯关系。它不是 Execute / Audit / Repair 的默认必读文件。

## 1. 三层模型

```text
设计文档 / 规则 / 契约 / 定义
        ↓
docs/implementation_tasks/** 原始执行任务
        ↓   Plan 阶段过滤、归并、去噪、总结、建立追溯索引
.trellis/tasks/** 详细计划与执行/审计 manifest
        ↓
Execute / Audit / Repair
```

## 2. 使用规则

- Plan agent 在把原始执行任务转写为 `.trellis/tasks/**/MASTER.plan.md`、`AUDIT.plan.md`、`REPAIR.plan.md` 与 jsonl manifest 前，必须读取本文件。
- Plan agent 必须先用当前 Round 的 `ROUND*_BATCH_IMPLEMENTATION_MAP.md` 确认当前批次、Item IDs、source bundle 与 manifest policy，再读取该批次对应的原始任务卡 / alias 执行文件及其输入文件。
- Execute / Audit / Repair 默认不直接读取本文件，也默认不直接读取 `docs/implementation_tasks/**` 原始任务卡。
- Execute 读取 `.trellis/tasks/**/MASTER.plan.md` 与 `implement.jsonl`；Audit 读取 `AUDIT.plan.md`、`audit.jsonl`/`check.jsonl` 与 MASTER 中的追溯索引；Repair 读取 `REPAIR.plan.md`。
- 原始任务卡只作为 Plan 阶段的范围、边界、输入声明。Plan 必须把仍然有效的上下文归并进 Trellis 计划；无法无损总结的上下文必须在 Trellis 计划中列明原文路径和读取原因。
- `docs/` 与 `specs/` 是设计文档、契约、定义、规则、计划、验收与治理资料目录，不是运行时代码目录，也不是功能实现地址。

## 3. Plan 阶段共同必读上下文

| 路径                                                         | Plan 使用原因                                                                                                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                                                  | 项目入口、docs/specs 非实现地址边界、旧口径禁止恢复、MANIFEST 角色说明                                                                            |
| `MIGRATION_MAP.md`                                           | 当前项目地图；定位模块设计文档、契约、规则、实现目录入口；Plan 冻结前回查遗漏                                                                     |
| `ROUND*_BATCH_IMPLEMENTATION_MAP.md`                         | 当前 Round 批次切片与索引入口；例如 Round3 使用 `ROUND3_BATCH_IMPLEMENTATION_MAP.md`，后续 Round 可改写为 `ROUND4_BATCH_IMPLEMENTATION_MAP.md`    |
| `docs/INDEX.md`                                              | 文档导航入口                                                                                                                                      |
| `docs/implementation_tasks/README.md`                        | 原始任务顺序、全局规则、任务库存                                                                                                                  |
| `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` | 未闭合项到原始执行任务卡的覆盖索引；Plan 必须用它把 registry 中目标批次相关 ID 映射进 MASTER/AUDIT AC、evidence、closeout 或 explicit re-deferral |
| `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`        | 原始任务执行边界；供 Plan 归并到 MASTER                                                                                                           |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`         | 测试策略与命名约束；供 Plan 归并到 MASTER/AUDIT                                                                                                   |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`        | 资源限制与低占用要求；供 Plan 归并到 MASTER §10                                                                                                   |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`          | 原始任务结构、验收命令、阶段化验收要求                                                                                                            |
| `specs/contracts/runtime_versions.md`                        | Python/Node/npm/锁文件与验收命令权威；若执行会用到则进入 implement/audit manifest                                                                 |
| `docs/quality/staged_acceptance_policy.md`                   | docs-only/backend/frontend/release 分层验收策略                                                                                                   |
| `docs/quality/PENDING_USER_DECISIONS.md`                     | 用户已拍板 D-01 至 D-12；Plan 不得让执行者重复询问                                                                                                |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                            | 延后项与 resolved gate 的权威登记                                                                                                                 |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                           | 已解决问题登记，避免重复修复或误判仍 OPEN                                                                                                         |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                         | 未解决问题登记，避免遗漏后续必须处理项                                                                                                            |

## 4. Trellis 详细计划路径索引

> 下列 `.trellis/tasks/**` 目录是 plan 阶段过滤无效信息后形成的详细执行计划、审计证据、repair 记录和 handoff 资料。Plan agent 可以用它们迁移历史上下文、建立新 MASTER 的 trace；Execute/Audit 是否读取其中某个文件，必须由当前 MASTER/AUDIT.plan/jsonl 显式决定。

| 原始任务范围                            | Trellis 详细计划 / 证据路径                                                                                                                                                                                          | Plan 处理要求                                                                                                                                  |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Round 0：`000`-`004`                    | `.trellis/tasks/archive/2026-06/06-17-round0-scaffold-audit/MASTER.plan.md`；同目录 `audit.report.md`、`REPAIR.plan.md`                                                                                              | 将仍有效的 scaffold 约束归并进当前 MASTER；已闭环修复只保留 trace                                                                              |
| Round 1：`005`-`010`                    | `.trellis/tasks/archive/2026-06/06-17-round1-foundation-audit/MASTER.plan.md`；同目录 `audit.report.md`、`REPAIR.plan.md`；`005` 另有 `.trellis/tasks/06-16-005-schema-init/MASTER.plan.md`                          | 优先使用已冻结 MASTER 作为历史实现事实；schema 任务必须追溯 migration 覆盖                                                                     |
| Round 2 Batch A：`011`、`012`           | `.trellis/tasks/archive/2026-06/06-17-round2-batch-a-sources/MASTER.plan.md`；同目录 `audit.report.md`                                                                                                               | 迁移 source registry / adapter contract 的有效约束                                                                                             |
| Round 2 Batch B：`013`                  | `.trellis/tasks/archive/2026-06/06-17-round2-batch-b-adapters/MASTER.plan.md`；同目录 `audit.report.md`；`docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md`                      | 迁移 adapter skeleton 与 Batch B 修复状态                                                                                                      |
| Round 2 Batch D：`014`                  | `.trellis/tasks/archive/2026-06/06-18-round2-batch-d-orchestrator/MASTER.plan.md`；同目录 `audit.report.md`、`repair.report.md`；`BATCH_D_STATUS.md`                                                                 | 迁移 orchestrator、runner、幂等与 repair 结论                                                                                                  |
| Round 2 Batch C：`015`、`016`           | `.trellis/tasks/archive/2026-06/06-17-round2-batch-c-validation-conflict/MASTER.plan.md`；同目录 `audit.report.md`、`REPAIR.plan.md`、`REPAIR.report.md`；`BATCH_C_LEDGER.md`、`BATCH_C_REPAIR_STATUS.md`            | 迁移 validation/conflict 的前置约定、修复状态与剩余风险                                                                                        |
| Round 2.5 repair alignment              | `.trellis/tasks/06-19-round2-repair-alignment/MASTER.plan.md`                                                                                                                                                        | 作为进入 Round 3 前 gate 的 trace 来源                                                                                                         |
| Round 2.6 contract gate：`016A`-`016F`  | `.trellis/tasks/archive/2026-06/06-19-round2-6-contract-gate/MASTER.plan.md`；同目录 `audit.report.md`、`REPAIR.plan.md`                                                                                             | 迁移 contract gate 与文档/契约对齐结论                                                                                                         |
| Round 2.6 routing service gate          | `.trellis/tasks/archive/2026-06/06-19-round2-6-routing-service-gate/MASTER.plan.md`；同目录 `audit.report.md`；`research/phase-a-self-check-migrated.md`                                                             | 迁移 routing service gate 证据与 Phase A 自检                                                                                                  |
| Round 3：`017`-`023` + Batch 2.5 `018A` | 当前执行前必须追溯 Round 2.5、Round 2.6 contract gate、Round 2.6 routing service gate；另读 `docs/ROUND3_HANDOFF.md`、`docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md` 与 `ROUND3_BATCH_IMPLEMENTATION_MAP.md` | 新建 MASTER 时必须把 gate 状态写入 §0/§1/Source Context Index；Batch 2.5 必须按 `018A_layer1_observation_ingestion_bridge.md` 五阶段 Gate 计划 |
| Round 4：`024`-`030`                    | 当前仓库未发现 Round 4 专属 `.trellis/tasks/**/MASTER.plan.md`                                                                                                                                                       | 新建 Plan 时从原始任务、项目地图、对应模块设计文档、contracts、issue registries 生成 MASTER/AUDIT/jsonl                                        |
| Round 5：`031`-`036`                    | 当前仓库未发现 Round 5 专属 `.trellis/tasks/**/MASTER.plan.md`                                                                                                                                                       | 新建 Plan 时从 release/quality 规则、manifest 保护条款、contracts 生成 MASTER/AUDIT/jsonl                                                      |

## 5. Plan 归并规则

Plan agent 必须把每个原始输入文件归类为以下之一，并写入 `MASTER.plan.md` 的 Source Context Index：

| 分类         | 处理方式                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| 可总结       | 把约束、验收点、边界写入 MASTER / AUDIT.plan；jsonl 不必列原文                                           |
| 不可无损总结 | 在 MASTER Source Context Index 中列出原文路径、必须读取章节、使用原因；需要执行/审计读取时进入对应 jsonl |
| 已过时/无效  | 写入 filtered-out / obsolete context list，说明原因；禁止进入 Execute/Audit manifest                     |
| 原始任务卡   | 只作为 Plan 来源；原则上不进入 implement.jsonl/audit.jsonl，除非 MASTER 明确要求追溯原始卡原文           |

## 6. 关键主题追溯入口

| 主题                                 | Plan 必须核对的原文入口                                                                                                                                                                                                                                                         |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 数据源角色模型                       | `README.md`、`docs/adr/ADR-0005-primary-validation-fallback-source-model.md`、`specs/datasource_registry/source_registry.yaml`                                                                                                                                                  |
| docs/specs 非实现地址边界            | `README.md`、`MIGRATION_MAP.md`、`docs/architecture/07_project_directory_structure.md`                                                                                                                                                                                          |
| schema / migration 覆盖              | `specs/schema/schema.sql`、`docs/schema/MIGRATION_COVERAGE.md`、`docs/schema/MIGRATION_008_PLAN.md`、`docs/ops/migration_recovery_policy.md`                                                                                                                                    |
| QMD Ops DB Inspect CLI               | `docs/ops/db_inspect_cli.md`、`specs/contracts/ops_db_inspect_contract.yaml`、`ROUND3_BATCH_IMPLEMENTATION_MAP.md`、`docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`、`docs/ROUND3_HANDOFF.md`                                                                            |
| Source Capability / Route / Service  | `docs/modules/source_capability_registry.md`、`docs/modules/source_route_plan.md`、`docs/modules/datasource_service.md`、对应 `specs/contracts/source_*` 与 `datasource_service_contract.yaml`                                                                                  |
| Layer 1 observation ingestion bridge | `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018A_layer1_observation_ingestion_bridge.md`、`docs/modules/layer1_global_regime_panel.md`、`docs/architecture/03_runtime_flows.md`、`specs/contracts/snapshot_lineage_contract.yaml`、`specs/contracts/write_contract.yaml` |
| 模块边界                             | `docs/architecture/module_boundary_matrix.md`、`specs/contracts/module_boundary_contract.yaml`、`scripts/check_module_boundaries.py`                                                                                                                                            |
| API / frontend security              | `specs/contracts/api_security_contract.yaml`、`docs/ops/frontend_security_policy.md`、`docs/modules/fastapi_backend.md`、`docs/modules/frontend_dashboard.md`                                                                                                                   |
| Agent 安全与固定来源                 | `docs/modules/agent_module.md`、`docs/api/agent_tool_contracts.md`、`docs/ops/agent_security_policy.md`、`docs/ops/agent_workflow_boundaries.md`                                                                                                                                |
| 回测与复盘                           | `docs/modules/backtest_and_review.md`、`docs/modules/backtest_review_lifecycle.md`、`specs/contracts/backtest_contract.yaml`、`specs/contracts/backtest_metric_contract.yaml`、`specs/contracts/backtest_reproducibility_contract.yaml`                                         |
| 发布清理与 manifest                  | `README.md`、`docs/quality/final_package_rules.md`、`specs/contracts/release_cleanup_allowlist.yaml`、`docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md`                                                                              |
