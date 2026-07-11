# task-04-datasource-fetch

> 流水线 **04**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**数据源抓取模块（DataSourceService / Adapter / Fetch Port）**

## 负责什么（业务视角）

按 RoutePlan 正式抓取外部数据：走 `DataSourceService.fetch`，经 adapter/fetch_port 拉取原始 payload，写 fetch 证据；生产路径禁止 runner 直传 adapter 绕过 Service。

## 上下游

| 方向     | 谁                                                                       |
| -------- | ------------------------------------------------------------------------ |
| **上游** | **task-01** registry · **task-02** RoutePlan · **task-03** ResourceGuard |
| **下游** | **task-05-raw-store**（原始数据与 fetch_log 落地）                       |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/modules/design/data_sources.md`、`docs/modules/design/source_route_plan.md`、`docs/modules/design/source_capability_registry.md`、`docs/modules/design/qmt_xtdata_adapter.md`、`docs/ops/design/qmt_xqshare_setup.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/architecture/design/module_boundary_matrix.md`、`docs/architecture/design/03_runtime_flows.md`、`docs/architecture/design/04_data_architecture.md`、`docs/architecture/design/06_deployment_and_local_ops.md`、`docs/ops/design/ERROR_CODE_GUIDE.md`、`docs/ops/design/incident_playbook.md`、`docs/ops/design/idempotency_retry_dlq_policy.md`。

> 倒查说明（`MIGRATION_MAP.md` 数据源域 文件1/3/4/5 + 数据同步域 文件4 §13.12 → 全文）：本票管 **DataSourceService.fetch、Adapter/Fetch Port、FetchRequest/FetchResult、fetch 失败诚实落日志**；必须先有 RoutePlan（→ task-02）与 ResourceGuard（→ task-03）。`module_boundary_matrix.md` 禁止 datasources 写 clean、禁止 API 直 import adapter；`data_sync_orchestrator.md` §13.12 规定 runner **不得**直传 adapter 绕过 Service。

## 运行时文件

> 非 design 路径：本模块**读取、产出或验收**所用；设计口径以上节权威文件为准。

| 文件                                                 | 作用                                                                  |
| ---------------------------------------------------- | --------------------------------------------------------------------- |
| `specs/contracts/datasource_service_contract.yaml`   | **验收契约**：`FetchRequest`/`FetchResult` 接口机器 SSOT，pytest 对照 |
| `specs/contracts/source_route_contract.yaml`         | **配置依赖**：只读 task-02 产出的 RoutePlan 结构与状态枚举            |
| `specs/contracts/platform_source_matrix.yaml`        | **配置依赖**：只读 task-01，adapter 选型输入                          |
| `specs/datasource_registry/source_registry.yaml`     | **配置依赖**：只读 task-01，源元数据输入                              |
| `specs/datasource_registry/source_capabilities.yaml` | **配置依赖**：只读 task-01，能力匹配输入                              |
| `specs/contracts/module_boundary_contract.yaml`      | **边界约束**：禁止 runner 直传 adapter、禁止本模块写 clean            |

## 代码主区（实现时收窄）

```text
backend/app/datasources/service.py · adapters · fetch_ports
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
