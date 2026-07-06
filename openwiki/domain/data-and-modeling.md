# Data And Modeling Domain

The product is a monitoring and explanation system, not an automatic trading system. The canonical workflow in `README.md` and `docs/architecture/00_project_overview.md` is trusted data, multi-layer modeling, evidence-chain monitoring, read-only agent explanation, and human confirmation.

## Core boundaries

- Local-first: data, DuckDB, raw files, reports, and audit artifacts live under local project/runtime paths unless explicitly configured otherwise.
- Human review: severe conflicts and action-like conclusions are not silently accepted.
- Agent read-only: docs and contracts say agents may summarize structured evidence but must not write clean tables, place orders, directly fetch arbitrary web data, or override factual sources.
- Source roles: the current model is `Primary / Validation / FallbackPolicy`. The README explicitly forbids restoring old `Shadow / Emergency` roles as source roles, with only narrow diagnostic Layer 1 exceptions.

## Five-layer model

The design docs define five modeling layers. Current source contains one package per layer:

1. Layer 1 global regime/five-axis panel: `backend/app/layer1_axes/`
2. Layer 2 cross-asset sensors: `backend/app/layer2_sensors/`
3. Layer 3 global industry chain shock anchors: `backend/app/layer3_chains/`
4. Layer 4 market structure: `backend/app/layer4_markets/`
5. Layer 5 evidence/security evidence: `backend/app/layer5_evidence/`

Layer 1 is the most standardized. `docs/modules/layer1_global_regime_panel.md` defines the five axes: environment, credit stress, risk appetite, liquidity, and sentiment. `backend/app/layer1_axes/axis_loader.py` loads external YAML specs from `specs/layer1_axes/restructured_axes_v1_1/`, validates required indicator fields, and preserves guardrail concepts such as diagnostic-only indicators, forbidden substitutes, quality rules, stale rules, and explanation boundaries.

Layer 2 uses cross-asset registry loaders and guarded writes. `backend/app/layer2_sensors/sensor_loader.py` reads staged or clean-replay registry YAML, validates asset groups and double-count rules, and writes through `WriteManager`.

Layer 3 is not a generic sector list. The architecture docs define it as a global industry-chain shock-anchor layer for entities and commodities that can reprice supply chains through capex, capacity, bottlenecks, policy, events, or commodity prices. Source lives under `backend/app/layer3_chains/`, with specs under `specs/layer3_global_industry_chains/`.

Layer 4 models market-specific structure, such as US equity, CN equity, futures, options, breadth, limits, market rules, and snapshot/read models. Source lives under `backend/app/layer4_markets/`.

Layer 5 stores verifiable evidence and instrument-level facts. `backend/app/layer5_evidence/evidence_chain.py` composes foundation validation with upstream Layer 1-4 context. It requires upstream snapshot IDs, Layer 3/4 context, validates staged evidence, queues manual review for severe conflicts, and includes a guard that rejects agent text as factual source.

## Data source semantics

`docs/modules/data_sources.md` and current datasource code separate fetching from truth selection. Datasource modules fetch auditable raw/staged evidence; validation and conflict modules decide if data can become clean. Important rules:

- Raw data is retained for replay and audit.
- Clean tables should contain validated main values.
- Small source differences can be warnings; severe conflicts go to `source_conflict` and can trigger reconcile.
- Silent source switching is forbidden. Fallback must be recorded through route plans, quality flags, source-switch metadata, or audit logs.
- Licensed/local-client sources such as QMT, iFinD, and qmt_xqshare require explicit user authorization and platform/env gates.

## Agent and report semantics

The architecture docs describe reports as reading snapshot tables, staging controlled agent output, applying no-action-semantics guards, then building reports/notifications. Current code and docs keep agent output downstream of facts. Do not treat LLM text or manually imported prose as a clean factual source unless it is linked to fixed source adapters or manual review staging rules.

## Source references

- `README.md`
- `docs/architecture/00_project_overview.md`
- `docs/modules/layer1_global_regime_panel.md`
- `docs/modules/data_sources.md`
- `backend/app/layer1_axes/axis_loader.py`
- `backend/app/layer2_sensors/sensor_loader.py`
- `backend/app/layer5_evidence/evidence_chain.py`
- `specs/layer1_axes/`
- `specs/layer3_global_industry_chains/`
