# task-02-source-route-plan

> 流水线 **02**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**源路由计划模块（SourceRoutePlanner / SourceRoutePlan）**

## 负责什么（业务视角）

在真正抓数之前，算出「用哪个源、降级还是阻断、原因是什么」。产出可审计的 RoutePlan（READY / BLOCKED / DEGRADED 等），禁止 silent fallback。

## 上下游

| 方向     | 谁                                                                          |
| -------- | --------------------------------------------------------------------------- |
| **上游** | **task-01-source-registry**（源与能力登记）                                 |
| **下游** | **task-03-resource-guard** · **task-04-datasource-fetch**（按计划执行抓取） |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`、`specs/contracts/design/source_provenance_quality_contract.yaml`、`docs/modules/design/source_route_plan.md`、`docs/modules/design/data_sources.md`、`docs/modules/design/source_capability_registry.md`、`specs/layer1_axes/design/restructured_axes_v1_1/common/common_axis_rules.md`、`docs/modules/design/data_validation_and_conflict.md`、`docs/architecture/design/04_data_architecture.md`、`docs/modules/design/write_manager.md`、`docs/modules/design/qmt_xtdata_adapter.md`、`docs/ops/design/qmt_xqshare_setup.md`、`docs/architecture/design/06_deployment_and_local_ops.md`、`docs/architecture/design/03_runtime_flows.md`、`docs/ops/design/ERROR_CODE_GUIDE.md`、`docs/ops/design/incident_playbook.md`、`specs/contracts/design/source_conflict_rules.yaml`。

> 倒查说明（`MIGRATION_MAP.md` 数据源域 文件3 → 全文）：本票管 **RoutePlan 生成、持久化、固定候选顺序、route_status/route_grade、FallbackPolicy 决策记录、来源/质量/恢复证据**；registry 只读（→ task-01）。`04_data_architecture.md` / `write_manager.md` / `data_validation_and_conflict.md` 约束 **可信最终库／连续监控区／审计归档区** 与下游消费边界。

## 运行时文件

> 非 design 路径：本模块**加载、产出或验收**所用；设计口径以上节权威文件为准。

| 文件                                                 | 作用                                                                              |
| ---------------------------------------------------- | --------------------------------------------------------------------------------- |
| `specs/contracts/source_route_contract.yaml`         | **验收契约**：RoutePlan 字段、`route_status`/`route_grade` 机器 SSOT，pytest 对照 |
| `specs/contracts/platform_source_matrix.yaml`        | **配置依赖**：只读 task-01 产出，选路输入                                         |
| `specs/datasource_registry/source_capabilities.yaml` | **配置依赖**：只读 task-01 产出，能力匹配输入                                     |
| `specs/schema/schema.sql`                            | **表结构依赖**：RoutePlan 持久化相关表建表定义                                    |

## 代码主区（实现时收窄）

```text
backend/app/datasources/（SourceRoutePlanner · route 相关）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
