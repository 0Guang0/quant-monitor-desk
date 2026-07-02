# Execute reference read evidence — Market (`feature/m-data-03-market`)

> Per `parallel-dispatch-protocol.md` §3 · RED before live e2e · 2026-07-03

## Agent scope

| Field  | Value                                                                                    |
| ------ | ---------------------------------------------------------------------------------------- |
| Agent  | Execute Agent 4 (Market)                                                                 |
| Slices | S-LIVE-SEC-EDGAR · S-LIVE-ALPHA-VANTAGE · S-LIVE-DERIBIT · S-LIVE-CNINFO · S-LIVE-MOOTDX |
| Branch | `feature/m-data-03-market`                                                               |

## 借鉴等级（§0 仓内 = 直接复用）

Market 五源均为 **L3**（`reference-adoption-m-data-03.md` §2.1 · §3）。仓内 `*_port.py` + `*_incremental_run.py` **直接复用**，禁止标 L1/L2/L3。

| source_id     | SDD（plan-spec §Official API）                                             | 仓内触点                                               | live 门                                           |
| ------------- | -------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------- |
| sec_edgar     | https://www.sec.gov/search-filings/edgar-application-programming-interface | `sec_edgar_port` · `sec_edgar_incremental_run`         | `SEC_EDGAR_USER_AGENT` + `QMD_ALLOW_LIVE_FETCH=1` |
| alpha_vantage | https://www.alphavantage.co/documentation/                                 | `alpha_vantage_port` · `alpha_vantage_incremental_run` | `ALPHA_VANTAGE_API_KEY` + gate                    |
| deribit       | https://docs.deribit.com/                                                  | `deribit_port` `DeribitLiveFetchPort`                  | gate only（public REST）                          |
| cninfo        | 巨潮公开接口 + 仓内 port 注释                                              | `cninfo_port` `CninfoProductLiveFetchPort`             | gate · replay-first                               |
| mootdx        | pytdx / 通达信（R3FR 仓内）                                                | `mootdx_port` · `mootdx_incremental_run`               | gate · replay-first                               |

## OpenBB 三阶段对齐（L3 概念 only）

| OpenBB 阶段       | QMD market 对齐                                                |
| ----------------- | -------------------------------------------------------------- |
| `transform_query` | watermark → `FetchRequest.start_time` / bar window             |
| `extract_data`    | `create_*_fetch_port(use_mock=False)` + `gate_live_fetch_port` |
| `transform_data`  | staging adapter → ADR-028 clean 表                             |

**禁止：** 拷贝 OpenBB Fetcher/Provider（AGPL）。

## 分源 harness 动作

### SEC EDGAR

- **Read:** SDD EDGAR API · `sec_edgar_port.py` rate limit / `SEC_EDGAR_USER_AGENT`
- **ponytail:** live branch 暂 delegate mock replay（gate 已接通）；network 测验证隔离路径 + clean 写
- **Harness:** `bootstrap_sec_edgar_live_e2e_ctx` → `run_sec_edgar_incremental` → `us_disclosure_clean`

### Alpha Vantage

- **Read:** SDD TIME_SERIES_DAILY · credentials 门概念（OpenBB L3）
- **ponytail:** `AlphaVantageLiveFetchPort` delegate mock until dedicated urllib slice
- **Harness:** skip without `ALPHA_VANTAGE_API_KEY` · `security_bar_1d`

### Deribit

- **Read:** SDD `public/get_instruments` + `get_book_summary_by_instrument`（`mark_iv` 仅后者提供）
- **改造点:** `DeribitLiveFetchPort._book_summary_mark_iv` 补齐 IV；live e2e 用 `_resolve_deribit_live_instrument` 取当前合约名
- **Harness:** 真网 → `crypto_derivative_clean`（clean 行 SQL 断言；表不在 `ops_db_inspect_contract` key_tables）

### CNINFO · MOOTDX

- **Read:** `cn_product_live_replay.py` replay-first 形态（R3H-08，非 EasyXT forbidden）
- **forbidden 负向:** 不在本 agent（S00-INFRA silent-fallback 已覆盖）
- **Harness:** 同 baostock pilot — `build_*_live` + `isolated_live_data_root`

## 复用仓内模式

| Pattern                  | Path                                          |
| ------------------------ | --------------------------------------------- |
| Isolated sandbox         | `tests/conftest.py` `isolated_live_data_root` |
| Product live gate        | `product_live_gate.py` · ADR-027              |
| Network skip default     | `conftest.py` `--run-network`                 |
| Post-write inspect smoke | `DbInspector.inspect()`                       |
| Pilot precedent          | `execute-reference-read-evidence-pilot.md`    |

## S-ACCEPT deferral

本 agent 仅 `-m network` e2e + `DbInspector` 表/行数。完整 `qmd data inspect` + data health P0 属 **S-ACCEPT**（`tier_a_live_acceptance.py` 11/11）。
