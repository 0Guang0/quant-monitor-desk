# R3H-01 — Official Macro and Disclosure Adapters

## 1. Goal

Close every official macro / regulator / filing source before Round4. This is not a sample-source task.

Required source coverage:

```text
fred
us_treasury
sec_edgar
cftc_cot
bis
world_bank
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
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/snapshot_lineage_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Reference tree:

```text
C:\Users\Guang\Desktop\quant-monitor-desk\参考项目
```

Use OpenBB provider structure only for architecture ideas:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/
```

Allowed ideas:

- provider metadata shape;
- optional auth/extras/terms metadata;
- provider README/catalog organization;
- source/domain separation.

Forbidden:

- copying OpenBB AGPL runtime provider source;
- importing `参考项目/**` from backend runtime;
- bypassing QMD route/auth/ResourceGuard gates.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/fred_port.py
backend/app/datasources/fetch_ports/us_treasury_port.py
backend/app/datasources/fetch_ports/sec_edgar_port.py
backend/app/datasources/fetch_ports/cftc_cot_port.py
backend/app/datasources/fetch_ports/bis_port.py
backend/app/datasources/fetch_ports/world_bank_port.py
backend/app/datasources/normalizers/official_macro.py
backend/app/datasources/normalizers/sec_edgar.py
backend/app/datasources/auth/license_gate.py
backend/app/core/resource_guard.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_official_macro_adapters.py
tests/test_sec_edgar_adapter.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/fixtures/replay/official_macro/**
tests/fixtures/replay/sec_edgar/**
```

Do not create a generic catch-all `official_adapter.py` that hides source-specific auth, rate limits, fields, and evidence rules.

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license decision;
3. ResourceGuard caps for symbols/series/window/rows;
4. route planner READY test and DISABLED/unauthorized negative test;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. data health or freshness checks appropriate to low-frequency official data;
8. Layer1/Layer5 binding where the source feeds macro/disclosure evidence.

Minimum domain expectations:

| Source        | Domains                                      |
| ------------- | -------------------------------------------- |
| `fred`        | P0 macro series live/authorized closure      |
| `us_treasury` | yield curve, inflation expectation reference |
| `sec_edgar`   | company filings, Form 4 insider transactions |
| `cftc_cot`    | weekly COT positioning                       |
| `bis`         | policy rates, credit-to-GDP gap              |
| `world_bank`  | low-frequency development indicators         |

---

## 6. Done criteria

- Every listed source is `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.
- No listed source remains a vague proposed-disabled placeholder.
- Official factual sources have higher route priority than aggregators/web sources.
- Layer1/Layer5 can consume at least the declared official macro/disclosure evidence path.
- Tests and contract coverage are updated.
