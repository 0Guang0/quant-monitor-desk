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

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_sources.md`（含 §5.2.1 overlay）、`docs/modules/design/source_capability_registry.md`、`docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md`、`docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`、`specs/layer1_axes/design/restructured_axes_v1_1/common/common_axis_rules.md`、`specs/contracts/design/layer1_axis_contract.yaml`、`docs/architecture/design/08_decision_log_index.md`、`docs/architecture/design/module_boundary_matrix.md`、`docs/modules/design/qmt_xtdata_adapter.md`、`docs/ops/design/qmt_xqshare_setup.md`、`docs/architecture/design/06_deployment_and_local_ops.md`、`docs/ops/design/ERROR_CODE_GUIDE.md`、`docs/ops/design/incident_playbook.md`。

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

| 文件 | 用途 |
|------|------|
| **[HANDOFF.md](HANDOFF.md)** | **会话交接**（下一 agent 先读加载顺序） |
| **[EXECUTION-DOC-INDEX.md](EXECUTION-DOC-INDEX.md)** | **执行文档权威层级 / 依赖确认** |
| `task_plan.md` | R4 工作包与关账 AC（L2） |
| `gate1-integration-spec.md` | Gate 1 跨模块切片与阻塞边（L1） |
| `g1-02-execution-brief.md` | G1-02 防漂移执行 brief（L3 · 开工必读） |
| `g1-01-wiring-inventory.md` | G1-01 正式入口清单（Plan r6 READY · L4） |
| `decision-map-enable-seam.md` | 启用接缝 #1–#4 决议 → ADR-018 |
| `findings.md` | **只记本票**问题 |
| `progress.md` | 会话进度 |
| `completion-check-plan-g1-01-r6.md` | G1-01 清单 Plan 关账 |
| `completion-check-plan-execution-set.md` | **最终执行计划集合** Plan 关账（归档后） |
| `completion-check-audit.md` | 模块 R4 Audit（仍 OPEN） |
| [`归档/`](归档/README.md) | 已退役临时产物（只读，不指挥实现） |

权威 design 另含 **ADR-017 / ADR-018**（见 `MIGRATION_MAP.md`）。本地票：`.scratch/task-01-g1-02-enable-seam/`（不发 GitHub）。
