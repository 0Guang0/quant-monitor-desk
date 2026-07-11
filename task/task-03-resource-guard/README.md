# task-03-resource-guard

> 流水线 **03**/19 · 详见 [`../TASK_PIPELINE_INDEX.md`](../TASK_PIPELINE_INDEX.md)

## 完成哪个模块

**本机资源守卫（ResourceGuard）**

## 负责什么（业务视角）

在重任务（抓取、写入、大查询）前检查 CPU/内存/磁盘，eco/normal/batch 三档限制；资源不足时 PAUSE/STOP 并诚实报错，防止本机被拖死。

## 上下游

| 方向     | 谁                                                                         |
| -------- | -------------------------------------------------------------------------- |
| **上游** | **task-02-source-route-plan**（已知将要执行的任务范围）                    |
| **下游** | **task-04-datasource-fetch** 及后续所有重操作（fetch · write · scheduler） |

## 权威文件

权威文件必须在 `**/design/**` 下，详见：`docs/ops/design/performance_limits.md`、`specs/contracts/design/resource_limits.yaml`、`rules/design/GLOBAL_RESOURCE_LIMITS.md`、`docs/architecture/design/03_runtime_flows.md`、`specs/contracts/design/runtime_flow_contract.yaml`、`docs/modules/design/source_route_plan.md`、`docs/modules/design/data_sync_orchestrator.md`、`docs/architecture/design/04_data_architecture.md`、`docs/ops/design/logs_health_audit.md`、`specs/contracts/design/log_audit_contract.yaml`、`docs/ops/design/ERROR_CODE_GUIDE.md`、`docs/ops/design/incident_playbook.md`、`docs/architecture/design/06_deployment_and_local_ops.md`、`specs/contracts/design/ops_health_check_contract.yaml`、`docs/ops/design/daily_weekly_monthly_checklist.md`。

> 倒查说明（`MIGRATION_MAP.md` 运维域 文件3/13/15 → 全文）：本票管 **eco/normal/batch 三档、PAUSE/HARD_STOP、`resource_guard_log`**。`runtime_flow_contract.yaml` 规定检查点（job 前、batch 前、clean merge 前等）；`source_route_plan.md` 定义 `route_status=RESOURCE_GUARD_PAUSED`。

## 运行时文件

> 非 design 路径：本模块**读取或对齐**所用；设计口径以上节权威文件为准。

| 文件                                         | 作用                                                                 |
| -------------------------------------------- | -------------------------------------------------------------------- |
| `specs/contracts/api_security_contract.yaml` | **边界约束**：API 查询预算上限，须与 `performance_limits.md` §7 一致 |

## 代码主区（实现时收窄）

```text
backend/app/ops/（ResourceGuard 实现）
```

## 本票文档

| 文件           | 用途                 |
| -------------- | -------------------- |
| `task_plan.md` | R4 验收标准与关账 AC |
| `findings.md`  | **只记本票**问题     |
| `progress.md`  | 关账勾选             |
