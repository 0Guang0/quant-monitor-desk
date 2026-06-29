# R3H-08 外部索引

> **§A** = 切片开工必读 · **§B** = 情境路由 · **§C** = 源码字典

---

## §A — 切片开工前必读（外部）

| #   | 路径                                                                                                                             | 用途           |
| --- | -------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| A1  | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_08_LIVE_PRODUCTIZATION.md` | 活卡           |
| A2  | `docs/implementation_tasks/.../WAVE2_R3H08_TO_ISSUES_INDEX.md`                                                                   | Wave 2 INDEX   |
| A3  | `docs/implementation_tasks/.../R3H_PASS_EXECUTION_PLAN.md` §2                                                                    | Tier 表        |
| A4  | `docs/quality/production_live_pilot_policy.md`                                                                                   | rehearsal 边界 |
| A5  | `docs/decisions/ADR-027-r3h08-product-live-env-gate.md`                                                                          | 架构 ADR       |
| A6  | `docs/decisions/ADR-025-r3h10-sync-fail-closed-datasource-service.md`                                                            | Sync           |
| A7  | `specs/contracts/reference_adoption_guardrails.yaml`                                                                             | L1/L2/L3       |

---

## §B — 执行情境路由（外部）

| 情境              | 路径                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------------------- |
| C2 SSOT 先例      | `.trellis/tasks/archive/2026-06/06-29-round3h-r3h10-datasource-service-ssot/research/00-EXECUTION-ENTRY.md` |
| R3H-10 defer 台账 | `.../audit-repair-ledger.md` §Wave 2                                                                        |
| 模块轨 Wave 2     | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.2                                                                    |
| R3G-03 promote    | `docs/implementation_tasks/.../R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`                                    |
| ADR 目录          | `docs/decisions/README.md`                                                                                  |

---

## §C — 源码字典

| 路径                                                              | 用途              |
| ----------------------------------------------------------------- | ----------------- |
| `backend/app/datasources/service.py`                              | DataSourceService |
| `backend/app/datasources/fetch_ports/`                            | per-source live   |
| `backend/app/ops/sandbox_clean_write/limited_production_entry.py` | Tier B            |
| `backend/app/ops/sandbox_clean_write/clean_write_targets.py`      | Tier A 域         |
| `backend/app/ops/rehearsal_boundary.py`                           | REHEARSAL_ONLY    |
| `backend/app/sync/orchestrator.py`                                | Sync 金路径       |
| `backend/app/ops/interface_probe.py`                              | probe defer       |

---

## §D — 参考项目源码（只读 · Execute RED 前必 Read）

> **强制：** 见 `00-EXECUTION-ENTRY.md` §2.1 · `reference-adoption-r3h08.md` §7。  
> **禁止：** runtime import；**禁止**不 Read 就从零造。  
> 完整逐切片表：`reference-adoption-r3h08.md` §7.2。

| 切片       | `参考项目/**` 路径（仓库根相对）                                                |
| ---------- | ------------------------------------------------------------------------------- |
| S08-BOOT   | （无参考树文件；Read `reference_adoption_guardrails.yaml` + §7 全文）           |
| S08-01 08C | `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` |
|            | `参考项目/digital-oracle/digital_oracle/providers/bis.py`                       |
|            | `参考项目/digital-oracle/digital_oracle/providers/base.py`                      |
| S08-02 08A | `参考项目/EasyXT/data_manager/unified_data_interface.py`                        |
| S08-03 08B | `参考项目/EasyXT/data_manager/unified_data_interface.py`                        |
|            | `参考项目/digital-oracle/digital_oracle/providers/yfinance_provider.py`         |
| S08-04 08D | `参考项目/digital-oracle/digital_oracle/providers/kalshi.py`                    |
|            | `参考项目/digital-oracle/digital_oracle/providers/polymarket.py`                |
| S08-05     | `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py` |

**EasyXT 附加反例（触及时 Read）：** `参考项目/EasyXT/data_manager/auto_data_updater.py` L31-32, L87-97
