# R3H-03 — CN Market Adapters

## 1. Goal

Close every China-market primary, validation, and authorization-gated source before Round4. This is not only a baostock/cninfo sample task.

Required source coverage:

```text
baostock
akshare
cninfo
tdx_pytdx
mootdx
eastmoney
sina_finance
ths_ifind
qmt_xtdata
qmt_xqshare
```

Each listed source must end as `READY_WITH_EVIDENCE`, validation-only READY, authorization-disabled with tested route reason, or `ADR_DISABLED_OUT_OF_SCOPE`.

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
specs/contracts/source_conflict_rules.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use EasyXT for data health and TDX lifecycle adaptation:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
```

Allowed ideas:

- TDX connection lifecycle;
- server selection/failover shape;
- security list / daily/index quote parsing;
- OHLCV/data-integrity checks.

Forbidden:

- auto-login/account-control/trading;
- full-market/full-history/minute default scan;
- hardcoded DB/table;
- SQL interpolation;
- runtime import from `参考项目/**`.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/baostock_port.py
backend/app/datasources/fetch_ports/akshare_port.py
backend/app/datasources/fetch_ports/cninfo_port.py
backend/app/datasources/fetch_ports/tdx_pytdx_port.py
backend/app/datasources/fetch_ports/mootdx_port.py
backend/app/datasources/fetch_ports/eastmoney_port.py
backend/app/datasources/fetch_ports/sina_finance_port.py
backend/app/datasources/fetch_ports/ths_ifind_port.py
backend/app/datasources/fetch_ports/qmt_xtdata_port.py
backend/app/datasources/fetch_ports/qmt_xqshare_port.py
backend/app/datasources/normalizers/cn_market.py
backend/app/datasources/auth/license_gate.py
backend/app/core/resource_guard.py
backend/app/ops/data_health_profiles/cn_market.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_conflict_rules.yaml
specs/verification/contract_coverage.yaml
tests/test_cn_market_adapters.py
tests/test_tdx_provider_port.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/cn_market/**
```

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port or explicit authorization-disabled adapter boundary;
2. auth/license decision, especially for QMT/xqshare/iFinD;
3. ResourceGuard caps for symbols/window/rows and no full-market defaults;
4. route planner READY/validation-only/disabled tests;
5. replay fixture or sandbox sample where allowed;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health and source conflict checks;
8. Layer3/Layer4/Layer5 binding where this source feeds CN market/evidence paths.

Minimum role expectations:

| Source                       | Expected role                                                                     |
| ---------------------------- | --------------------------------------------------------------------------------- |
| `baostock`                   | CN daily-bar primary candidate for bounded production entry                       |
| `cninfo`                     | announcement/disclosure metadata primary candidate                                |
| `akshare`                    | validation-only unless explicit contract says otherwise                           |
| `tdx_pytdx` / `mootdx`       | raw/validation-only or authorization-gated candidate; no silent fallback          |
| `eastmoney` / `sina_finance` | validation/fallback with source conflict evidence                                 |
| `ths_ifind`                  | authorized validation/research/concept source only after license gate             |
| `qmt_xtdata` / `qmt_xqshare` | local authorized terminal sources; default disabled until user environment exists |

---

## 6. Done criteria

- Every listed source has final decision and tests.
- No CN source silently replaces another source as Primary.
- QMT/iFinD/xqshare remain disabled unless explicit user authorization and environment proof exist.
- Layer3/Layer4/Layer5 have real CN data/evidence paths for declared scope.
- Tests and contract coverage are updated.
