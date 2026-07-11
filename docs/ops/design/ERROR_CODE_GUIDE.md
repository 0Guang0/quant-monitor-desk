# 错误码指南

| Error code              | 含义                                  | 安全重试         | 用户动作                                                  | 不允许                      |
| ----------------------- | ------------------------------------- | ---------------- | --------------------------------------------------------- | --------------------------- |
| `DISABLED_SOURCE`       | 源或 domain 默认禁用                  | 否，除非用户启用 | 查看 SourceRoutePlan 的 disabled_reason                   | 自动启用 QMT/Yahoo/xqshare  |
| `READY_DEGRADED`        | 主源失败但已按 RoutePlan 选中合格次源 | 依策略           | 查看来源/质量标签、主源失败原因与修复事件                 | 伪装为 Primary 或无标签成功 |
| `NO_AVAILABLE_SOURCE`   | 固定候选链无合格候选或全部失败        | 否               | 检查 source_registry、覆盖层与 capability                 | 未记录 fallback             |
| `CAPABILITY_MISSING`    | operation/field 未声明                | 否               | 补 `source_capabilities.yaml`                             | 直接调用 adapter            |
| `USER_AUTH_REQUIRED`    | 需要本机或远程授权                    | 否               | 用户确认授权并配置 env                                    | 自动登录/探测终端           |
| `RESOURCE_GUARD_PAUSED` | 资源保护暂停                          | 等待或减小范围   | 降低 date range/universe/resource mode                    | 绕过 ResourceGuard          |
| `NOT_PUBLISHED_YET`     | 数据尚未发布                          | 是，下次调度     | 检查 expected_lag                                         | 写空 clean 表               |
| `SCHEMA_DRIFT`          | 字段或 schema hash 变化               | 否               | 创建高优先级修复事件；合格次源可按 RoutePlan 维持连续监控 | 写可信最终库或忽略修复事件  |
| `AUTH_FAILED`           | 授权失败                              | 否               | 检查凭证/终端授权                                         | 重复暴力重试                |
| `RATE_LIMITED`          | 被限流                                | 延迟后可重试     | 按 source policy 暂停                                     | 切源伪装成功                |
| `QUERY_TOO_LARGE`       | 查询/扫描过大                         | 缩小范围         | 使用 shard/backfill                                       | 关闭资源限制                |
| `DUCKDB_LOCKED`         | DB 被占用                             | 是               | 等待 writer 释放                                          | 多 writer 强写              |

## 要求

每个 CLI/API/job 失败输出必须至少包含：

```text
error_code
message
docs_anchor
retryable
manual_confirmation_required
```

## ADR-017：已记录的兜底不是 silent fallback

`NO_AVAILABLE_SOURCE` 仅在固定候选链全部不合格或全部失败后返回。Primary 失败但 fallback 成功时
必须返回／记录 `READY_DEGRADED`、实际来源、主源失败原因、RoutePlan 与风险标签，而非把失败藏成
普通成功。`SCHEMA_DRIFT`、代码、适配器或格式失败在允许兜底的同时必须产生高优先级修复事件；
未登记、禁用、未审核或能力不匹配来源仍禁止尝试。
