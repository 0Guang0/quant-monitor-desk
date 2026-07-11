# ADR 决策记录索引

本目录用于保存“为什么这样设计”的长期决策。当前拆分步骤不扩展新细节，只从 v1.6 已确认结论中提取决策骨架。

| ADR      | 决策                                             | 状态     | 对应模块                                                                                  |
| -------- | ------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------- |
| ADR-0001 | 使用 DuckDB 作为本地核心分析库                   | accepted | `docs/modules/data_validation_write_concurrency.md` / `docs/modules/local_file_system.md` |
| ADR-0002 | Agent 只读、只解释、不直接写库                   | accepted | `docs/modules/agent_module.md`                                                            |
| ADR-0003 | Layer 1 才物化完整标准化字段                     | accepted | `docs/modules/layer1_global_regime_panel.md`                                              |
| ADR-0004 | Layer 3 采用资金震动锚点模型并执行方案B          | accepted | `docs/modules/layer3_industry_shock_anchor.md`                                            |
| ADR-0005 | 数据源采用 Primary / Validation / FallbackPolicy | accepted | `docs/modules/data_sources.md`                                                            |

## 扩展 ADR（独立编号体系）

`docs/decisions/` 使用独立的 ADR 编号；以下已接受决策同样是本项目设计权威的一部分。

| ADR     | 决策                                           | 状态     | 对应模块                                                                                |
| ------- | ---------------------------------------------- | -------- | --------------------------------------------------------------------------------------- |
| ADR-017 | 动态数据源降级、异常数据生命周期与主源恢复回补 | accepted | `docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md` |
| ADR-018 | 启用策略两层接缝与 FRED 编排合并关账           | accepted | `docs/decisions/design/ADR-018-enable-seam-two-layer-and-fred-merge-gate.md`            |
