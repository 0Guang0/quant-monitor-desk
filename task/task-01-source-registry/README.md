# task-01-source-registry

> 流水线 **01**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据源注册模块（Source Registry / Capability）**

## 负责什么（业务视角）

维护「有哪些数据源、能干什么、默认开不开」的登记册。包括 `source_registry`、capability 绑定、platform matrix 与按源 enable/disable 策略，是所有后续选路与抓取的配置地基。

## 上下游

| 方向     | 谁                                                                           |
| -------- | ---------------------------------------------------------------------------- |
| **上游** | 无（流水线起点）· 输入来自 `specs/` 下 registry/YAML 与 `MIGRATION_MAP` 设计 |
| **下游** | **task-02-source-route-plan**（路由规划读取 registry/capability）            |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_sources.md`、`docs/modules/design/source_capability_registry.md`、`specs/layer1_axes/design/restructured_axes_v1_1/common/common_axis_rules.md`、`specs/contracts/design/layer1_axis_contract.yaml`、`docs/architecture/design/08_decision_log_index.md`（ADR-0005）、`docs/architecture/design/module_boundary_matrix.md`、`docs/modules/design/qmt_xtdata_adapter.md`、`docs/ops/design/qmt_xqshare_setup.md`、`docs/architecture/design/06_deployment_and_local_ops.md`、`docs/ops/design/ERROR_CODE_GUIDE.md`、`docs/ops/design/incident_playbook.md`。

> 倒查说明（`MIGRATION_MAP.md` → 上文 design 全文）：本票管 **registry/capability/启用策略/三角色口径**，不管 RoutePlan 运行时选路（→ task-02）。`data_sources.md` §5.2/§5.3/§5.9 与 `common_axis_rules.md` §4 约束 Primary/Validation/FallbackPolicy 及 `SHADOW` 不得进入 registry role。

## 运行时文件

> 非 design 路径：本模块**加载、维护或验收**所用；设计口径以上节权威文件为准。

| 文件                                                 | 作用                                                                     |
| ---------------------------------------------------- | ------------------------------------------------------------------------ |
| `specs/datasource_registry/source_registry.yaml`     | **配置产出/依赖**：源登记机器可读 SSOT，本模块维护，下游 task-02/04 只读 |
| `specs/datasource_registry/source_capabilities.yaml` | **配置产出/依赖**：能力绑定机器可读 SSOT，本模块维护，下游只读           |
| `specs/contracts/source_capability_contract.yaml`    | **验收契约**：capability 字段与结构约束，pytest/契约测试对照             |
| `specs/contracts/platform_source_matrix.yaml`        | **配置产出/依赖**：平台×数据源矩阵，路由与启用策略输入                   |
| `specs/contracts/module_boundary_contract.yaml`      | **边界约束**：模块 import/写库边界，实现不得越界                         |
| `specs/schema/schema.sql`                            | **表结构依赖**：`source_registry` 等 DuckDB 建表定义，迁移与落库对照     |

## 代码主区（实现时收窄）

```text
backend/app/datasources/（registry · capability 相关）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
