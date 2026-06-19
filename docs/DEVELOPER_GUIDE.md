# Developer Guide

## 1. 任务入口

- 全局执行规则：`docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- 测试策略：`docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- Round2.6：`docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/`

## 2. 当前禁止

1. Round2.6 Phase A 不改代码。
2. 不改依赖锁文件。
3. 不绕过 QMT/Yahoo/qmt_xqshare disabled gate。
4. 不把参考项目交易能力搬进来。
5. 不让 Agent 或 API 直接构造 vendor adapter。

## 3. 设计优先级

优先对齐：SourceCapabilityRegistry、DataSourceService、SourceRoutePlan、ModuleBoundaryMatrix、Privacy Data Flow、Backtest Review Lifecycle、Reference Adoption Guardrails。

## 4. 验证

Round2.6 Phase A 自检已迁移至 Trellis：`.trellis/tasks/06-19-round2-6-routing-service-gate/research/phase-a-self-check-migrated.md`。生产等价 smoke：`python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r26-smoke`。
