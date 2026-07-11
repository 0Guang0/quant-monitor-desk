# SourceRoutePlan

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
source_grade
quality_grade
manual_review_required
primary_failure_reason
source_registry_revision
activation_overlay_revision
recovery_replacement_of_route_plan_id
created_at
```

每个 candidate 必须记录：

```text
source_id
role
priority
enabled
activation_effective_enabled
allowed_domain
capability_declared
authorized
disabled_reason
skip_reason
```

## 4. 关键状态

| route_status          | 含义                                                   |
| --------------------- | ------------------------------------------------------ |
| READY                 | 可安全进入 fetch                                       |
| READY_PRIMARY         | 选中 Primary；质量通过时才可写可信最终库               |
| READY_DEGRADED        | 选中 FallbackPolicy 授权路径；只可写带标签的连续监控区 |
| BLOCKED_MANUAL_REVIEW | 源冲突、schema drift 或策略要求人工确认                |
| DISABLED_SOURCE       | 目标源或 domain 默认禁用                               |
| NO_AVAILABLE_SOURCE   | 没有合格候选源                                         |
| CAPABILITY_MISSING    | capability 未声明                                      |
| USER_AUTH_REQUIRED    | 需要用户授权                                           |
| RESOURCE_GUARD_PAUSED | 资源保护暂停                                           |

`READY` 是兼容旧实现的粗粒度状态；最终成品应在 route payload 中同时提供 `route_grade=primary|degraded|blocked`，避免下游把降级路径误读成正常主源路径。

## 4.1 FallbackPolicy 决策记录

当 Primary 不可用时，RoutePlan 必须先记录主源失败原因，再决定 fallback 行为。失败原因包括但不限于：

```text
auth_failed
rate_limited
schema_drift
empty_response
not_published_yet
network_failure
resource_guard_paused
source_disabled
capability_missing
```

允许的 fallback 行为必须来自 domain 级 `FallbackPolicy`：

```text
retry_same_source
use_validation_source_with_flag
use_last_good_cache
mark_missing
manual_review_required
skip_until_next_publish
```

若策略为 `use_validation_source_with_flag`，RoutePlan 必须输出：

```text
selected_source_id = 实际 Validation 源
selected_role = FallbackPolicy
route_grade = degraded
quality_flags 包含 SOURCE_FALLBACK_USED 与 VALIDATION_SOURCE_USED
primary_source_failed = true
primary_failure_reason = 上述失败原因之一
```

禁止把 `selected_role=Validation` 或 `source_id` 直接伪装成 Primary。没有 FallbackPolicy 授权时，Validation 源只能进入 validation/source_conflict/manual_review/evidence。

## 5. 新增外部数据源路由规则

新增的 `us_treasury`、`sec_edgar`、`cftc_cot`、`bis`、`world_bank`、`deribit`、`coingecko`、`kalshi`、`polymarket`、`stooq`、`alpha_vantage`、`mootdx`、`eastmoney`、`sina_finance`、`ths_ifind` 与 `web_search` 必须先进入 `DISABLED_SOURCE` 路由，直到对应 adapter、授权/条款、capability、ResourceGuard、回放样本和验收测试完成。

SourceRoutePlan 可以把这些源暴露为候选/诊断项，但不得把 proposed-disabled source 选为 `READY`，也不得构造 adapter。`source_type` 与 `license_type` 必须保持与 `specs/schema/schema.sql` / migration 009 CHECK 枚举一致，否则 route plan 必须失败为 contract/config error。

路由优先级原则：官方/监管/披露源优先于聚合源；交易所级 market-data 优先于聚合价格；授权终端优先于网页源；预测市场只能输出 `probability_signal`；Web Search 只能输出 evidence/manual_review，不得进入任何数值写入目标。聚合源或 validation-only 源只有在 domain FallbackPolicy 明确为 `use_validation_source_with_flag` 时，才允许以 `DEGRADED` 身份进入带标签的连续监控链路，绝不写可信最终库。

## 6. 持久化边界

RoutePlan 是正式业务链路的一部分，必须持久化。存储方式必须由 ADR 固定，并满足可审计、可查询、可重放要求。允许的实现形态为：

1. 新增 `source_route_log` 表；或
2. 写入 `job_event_log.payload_json`。

禁止只在内存中生成 RoutePlan 后丢弃。任何进入 fetch、validation、clean 或验收报告的业务链路，都必须能从持久化记录追溯到对应 RoutePlan。

生产等价验收与正式运行必须能在验收报告中回答：

```text
为什么没有用 Primary？
用了哪个 fallback 策略？
实际 source_used 是谁？
这条数据属于可信最终库还是连续监控区，来源等级和质量等级分别是什么？
下游是否允许按标签消费连续监控数据？
```

## 7. 验收

```bash
python -m pytest tests/test_source_route_planner.py tests/test_source_registry.py tests/test_sync_orchestrator.py -q
```

## ADR-017 补充：连续监控与恢复 RoutePlan

每个 RoutePlan 除既有候选和原因码外，必须持久化领域固定候选顺序、有效启用覆盖层版本、
`source_grade`、`quality_grade`、`manual_review_required` 与主源失败事件引用。所有 Primary
失败可触发受批准候选的顺序尝试；代码、适配器、格式、schema 失败同时生成高优先级修复事件。
无候选或不可归一化结果必须为 `MISSING`。主源恢复 RoutePlan 必须记录按领域频率计算的回补区间
及前后缓冲窗口，并只在验证的主源版本与异常版归档均成功后切换同一事实位置的默认读取。
