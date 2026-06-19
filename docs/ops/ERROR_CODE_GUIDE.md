# Error Code Guide（Round2.6）

| Error code | 含义 | 安全重试 | 用户动作 | 不允许 |
|---|---|---|---|---|
| `DISABLED_SOURCE` | 源或 domain 默认禁用 | 否，除非用户启用 | 查看 SourceRoutePlan 的 disabled_reason | 自动启用 QMT/Yahoo/xqshare |
| `NO_AVAILABLE_SOURCE` | 无可用候选源 | 否 | 检查 source_registry 与 capability | silent fallback |
| `CAPABILITY_MISSING` | operation/field 未声明 | 否 | 补 `source_capabilities.yaml` | 直接调用 adapter |
| `USER_AUTH_REQUIRED` | 需要本机或远程授权 | 否 | 用户确认授权并配置 env | 自动登录/探测终端 |
| `RESOURCE_GUARD_PAUSED` | 资源保护暂停 | 等待或减小范围 | 降低 date range/universe/resource mode | 绕过 ResourceGuard |
| `NOT_PUBLISHED_YET` | 数据尚未发布 | 是，下次调度 | 检查 expected_lag | 写空 clean 表 |
| `SCHEMA_DRIFT` | 字段或 schema hash 变化 | 否 | 进入人工/adapter 更新 | 写 clean 表 |
| `AUTH_FAILED` | 授权失败 | 否 | 检查凭证/终端授权 | 重复暴力重试 |
| `RATE_LIMITED` | 被限流 | 延迟后可重试 | 按 source policy 暂停 | 切源伪装成功 |
| `QUERY_TOO_LARGE` | 查询/扫描过大 | 缩小范围 | 使用 shard/backfill | 关闭资源限制 |
| `DUCKDB_LOCKED` | DB 被占用 | 是 | 等待 writer 释放 | 多 writer 强写 |

## 要求

每个 CLI/API/job 失败输出必须至少包含：

```text
error_code
message
docs_anchor
retryable
manual_confirmation_required
```
