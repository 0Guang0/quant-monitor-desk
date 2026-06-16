# ADR-0005: primary-validation-fallback-source-model

- 状态：accepted
- 来源：从 v1.6 设计文档已确认结论拆分生成

## 背景

每个指标强制维护 Primary/Shadow/Emergency 三个外部源会增加运维成本，也可能引入 silent switch 风险。

## 决策

数据源角色统一为 Primary / Validation / FallbackPolicy；FallbackPolicy 不是第三外部源，而是 retry、last_good、NaN + stale_reason、manual_review 等策略。

## 影响

降低运维成本，同时保留可审计、可回退、可人工确认的治理边界。

## 详细参考

`docs/modules/data_sources.md`、`specs/layer1_axes/restructured_axes_v1_1/`
