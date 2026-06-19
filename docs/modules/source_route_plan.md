# SourceRoutePlan（Round2.6）

## 1. 目的

`SourceRoutePlan` 是运行时的显式源路由计划，用于解释“为什么选中某个源、为什么跳过某个源、为什么 fallback、为什么无法调度”。它吸收 EasyXT 候选源链思路，但保持本项目禁止 silent fallback 的强审计边界。

## 2. 权威契约

- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/platform_source_matrix.yaml`
- `specs/datasource_registry/source_capabilities.yaml`

## 3. RoutePlan 必须记录

```text
route_plan_id
run_id
job_id
data_domain
operation
route_status
selected_source_id
candidates[]
quality_flags
created_at
```

每个 candidate 必须记录：

```text
source_id
role
enabled
allowed_domain
capability_declared
disabled_reason
skip_reason
```

## 4. 关键状态

| route_status | 含义 |
|---|---|
| READY | 可安全进入 fetch |
| DISABLED_SOURCE | 目标源或 domain 默认禁用 |
| NO_AVAILABLE_SOURCE | 没有合格候选源 |
| CAPABILITY_MISSING | capability 未声明 |
| USER_AUTH_REQUIRED | 需要用户授权 |
| RESOURCE_GUARD_PAUSED | 资源保护暂停 |

## 5. 持久化边界

实现阶段必须二选一并记录 ADR：

1. 新增 `source_route_log` 表；或
2. 写入 `job_event_log.payload_json`。

未确定前，设计上要求所有 fetch 前必须生成 RoutePlan，但不强制当前 Round2 代码立即落库。

## 6. 验收

```bash
python -m pytest tests/test_source_route_planner.py tests/test_source_registry.py tests/test_sync_orchestrator.py -q
```
