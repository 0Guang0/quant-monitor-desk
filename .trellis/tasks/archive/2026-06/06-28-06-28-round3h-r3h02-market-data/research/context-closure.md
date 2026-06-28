# Context closure — R3H-02

## Upstream wiring

- R3H-01 `fred_port.py` + `official_macro.py` + `evidence_bundle.py` — port/normalizer/preview pattern for 9.1–9.5
- Batch 3G `rehearsal_loader` + `r3g01/yahoo_finance` — yahoo fixture migration target for 9.4
- `implement.jsonl` + frozen §9 + `EXECUTION_INDEX.md` §1–§3 — Execute SSOT
- Five-source registry/capability/route — coordinator batch in 9.6 (`execute-evidence/9.6-manifest.md`)

## Deferred / out of scope

- R3H-05 full five-layer production-entry audit — forbidden; 9.7 smoke only
- Main DB `quant_monitor.duckdb` writes — forbidden
- yahoo `validation_only` promotion — forbidden without ADR
- Full TradingCalendar / G2 exchange window — ponytail calendar_days until R3H-03
- OpenBB / `参考项目/**` runtime import — forbidden

## Slice boundary

- Mock/replay-first fetch ports; live API gates (`ALPHA_VANTAGE_API_KEY` etc.)
- `yahoo_finance` remains `validation_only: true`
- ADR allowed only for stooq/coingecko if truly blocked; alpha_vantage/deribit must reach READY_WITH_EVIDENCE

## GitNexus blast radius (boot)

| Symbol                   | Risk                            |
| ------------------------ | ------------------------------- |
| `YahooFinanceAdapter`    | LOW (d=1: adapters registry)    |
| `DataSourceService`      | MEDIUM (d=1: 6 direct upstream) |
| route_planner / registry | MEDIUM at 9.6                   |
