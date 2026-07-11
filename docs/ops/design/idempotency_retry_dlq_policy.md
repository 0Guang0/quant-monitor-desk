# Idempotency, Retry, Backoff, Dead Letter, and Partial Success Policy

## 1. 目的

修复 QM-AUD-011：DataSyncOrchestrator 必须有幂等键、重试退避、死信队列和部分成功补偿。

## 2. 幂等键

每个数据同步任务必须生成：

```text
idempotency_key = hash(job_type + source_id + data_domain + market_id + instrument_id + window_start + window_end + as_of_policy + schema_version)
```

同一幂等键重复执行时：

- 如果已成功，直接返回既有结果。
- 如果失败且可重试，进入 retry。
- 如果处于 running 超时，进入 manual review。

## 3. 重试与退避

| 错误              | 默认行为                      |
| ----------------- | ----------------------------- |
| NETWORK_ERROR     | 指数退避重试，最多 3 次       |
| RATE_LIMITED      | 等待源级 cooldown，不立即重试 |
| AUTH_FAILED       | 不重试，进入 manual review    |
| SCHEMA_DRIFT      | 不重试，进入 schema review    |
| EMPTY_RESPONSE    | 根据发布日历判断是否可接受    |
| NOT_PUBLISHED_YET | 等待下一发布窗口              |

## 4. Dead Letter / Manual Review

不可自动恢复的任务写入 `manual_review_queue`，必须包含：

- idempotency_key
- source_id
- data_domain
- error_type
- last_error_message
- last_attempt_at
- recommended_next_action

## 5. 部分成功补偿

批量任务必须记录 item-level 状态，不允许用一个总状态覆盖全部。部分成功时：

- 成功 item 可提交。
- 失败 item 进入 retry 或 manual review。
- snapshot 构建只能读取通过 quality gate 的 clean 数据。

## ADR-017 关联与部分成功规则

幂等键和 manual review 记录还必须关联 `route_plan_id`、`source_registry_revision` 与
`activation_overlay_revision`，以便区分同一窗口在不同路由决策下的运行。可信快照默认只读可信
最终库；连续监控快照可读取质量异常数据，但必须保留来源／质量／人工复核标签，不能被当作可信
快照缓存或覆盖。
