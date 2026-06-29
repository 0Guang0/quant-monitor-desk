# R3H-08 Live-tier 基线矩阵（S08-BOOT Execute 产出）

> **SSOT：** `R3H_PASS_EXECUTION_PLAN.md` §2.1 · `reference-adoption-r3h08.md` §4  
> **门禁 cite：** `specs/contracts/reference_adoption_guardrails.yaml` L13-28 `adoption_ladder`（L1/L2/L3 列定义）  
> **状态日期：** 2026-06-29 · Step 9.0 S08-BOOT

## 摘要

- **24 业务源** env-gated 产品 live 盘点；`web_search` 真 API **延后 post-Round4**（本矩阵仍列 Tier C mock）。
- **当前态：** 多数 port `mock-default`；部分宏观/概率源有 **rehearsal/smoke opt-in**（非 `ProductLiveGate` 金路径）。
- **目标：** `DataSourceService` + `ProductLiveGate` + 各切片启用 port live 分支。

## 矩阵（24 行）

| source_id       | tier  | port                                      | 当前状态                                                                                                       | 目标切片                 | reference_anchor                                                                               | adoption_level |
| --------------- | ----- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------- | -------------- |
| `fred`          | **A** | `fetch_ports/fred_port.py`                | mock-default; `FredLiveFetchPort` opt-in (`use_mock=False`); promote 路径 `limited_production_entry` fred-only | S08-01 08C               | `reference-adoption-r3h08.md` §3.1 OpenBB `fetcher.py` L36-85 arch; QMD `fred_port.py` L93-109 | L2/L3          |
| `us_treasury`   | **A** | `fetch_ports/us_treasury_port.py`         | mock-default; `UsTreasuryLiveFetchPort` opt-in                                                                 | S08-01 08C               | `reference-adoption-r3h08.md` §4 macro Tier A; OpenBB arch                                     | L2/L3          |
| `sec_edgar`     | **A** | `fetch_ports/sec_edgar_port.py`           | mock-default; live branch opt-in                                                                               | S08-01 08C               | `reference-adoption-r3h08.md` §4; disclosure primary                                           | L2/L3          |
| `cftc_cot`      | **A** | `fetch_ports/cftc_cot_port.py`            | mock-default (`use_mock=True`); live stub                                                                      | S08-01 08C               | `reference-adoption-r3h08.md` §4 macro primary                                                 | L2/L3          |
| `bis`           | **A** | `fetch_ports/bis_port.py`                 | mock-default; `BisLiveFetchPort` opt-in                                                                        | S08-01 08C               | `参考项目/digital-oracle/digital_oracle/providers/bis.py` L46-66 CSV URL/parse                 | L2             |
| `world_bank`    | **A** | `fetch_ports/world_bank_port.py`          | mock-default; live branch opt-in                                                                               | S08-01 08C               | `reference-adoption-r3h08.md` §4 macro                                                         | L2/L3          |
| `alpha_vantage` | **A** | `fetch_ports/alpha_vantage_port.py`       | mock-default; live partial delegate mock (L178-179 caveat)                                                     | S08-01 08C               | `reference-adoption-r3h08.md` §6 caveat; market primary                                        | L2/L3          |
| `deribit`       | **A** | `fetch_ports/deribit_port.py`             | mock-only surface (no live port yet)                                                                           | S08-01 08C               | `reference-adoption-r3h08.md` §4 crypto primary                                                | L3             |
| `baostock`      | **A** | `fetch_ports/baostock_port.py`            | mock-only; CN rehearsal via `cn_rehearsal_live_ports` (`REHEARSAL_ONLY`)                                       | S08-02 08A               | EasyXT `unified_data_interface.py` L172-237 **forbidden 反例**; QMD `baostock_port.py` L1      | L3             |
| `cninfo`        | **A** | `fetch_ports/cninfo_port.py`              | mock-default; PDF live smoke tier-B (`enable_pdf_live`)                                                        | S08-02 08A               | EasyXT forbidden 反例; QMD `cninfo_port.py`                                                    | L3             |
| `mootdx`        | **A** | `fetch_ports/mootdx_port.py`              | mock-only                                                                                                      | S08-02 08A               | EasyXT forbidden 反例; QMD `mootdx_port.py`                                                    | L3             |
| `yahoo_finance` | **B** | `fetch_ports/yahoo_finance_port.py`       | mock replay; `validation_only` permanent                                                                       | S08-03 08B               | EasyXT validation **forbidden**; `digital-oracle/yfinance_provider.py` L2 HTTP 形态            | L3             |
| `akshare`       | **B** | `fetch_ports/akshare_port.py`             | mock replay validation                                                                                         | S08-03 08B               | EasyXT forbidden; validation_only registry                                                     | L3             |
| `stooq`         | **B** | `fetch_ports/stooq_port.py`               | mock replay validation                                                                                         | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `coingecko`     | **B** | `fetch_ports/coingecko_port.py`           | mock replay validation                                                                                         | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `eastmoney`     | **B** | `fetch_ports/eastmoney_port.py`           | mock replay validation                                                                                         | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `sina_finance`  | **B** | `fetch_ports/sina_finance_port.py`        | mock replay validation                                                                                         | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `tdx_pytdx`     | **B** | `fetch_ports/tdx_pytdx_port.py`           | mock replay validation probe                                                                                   | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `ths_ifind`     | **B** | `fetch_ports/ths_ifind_port.py`           | auth-disabled default; mock                                                                                    | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `qmt_xtdata`    | **B** | `fetch_ports/qmt_xtdata_port.py`          | license-disabled default; mock                                                                                 | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `qmt_xqshare`   | **B** | `fetch_ports/qmt_xqshare_port.py`         | auth-disabled default; mock                                                                                    | S08-03 08B               | EasyXT forbidden                                                                               | L3             |
| `kalshi`        | **C** | `fetch_ports/kalshi_port.py`              | smoke env `KALSHI_LIVE_SMOKE`; not ProductLiveGate                                                             | S08-04 08D               | `参考项目/digital-oracle/.../kalshi.py` L88-96 probability                                     | L2/L3          |
| `polymarket`    | **C** | `fetch_ports/polymarket_port.py`          | smoke env `POLYMARKET_LIVE_SMOKE`; not ProductLiveGate                                                         | S08-04 08D               | `参考项目/digital-oracle/.../polymarket.py` L48-60 OutcomeQuote                                | L2/L3          |
| `web_search`    | **C** | `fetch_ports/web_search_evidence_port.py` | mock-only evidence                                                                                             | **阶段外置 post-Round4** | — (真 API 延后)                                                                                | 阶段外置       |

## web_search 延后注记

`web_search` 真 API 不在 R3H-08 范围；PASS §1 唯一 post-Round4 ADR 项。当前仅 mock Tier C evidence，不启用产品 live。

## ProductLiveGate（BOOT 交付）

| 组件              | 路径                                           | BOOT 状态                                     |
| ----------------- | ---------------------------------------------- | --------------------------------------------- |
| `ProductLiveGate` | `backend/app/datasources/product_live_gate.py` | **已建** · `QMD_ALLOW_LIVE_FETCH` fail-closed |
| `LiveTierRouter`  | `backend/app/datasources/live_tier_router.py`  | **未建** · defer S08-01+                      |

## 参考 cite（BOOT 铁律 B）

| 登记项               | 路径                                                        | 等级                    |
| -------------------- | ----------------------------------------------------------- | ----------------------- |
| adoption_ladder SSOT | `specs/contracts/reference_adoption_guardrails.yaml` L13-28 | 矩阵列定义              |
| 24 源等级表          | `reference-adoption-r3h08.md` §4                            | L1/L2/L3/arch/forbidden |
| Execute §7 BOOT 行   | `reference-adoption-r3h08.md` §7.2 S08-BOOT                 | guardrails yaml         |
