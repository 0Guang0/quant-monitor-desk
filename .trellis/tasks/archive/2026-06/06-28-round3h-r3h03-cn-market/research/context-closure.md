# R3H-03 Execute Context Closure

## Upstream / wiring closure

- **Upstream:** R3H-01/02 CLOSED; staged pilot baostock/cninfo shapes migrated into `cn_market` normalizer.
- **Wiring:** fetch_ports → `cn_market_evidence_v1` → route_planner/registry; auth-gated ports → `license_gate`.
- **Parallel:** R3H-04 sources untouched; coordinator manifest at `research/execute-evidence/9.8-manifest.md`.

## Scope

- Task: `06-28-round3h-r3h03-cn-market` / branch `feature/round3h-r3h03-cn-market`
- Ten CN sources: baostock, cninfo, akshare, tdx_pytdx, mootdx, eastmoney, sina_finance, ths_ifind, qmt_xtdata, qmt_xqshare
- SSOT: `frozen/R3H_03_CN_MARKET_ADAPTERS.md` + `EXECUTION_INDEX.md` + `implement.jsonl`

## Implemented

- `cn_market_evidence_v1` normalizer + `license_gate` (QMT/iFinD/xqshare)
- Nine new fetch ports + hardened tdx_pytdx baseline (existing)
- Replay fixtures under `tests/fixtures/replay/cn_market/`
- Registry/capability/provider catalog: ten-source `READY_WITH_EVIDENCE`
- Layer CN smoke + **full** `cn_market` health profile (G2/G17):
  - `cn_trading_calendar.py` — L2 EasyXT `TradingCalendar` holidays → QMD calendar
  - `calendar_gap_rules.py` — `calendar_authority=True` FAIL path for cn_market
  - `cn_market.py` — OHLCV integrity via `ohlcv_rules` (L2 `data_integrity_checker` semantics)
- Reference adoption repair (2026-06-28): port L1/L2/L3 headers; mootdx extends `tdx_pytdx_port`; cninfo capped PDF live smoke

## Out of scope (per frozen §8)

- R3H-04 sources (kalshi/polymarket/web_search)
- R3H-05 full cross-layer audit
- Main DB `quant_monitor.duckdb` writes

## User gates (Grill-me confirmed)

- **Q8:** mootdx / qmt_xqshare **implemented** (no ADR)
- **Q12:** **full G2/G17** — L2 `TradingCalendar` → `cn_trading_calendar` + authoritative calendar FAIL (not weekday proxy)
- **Q13:** cninfo replay-first metadata + **capped PDF live smoke** (`create_cninfo_pdf_live_fetch_port`, `MAX_PDF_BYTES`)
