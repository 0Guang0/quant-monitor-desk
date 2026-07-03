# M-DATA-03 EXTERNAL-INDEX

> 包外必读 · Plan v4.1 §A/B/C

---

## §A 切片开工前必读（外部）

| #   | 路径                                                                                      | 用途                    |
| --- | ----------------------------------------------------------------------------------------- | ----------------------- |
| A1  | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md`                | 活任务卡                |
| A2  | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1 · §0.3.3–0.3.4                                   | 活规划 AC               |
| A3  | `MODULE_COMPLETION_RATING.md` §0 · §3.C–E                                                 | 评级诚实                |
| A4  | `docs/modules/data_sync_orchestrator.md` §13.4.2                                          | watermark 契约          |
| A5  | `docs/modules/datasource_service.md`                                                      | 生产 fetch SSOT         |
| A6  | `specs/contracts/reference_adoption_guardrails.yaml`                                      | 参考红线                |
| A7  | `docs/implementation_tasks/archive/.../R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1 | Tier A 逐源表           |
| A8  | `.trellis/tasks/archive/2026-07/wave4-r3-dcp-05-tier-a/research/to-issues-slices.md`      | DCP-05 切片先例（只读） |
| A9  | `MIGRATION_MAP.md` §4.12                                                                  | 模块地图                |

---

## §B 执行情境路由（外部）

| 情境          | 路径                                                         |
| ------------- | ------------------------------------------------------------ |
| CLI sync 矩阵 | `docs/ops/data_sync_command_matrix.md`                       |
| Sync 速查     | `docs/ops/data_sync_quick_reference.md`                      |
| DB inspect    | `docs/ops/db_inspect_cli.md`                                 |
| 性能预算      | `docs/ops/performance_limits.md`                             |
| Registry      | `specs/datasource_registry/source_registry.yaml`             |
| Clean 目标    | `backend/app/ops/sandbox_clean_write/clean_write_targets.py` |
| 待修复清单    | `docs/quality/待修复清单.md`（若 live blocker 登记）         |

---

## §C 源码/测试字典

| 源            | port                                | ops                               | e2e test                                |
| ------------- | ----------------------------------- | --------------------------------- | --------------------------------------- |
| fred          | `fetch_ports/fred_port.py`          | `ops/fred_incremental_run.py`     | `test_fred_macro_incremental_e2e.py`    |
| us_treasury   | `fetch_ports/us_treasury_port.py`   | `ops/us_treasury_incremental_*`   | `test_us_treasury_incremental_e2e.py`   |
| sec_edgar     | `fetch_ports/sec_edgar_port.py`     | `ops/sec_edgar_incremental_*`     | `test_sec_edgar_incremental_e2e.py`     |
| cftc_cot      | `fetch_ports/cftc_port.py`          | `ops/cftc_incremental_*`          | `test_cftc_incremental_e2e.py`          |
| bis           | `fetch_ports/bis_port.py`           | `ops/bis_incremental_*`           | `test_bis_incremental_e2e.py`           |
| world_bank    | `fetch_ports/world_bank_port.py`    | `ops/world_bank_incremental_*`    | `test_world_bank_incremental_e2e.py`    |
| alpha_vantage | `fetch_ports/alpha_vantage_port.py` | `ops/alpha_vantage_incremental_*` | `test_alpha_vantage_incremental_e2e.py` |
| deribit       | `fetch_ports/deribit_port.py`       | `ops/deribit_incremental_*`       | `test_deribit_incremental_e2e.py`       |
| baostock      | `fetch_ports/baostock_port.py`      | `ops/baostock_incremental_*`      | `test_baostock_incremental_e2e.py`      |
| cninfo        | `fetch_ports/cninfo_port.py`        | `ops/cninfo_incremental_*`        | `test_cninfo_incremental_e2e.py`        |
| mootdx        | `fetch_ports/mootdx_port.py`        | `ops/mootdx_incremental_*`        | `test_mootdx_incremental_e2e.py`        |

**横切：** `product_live_gate.py` · `sync/orchestrator.py` · `data_commands.py`

---

## §E 官方 API（source-driven-development · live RED 前必读）

**SSOT：** `plan-spec.md` §Official API（本表为薄指针，以 plan-spec 为准）。

| source_id     | 权威 URL                                                                   |
| ------------- | -------------------------------------------------------------------------- |
| fred          | https://fred.stlouisfed.org/docs/api/fred/series_observations.html         |
| us_treasury   | https://fiscaldata.treasury.gov/api-documentation/                         |
| sec_edgar     | https://www.sec.gov/search-filings/edgar-application-programming-interface |
| cftc_cot      | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm          |
| bis           | https://stats.bis.org/api-doc/v1                                           |
| world_bank    | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392           |
| alpha_vantage | https://www.alphavantage.co/documentation/                                 |
| deribit       | https://docs.deribit.com/                                                  |
| baostock      | http://baostock.com/baostock/index.php/Python_API文档                      |
| cninfo        | 仓内 `cninfo_port.py` 头部注释 + 巨潮公开说明                              |
| mootdx        | 仓内 `mootdx_port.py` + pytdx 文档                                         |

---

## §D 参考项目实读（Execute RED 前）

见 `reference-adoption-m-data-03.md` §1–§2；基线三文件：

- `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py`
- `参考项目/digital-oracle/digital_oracle/providers/bis.py`
- `参考项目/EasyXT/data_manager/unified_data_interface.py` L172–244
