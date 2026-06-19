# Implement — Round2.6 Routing Service Gate

见 `MASTER.plan.md` §8。

1. 实现 CapabilityRegistry 与 adapter domain reconciliation。
2. 实现 SourceRoutePlan / SourceRoutePlanner。
3. 实现 DataSourceService，并把 sync runner path 接入 service/fetch callable。
4. 扩展 vendor fixture E2E 与 production-equivalent smoke。
5. 更新 deferred registry、Round3 gate，并清理或迁移 root self-check。
