# Execute reference read evidence — Macro (`feature/m-data-03-macro`)

> Per `parallel-dispatch-protocol.md` §3 · RED before live e2e · 2026-07-03

## Agent scope

| Field  | Value                                                            |
| ------ | ---------------------------------------------------------------- |
| Agent  | Execute Agent 3 (Macro)                                          |
| Slices | S-LIVE-US-TREASURY · S-LIVE-BIS · S-LIVE-WORLDBANK · S-LIVE-CFTC |
| Branch | `feature/m-data-03-macro`                                        |

## BIS — L2 (digital-oracle bis.py L54–66)

**Read:** `reference-adoption-m-data-03.md` §2.2 · `bis_port.py` · `bis_incremental_run.py`

### 借鉴点（concept only）

| digital-oracle                               | QMD 仓内对齐                                                                  |
| -------------------------------------------- | ----------------------------------------------------------------------------- |
| `startPeriod` / `start_year` 来自 query 窗   | `FetchRequest.start_time` → `BisLiveFetchPort._resolve_start_year`            |
| HTTP CSV URL `stats.bis.org/api/v1/data/...` | `BIS_BASE_URL` + `WS_CBPOL` path（仓内 `bis_port.py`）                        |
| watermark 驱动增量窗                         | `read_observation_date_watermark` → `compute_since_date` → proxy `start_time` |

### 改造点（禁止直接 import）

| 禁止                                        | 仓内替代                                                      |
| ------------------------------------------- | ------------------------------------------------------------- |
| `from digital_oracle... import BisProvider` | `create_bis_fetch_port(use_mock=False)` → `BisLiveFetchPort`  |
| 参考 `SignalProvider` 平行体系              | 既有 `source_registry.yaml` + `MacroIncrementalSourceConfig`  |
| 参考 CSV 解析未改写粘贴                     | `official_macro_evidence_v1` + `bis_staging_rows_from_bundle` |
| 参考直连 HTTP 无 guard                      | `gate_live_fetch_port(source_id="bis")` + `ResourceGuard`     |

**负向测：** `test_bisIncremental_forbidden_noBisProviderRuntimeImport`（AST import 根扫描）

**SDD:** `plan-spec.md` — https://stats.bis.org/api-doc/v1

## US Treasury — L3

**Read:** `reference-adoption-m-data-03.md` §3 us_treasury row · OpenBB 三阶段 **概念**

| Stage           | QMD                                                      |
| --------------- | -------------------------------------------------------- |
| transform_query | `read_since_dates_for_instruments` → since map           |
| extract_data    | `UsTreasuryLiveFetchPort` HTTP                           |
| transform_data  | `treasury_staging_rows_from_bundle` → `axis_observation` |

**SDD:** https://fiscaldata.treasury.gov/api-documentation/

**Harness:** `bootstrap_macro_live_e2e_ctx` + `run_us_treasury_incremental(use_mock=False)`

## World Bank — L3

**Read:** `reference-adoption-m-data-03.md` §2.2 L2 同族窗参数思路 · §3 world_bank row

| Concept                 | QMD                                                  |
| ----------------------- | ---------------------------------------------------- |
| indicator + date window | `clean_indicator_id` + `compute_since_date`          |
| API 窗参数              | `WorldBankLiveFetchPort` + `FetchRequest.start_time` |

**SDD:** https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

**Harness:** `run_world_bank_incremental(use_mock=False)` under `isolated_live_data_root`

## CFTC — L3

**Read:** `reference-adoption-m-data-03.md` §3 cftc_cot row

| Concept               | QMD                                                      |
| --------------------- | -------------------------------------------------------- |
| 周频 watermark        | `WEEKLY_ADVANCE_DAYS=7` + `read_since_dates_for_markets` |
| COT positioning clean | `cftc_staging_rows_from_bundle` → `axis_observation`     |

**SDD:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

**Harness:** `run_cftc_incremental(use_mock=False)` under `isolated_live_data_root`

## Reused in-repo patterns (direct reuse)

| Pattern                  | Path                                                                |
| ------------------------ | ------------------------------------------------------------------- |
| Isolated sandbox         | `tests/conftest.py` `isolated_live_data_root`                       |
| Macro live bootstrap     | `tests/macro_incremental_support.py` `bootstrap_macro_live_e2e_ctx` |
| Product live gate        | `product_live_gate.py`                                              |
| Incremental ops          | `*_incremental_run.py`（仓内 DCP-05 直接复用）                      |
| Post-write inspect smoke | `DbInspector.inspect()`                                             |

## S-ACCEPT deferral note

Macro slice verifies `DbInspector` table existence + row counts. Full `qmd data inspect` + `data_health` P0 gate per source is **S-ACCEPT** scope (`tier_a_live_acceptance.py` 11/11).
