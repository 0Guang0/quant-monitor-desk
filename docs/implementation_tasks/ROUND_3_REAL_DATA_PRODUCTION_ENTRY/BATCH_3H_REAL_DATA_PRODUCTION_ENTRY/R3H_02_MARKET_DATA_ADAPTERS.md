# R3H-02 — Market Data Adapters

## 1. Goal

Close every cross-asset / US market / crypto market source before Round4. This is not a one-provider sample.

Required source coverage:

```text
alpha_vantage
stooq
yahoo_finance
deribit
coingecko
```

Each listed source must end as `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

---

## 2. QMD files to read

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/data_quality_rules.yaml
specs/contracts/resource_limits.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use OpenBB provider packaging/catalog layout only as architecture reference:

```text
参考项目/OpenBB/openbb_platform/providers/
```

Use JQ2PTrade/EasyXT only for read-only loader/report constraints if this task touches frozen market datasets:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/api_mapping.json
参考项目/EasyXT/data_manager/data_integrity_checker.py
```

Forbidden:

- copying OpenBB runtime provider code;
- using JQ2PTrade order/trade/portfolio APIs;
- broad default scans;
- full option-chain scans by default;
- crypto account/trading semantics.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/alpha_vantage_port.py
backend/app/datasources/fetch_ports/stooq_port.py
backend/app/datasources/fetch_ports/yahoo_finance_port.py
backend/app/datasources/fetch_ports/deribit_port.py
backend/app/datasources/fetch_ports/coingecko_port.py
backend/app/datasources/normalizers/market_data.py
backend/app/datasources/normalizers/crypto_market.py
backend/app/datasources/auth/license_gate.py
backend/app/core/resource_guard.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/resource_limits.yaml
specs/verification/contract_coverage.yaml
tests/test_market_data_adapters.py
tests/test_crypto_market_adapters.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/market_data/**
tests/fixtures/replay/crypto_market/**
```

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license/rate-limit decision;
3. ResourceGuard caps for symbol count, window, rows, option-chain breadth, and crypto instrument count;
4. route planner READY test and DISABLED/unauthorized/rate-limited negative tests;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health checks for OHLCV/date/freshness/field completeness;
8. Layer2/Layer4/Layer5 binding where this source feeds market data or evidence.

Minimum domain expectations:

| Source          | Domains                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------- |
| `alpha_vantage` | US equity daily bar, ETF daily bar, US option chain, FX/commodity/macro/crypto references |
| `stooq`         | global daily bar, FX daily bar, commodity daily bar                                       |
| `yahoo_finance` | validation-only US equity/ETF/option-chain posture unless ADR changes scope               |
| `deribit`       | crypto derivatives, futures term structure, options surface                               |
| `coingecko`     | crypto spot market and asset reference as aggregator/validation                           |

---

## 6. Done criteria

- Every listed source is `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.
- Aggregators cannot silently become primary where official/exchange-grade source is required.
- Option-chain and crypto derivatives paths have strict caps.
- Layer2/Layer4/Layer5 can consume the declared real market-data/evidence envelope.
- Tests and contract coverage are updated.
