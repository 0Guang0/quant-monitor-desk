# R3H-07 外部索引

> **§A** = 切片开工必读 · **§B** = 情境路由 · **§C** = 源码字典

---

## §A — 切片开工前必读（外部）

| #   | 路径                                                                                                                             | 内容               |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| A1  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_07_US_TRADING_CALENDAR.md` | 活卡               |
| A2  | `docs/implementation_tasks/.../WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`                                                        | Wave 1 §2 AC       |
| A3  | `docs/decisions/ADR-026-r3h07-us-trading-calendar-ssot.md`                                                                       | US 日历 SSOT       |
| A4  | `docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md`                                                            | 前置 C2（只读）    |
| A5  | `specs/contracts/reference_adoption_guardrails.yaml`                                                                             | L1/L2/L3           |
| A6  | `specs/contracts/datasource_service_contract.yaml`                                                                               | Service 契约       |
| A7  | `AGENTS.md`                                                                                                                      | Trellis · GitNexus |

---

## §B — 执行情境路由（外部）

| 情境                       | 路径                                                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CAL-US / PASS 登记         | `docs/quality/round3h_real_data_production_entry_audit.md`                                                   |
| R3H-10 关账 / Wave 2 defer | `.trellis/tasks/archive/2026-06/06-29-round3h-r3h10-datasource-service-ssot/research/audit-repair-ledger.md` |
| CN 日历闭合证据            | `.trellis/tasks/archive/2026-06/06-28-round3h-r3h03-cn-market/`                                              |
| 模块轨 / PASS              | `R3H_PASS_EXECUTION_PLAN.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md`                                           |
| Layer4 契约                | `specs/contracts/layer4_market_contract.yaml`                                                                |
| ADR 目录                   | `docs/decisions/README.md`                                                                                   |

---

## §C — 源码 · 测试字典

| 模块                   | 路径                                                                                                                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CN 日历（只读镜像）    | `backend/app/ops/data_health_profiles/cn_trading_calendar.py`                                                                                                                         |
| US 日历（S07-01 新建） | `backend/app/ops/data_health_profiles/us_trading_calendar.py`                                                                                                                         |
| fetch 窗口             | `backend/app/datasources/fetch_window.py`                                                                                                                                             |
| US ports               | `backend/app/datasources/fetch_ports/yahoo_finance_port.py` · `stooq_port.py` · `alpha_vantage_port.py`                                                                               |
| evidence               | `backend/app/datasources/normalizers/market_data.py`                                                                                                                                  |
| DataSourceService      | `backend/app/datasources/service.py`                                                                                                                                                  |
| Layer4                 | `backend/app/layer4_markets/market_structure.py`                                                                                                                                      |
| 核心测试               | `tests/test_market_data_adapters.py` · `tests/test_layer4_market_structure.py` · `tests/test_cn_market_adapters.py` · `tests/test_datasource_service.py`（S07-01 另建 us 日历模块测） |

---

## 参考项目

| 说明           | 路径                                   |
| -------------- | -------------------------------------- |
| 结论 SSOT      | `research/reference-adoption-r3h07.md` |
| 参考树（只读） | `参考项目/**`                          |
