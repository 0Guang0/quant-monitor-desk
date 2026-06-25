# R3H-04 — Prediction and Web Evidence Adapters

## 1. Goal

Close every prediction-market and web-evidence source before Round4. These sources are not factual primary sources and must not write clean factual tables.

Required source coverage:

```text
kalshi
polymarket
web_search
```

Each listed source must end as executable evidence/probability path or `ADR_DISABLED_OUT_OF_SCOPE`.

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
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/user_input_privacy_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use agents-for-openbb only as artifact-shape reference when formatting evidence summaries:

```text
参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py
```

Allowed ideas:

- separating source data from generated summary;
- presenting bounded table/dashboard artifact shape;
- not piling unlimited context.

Forbidden:

- copying OpenAI/client loop runtime;
- using Agent output as fact source;
- web search clean write;
- resolving factual event outcomes from prediction prices;
- bypassing manual review.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/kalshi_port.py
backend/app/datasources/fetch_ports/polymarket_port.py
backend/app/datasources/fetch_ports/web_search_evidence_port.py
backend/app/datasources/normalizers/probability_signal.py
backend/app/evidence/manual_review_staging.py
backend/app/core/resource_guard.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_prediction_market_adapters.py
tests/test_web_evidence_adapter.py
tests/test_source_route_planner.py
tests/test_no_clean_write_for_web_evidence.py
tests/fixtures/replay/prediction_market/**
tests/fixtures/replay/web_evidence/**
```

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license/terms decision;
3. ResourceGuard caps for query count, markets/events, rows, and time window;
4. route planner READY/evidence-only tests and clean-write negative tests;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. output type: `probability_signal`, `event_contract`, `supplemental_web_evidence`, or `manual_review_evidence`;
8. Layer5/manual-review binding, not clean factual table binding.

Minimum domain expectations:

| Source       | Expected role                                             |
| ------------ | --------------------------------------------------------- |
| `kalshi`     | regulated event contract / probability signal             |
| `polymarket` | prediction-market probability / event contract validation |
| `web_search` | supplemental evidence/manual review only                  |

---

## 6. Done criteria

- Every listed source has executable evidence/probability path or ADR-disabled status.
- No listed source writes clean factual tables.
- Prediction markets cannot resolve factual outcomes.
- Web evidence always remains manual-review/evidence-staging only.
- Tests and contract coverage are updated.
