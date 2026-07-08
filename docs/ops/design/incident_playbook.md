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
