# 事故处理手册

## INC-001 DISABLED_SOURCE

- **症状**：job 未 fetch，route_status=`DISABLED_SOURCE`。
- **原因**：源或 domain 被禁用，例如 QMT/Yahoo/qmt_xqshare。
- **安全动作**：检查 SourceRoutePlan、source_registry、platform matrix。
- **危险动作**：自动启用源、silent fallback。

## INC-002 RESOURCE_GUARD_PAUSED

- **症状**：任务进入 `FAILED_RETRYABLE` 或 route_status=`RESOURCE_GUARD_PAUSED`。
- **安全动作**：缩小数据范围、分片 backfill、释放资源。
- **危险动作**：关闭 ResourceGuard 或无边界扩大权限。

## INC-003 SCHEMA_DRIFT

- **症状**：schema_hash 变化，validation failed。
- **安全动作**：保留 raw/fetch_log，暂停 clean write，更新 capability/adapter/test。
- **危险动作**：忽略 drift 写 clean。

## INC-004 USER_AUTH_REQUIRED

- **症状**：QMT/qmt_xqshare 不可调度。
- **安全动作**：用户确认本机/远程授权，配置 env，重新 route-preview。
- **危险动作**：自动登录、验证码识别、远程探测。

## INC-005 PRODUCTION_EQUIVALENT_SMOKE

- **症状**：生产等价 smoke 失败。
- **安全动作**：确认临时 DB、fixture-scale 数据、cleanup、ResourceGuard。
- **危险动作**：连接真实生产写路径或污染真实数据。

## INC-006 DEGRADED_CONTINUITY

- **症状**：Primary 失败、RoutePlan 选择 `DEGRADED`，连续监控仍可读。
- **安全动作**：检查失败来源、异常类型、影响领域、开始时间、RoutePlan 与风险标签；保持连续监控并跟踪主源恢复。
- **危险动作**：将次源升格为 Primary、删除失败记录或隐藏标签。

## INC-007 QUALITY_FAILED_CONTINUITY

- **症状**：质量异常但可归一化数据进入连续监控区，`manual_review_required=true`。
- **安全动作**：人工核对、保留证据；可信最终库保持不写入。
- **危险动作**：把该值补写入可信最终库或当作正常业务结论发送。

## INC-008 PRIMARY_IMPLEMENTATION_DEFECT

- **症状**：Primary 因代码、适配器、格式或 schema 失败。
- **安全动作**：记录失败来源、类型、领域和开始时间，建立高优先级修复事件；合格次源可按 RoutePlan 维持连续监控。
- **危险动作**：因次源可用而关闭／忽略修复事件。
