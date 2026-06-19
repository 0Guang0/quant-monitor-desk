# Plan Boot — 06-19-round2-6-routing-service-gate

## 用户目标摘要

第二个 Trellis 复杂任务：在 Contract Gate 通过后，实现 Round2.6 进入 Round3 前真正需要的最小运行闭环，包括 CapabilityRegistry、SourceRoutePlanner、DataSourceService、sync service path、生产等价 smoke、deferred registry 最终对齐和 self-check 清理。

## 原计划已读

- `docs/implementation_tasks/README.md`
- `GLOBAL_EXECUTION_RULES.md`
- `GLOBAL_TESTING_POLICY.md`
- `GLOBAL_RESOURCE_LIMITS.md`
- `ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/README.md`
- `016A`, `016B`, `016C`, `016D`, `016E`, `016F`

## 前置依赖

- `06-19-round2-6-contract-gate` 必须 PASS，或用户明确 override。
- Parent task tests are input, not substitute for this task RED/GREEN.

## Phase P0 complete
