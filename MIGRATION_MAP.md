# Migration Map — Quant Monitor Desk

Project navigation map for humans and AI coding agents. Use this file to orient in the repository without loading the full design document.

## 1. What this repository is

| Artifact | Role |
|----------|------|
| `docs/` | Human-readable architecture, module design, ops, ADRs, implementation tasks |
| `specs/` | Machine-readable contracts, schema, Layer 1 axes, Layer 3 chains |
| `backend/` | Python application (FastAPI, ETL, validators, layers, agents) |
| `frontend/` | React dashboard shell (UI not finalized — user must confirm before production UI) |
| `configs/` | Local runtime configuration (secrets stay in `.env`) |
| `data/` | Local DuckDB, raw files, parquet, audit (gitignored at runtime) |

Origin: implementation docs package v1.6 (`quant_monitor_implementation_docs_v1`) merged into this repo as the source of truth.

## 2. First reads (recommended order)

```text
1. README.md                          Project entry
2. MIGRATION_MAP.md                   This file
3. docs/INDEX.md                      Documentation index
4. docs/architecture/00_project_overview.md
5. docs/architecture/03_runtime_flows.md
6. docs/architecture/04_data_architecture.md
7. docs/architecture/05_module_map.md
8. docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md
9. docs/implementation_tasks/GLOBAL_TESTING_POLICY.md
10. docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md
11. docs/implementation_tasks/README.md
```

## 3. Five-layer model (quick reference)

| Layer | Name | Docs module | Spec / contract |
|-------|------|-------------|-----------------|
| L1 | Global Regime Panel | `docs/modules/layer1_global_regime_panel.md` | `specs/layer1_axes/restructured_axes_v1_1/` |
| L2 | Cross-Asset Sensor | `docs/modules/layer2_cross_asset_sensor.md` | `specs/contracts/layer2_sensor_contract.yaml` |
| L3 | Industry Chain Shock-Anchor | `docs/modules/layer3_industry_shock_anchor.md` | `specs/layer3_global_industry_chains/` |
| L4 | Market Structure | `docs/modules/layer4_market_structure.md` | `specs/contracts/layer4_market_contract.yaml` |
| L5 | Security Evidence | `docs/modules/layer5_security_evidence.md` | `specs/contracts/layer5_evidence_contract.yaml` |

Cross-cutting: `docs/modules/data_sync_orchestrator.md`, `write_manager.md`, `agent_module.md`.

## 4. Implementation task rounds

| Round | Directory | Focus |
|-------|-----------|-------|
| 0 | `docs/implementation_tasks/ROUND_0_PROJECT_SCAFFOLD/` | Scaffold, config, tests, doc index |
| 1 | `ROUND_1_DATA_FOUNDATION/` | Schema, ResourceGuard, WriteManager, raw store |
| 2 | `ROUND_2_DATA_INGESTION_VALIDATION/` | Adapters, sync, quality, conflict |
| 3 | `ROUND_3_MODELING_LAYERS/` | Layer 1–5 loaders and snapshots |
| 4 | `ROUND_4_API_FRONTEND_AGENT_BACKTEST/` | API, frontend, agent, reports |
| 5 | `ROUND_5_INTEGRATION_RELEASE/` | Integration tests, cleanup, release manifest |

Always read the four `GLOBAL_*.md` files before any task file.

## 5. Code ↔ docs mapping (planned)

| Code path | Primary doc |
|-----------|-------------|
| `backend/app/db/` | `docs/modules/duckdb_and_parquet.md` |
| `backend/app/validators/` | `docs/modules/data_validation_and_conflict.md` |
| `backend/app/datasources/` | `docs/modules/data_sources.md` |
| `backend/app/layer1_axes/` | `docs/modules/layer1_global_regime_panel.md` |
| `backend/app/layer2_sensors/` | `docs/modules/layer2_cross_asset_sensor.md` |
| `backend/app/layer3_chains/` | `docs/modules/layer3_industry_shock_anchor.md` |
| `backend/app/layer4_markets/` | `docs/modules/layer4_market_structure.md` |
| `backend/app/layer5_evidence/` | `docs/modules/layer5_security_evidence.md` |
| `backend/app/agents/` | `docs/modules/agent_module.md` |
| `backend/app/api/` | `docs/modules/fastapi_backend.md` |
| `frontend/src/` | `docs/modules/frontend_dashboard.md` |
| `specs/schema/schema.sql` | Round 1 task 005 |

## 6. Contracts index

All under `specs/contracts/`:

- `resource_limits.yaml` — ResourceGuard limits (mirrored in `configs/resource_limits.yaml`)
- `write_contract.yaml` — DuckDBWriteManager boundary
- `layer1_axis_contract.yaml` … `layer5_evidence_contract.yaml`
- `agent_contract.yaml` — read-only agent tools
- `runtime_flow_contract.yaml` — orchestration flows

OpenAPI: `specs/api/openapi_contract.md`

## 7. ADR index

See `docs/architecture/08_decision_log_index.md` and `docs/adr/ADR-*.md`.

## 8. Non-negotiable boundaries

- Default resource profile: **`eco`**
- Data sources: **Primary / Validation / FallbackPolicy** (not Shadow/Emergency)
- Layer 3: shock-anchor model, not a generic industry list
- Agent: read-only, no free SQL, no write DB, no trading action semantics
- Clean table writes: only via **DuckDBWriteManager**
- Frontend: placeholder until user confirms layout and visual design

## 9. Document lineage

```text
quant_monitor_design_document_v1_6.md
  → split into docs/architecture/, docs/modules/, specs/
  → implementation_tasks/ for AI round execution
  → merged into quant-monitor-desk/ (this repo)
```

When docs and code diverge, Round 5 task 034 (`docs_consistency_check`) is the reconciliation gate.
