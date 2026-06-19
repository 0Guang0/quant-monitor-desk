# Design — Round2.6 Routing Service Gate

见 `MASTER.plan.md` §4–6。

- 核心：SourceRegistry 保持 source/domain/role 权威；CapabilityRegistry 负责 operation/field；SourceRoutePlanner 负责候选源解释；DataSourceService 是生产 fetch facade。
- RoutePlan 持久化优先使用现有 `job_event_log.payload_json`，避免 Round3 前新增 migration；若 Execute 发现不可行，必须写 ADR 并请求用户确认。
- 验收重点：service-path E2E、production-equivalent smoke、ResourceGuard、no silent fallback、no pollution。
