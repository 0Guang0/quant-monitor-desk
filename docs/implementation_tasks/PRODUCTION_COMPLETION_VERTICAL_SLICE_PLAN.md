# Production Completion Vertical Slice Plan

> **Purpose:** provide a production-completion coverage map so missing work is visible across batches.  
> **Execution boundary:** this file is not a standalone execution task card and must not replace task-card-local reference-adoption details. Implementation agents must execute from the owning canonical task card.  
> **Style:** follows the local `to-issues` tracer-bullet format so each proposed slice can be copied into, or checked against, its owning task card.  
> **Scope:** covers reference-project adoption risk and all QMD modules that have meaningful implementation but are not yet `R6_FULL_PRODUCTION_STABLE`.  
> **Frontend note:** user-facing page/layout design is intentionally excluded because the user plans to design it separately. Frontend API contracts, no-action constraints, and readiness data shape remain in scope.

---

## 1. Directly executable plan definition

A production-completion implementation task is directly executable only from its owning canonical task card. A slice in this coverage map becomes executable only after the owning task card contains all of these fields:

1. **Reference source path** when a reference project is involved.
2. **Borrowable structure / logic** from the reference project.
3. **Dangerous capability to delete or forbid** before QMD use.
4. **QMD-owned target files** where the rewritten behavior must land.
5. **Tests / gates** proving the behavior.
6. **Not-done conditions** that prevent shell-only, registry-only, or sample-only closure.

A slice or task card that says only “refer to JQ2PTrade / EasyXT / OpenBB / agents-for-openbb” is not executable and is treated as from-scratch reinvention risk. This document can flag the gap, but the owning task card must carry the executable repair instructions.

---

## 2. Reference project adoption matrix

### 2.1 JQ2PTrade → Backtest / Review

**Reference paths to inspect:**

```text
参考项目/JQ2PTrade/api_mapping.json
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/api.py
参考项目/JQ2PTrade/ptrade_local/engine/context.py
参考项目/JQ2PTrade/ptrade_local/engine/backtester.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/ptrade_local/run_backtest.py
```

**Borrowable structure / logic:**

- `data_loader.py`
  - `DataBundle` shape: a deterministic bundle with available trading days and available instruments.
  - `load(start_date, end_date)` bounded-window entrypoint.
  - Read-only DuckDB connection pattern.
  - Pre-grouped symbol/date frames for fast local lookup.
  - `get_stock_history(...)` as a narrow historical lookup idea.
- `report.py`
  - Report generation separated from data loading and scenario execution.
  - Deterministic metric calculation from a structured value series.
  - Compact text/structured report shape.
- `backtester.py`
  - Daily loop shape can inspire QMD review replay: set current date, evaluate bounded inputs, append daily result.
  - Final report handoff after the loop.
  - Exception capture can inspire structured warnings, not console-only prints.
- `api_mapping.json` / `api.py`
  - Source for an explicit deny-list of action/execution API names.
  - Data read API naming can inform documentation only; do not expose PTrade compatibility as runtime.

**Dangerous capability to delete / forbid:**

- `backtester.py` executes arbitrary strategy code with `compile(..., 'exec')` and `exec(...)`. QMD must not copy this.
- `api.py` exposes order/action/account APIs: `order`, `order_value`, `order_target`, `order_target_value`, `cancel_order`, `get_open_orders`, `get_orders`, `get_trades`, `get_position`, `get_positions`, `set_yesterday_position`.
- `run_backtest.py` mutates `sys.path` and accepts arbitrary strategy file paths. QMD must not copy this runtime entry.
- `data_loader.py` hardcodes `D:/StockData/stock_data.ddb`, `stock_daily`, `period = '1d'`, `symbol_type IN ('stock', 'index')`, and `.SH -> .SS` mutation.
- Console `print(...)` reporting must be replaced by QMD report artifacts and evidence refs.
- Broad stock/index loading must be replaced by explicit source/evidence refs, row caps, symbol caps, and date-window caps.

**QMD-owned target files:**

```text
backend/app/review/__init__.py
backend/app/review/scenario_registry.py
backend/app/review/frozen_loader.py
backend/app/review/review_runner.py
backend/app/review/report_builder.py
backend/app/review/no_action_guard.py
backend/app/review/resource_budget.py
backend/app/api/routes/backtest_review.py
backend/app/api/schemas/backtest_review.py
specs/contracts/backtest_contract.yaml
specs/contracts/backtest_metric_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/review_sandbox_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_backtest_review.py
tests/test_backtest_reproducibility.py
tests/test_review_sandbox_contract.py
tests/test_no_action_semantics.py
tests/test_reference_adoption_guardrails.py
```

**Tests / gates:**

- One bounded `event_study` or `evidence_chain_review` scenario runs end-to-end from QMD evidence refs to report artifact.
- Forbidden API names from JQ2PTrade are rejected by contract tests and runtime guard.
- Arbitrary strategy file execution is impossible.
- Loader refuses broad universe / full history / no cap.
- Report contains `scenario_id`, input evidence refs, window, row/event counts, metrics, limitations, no-action flag, and resource budget.
- Reproducibility test proves same input evidence produces same report hash.

**Not done if:**

- Only `backend/app/review/__init__.py` or registry shell exists.
- The first scenario does not run.
- The runner executes user code, strategy files, or PTrade-compatible order APIs.
- The report lacks evidence refs or limitations.
- The slice only copies JQ2PTrade metric names without QMD evidence binding.

---

### 2.2 EasyXT → Backtest / Review metrics and data health

**Reference paths to inspect:**

```text
参考项目/EasyXT/easyxt_backtest/performance.py
参考项目/EasyXT/easyxt_backtest/portfolio_daily_result.py
参考项目/EasyXT/easyxt_backtest/core/backtest_core.py
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
参考项目/EasyXT/easy_xt/realtime_data/providers/tdx_provider.py
```

**Borrowable structure / logic:**

- `performance.py`
  - Metrics grouped by return, risk, and risk-adjusted return.
  - Empty-input metrics return stable zero/empty values.
  - Calculations for total return, annual return, max drawdown, volatility, Sharpe, Calmar, win-rate, and profit/loss ratio.
- `portfolio_daily_result.py`
  - Daily result rows with close price, previous close, trade count, turnover, commission, holding PnL, trading PnL, total PnL, net PnL, and balance.
  - Daily result manager producing a deterministic dataframe and summary statistics.
- `data_integrity_checker.py` / `smart_data_detector.py`
  - Missing trading-day profile.
  - Required-field/null checks.
  - OHLC relation checks.
  - Extreme return / volume anomaly warning shape.
  - Summary counts and first-N issue detail reporting.
- `tdx_provider.py`
  - Provider lifecycle shape: connect, test connection, fetch bounded quote/list, close, classify failures.

**Dangerous capability to delete / forbid:**

- `backtest_core.py` imports and instantiates Backtrader/Cerebro. QMD Round4 first review slice must not introduce an execution engine dependency.
- Trading / position / commission semantics from EasyXT are not allowed in QMD no-action review unless explicitly narrowed as non-action historical metrics.
- Any automatic login, account control, terminal control, or trading integration from EasyXT/TDX must be excluded.
- Hardcoded DB/table/calendar assumptions must be removed.
- Data health must not use EasyXT tables or SQL; it must consume QMD raw/staged/evidence bundles.

**QMD-owned target files:**

```text
backend/app/ops/data_health_profiles/ohlcv_rules.py
backend/app/ops/data_health_profiles/calendar_gap_rules.py
backend/app/ops/data_health_profiles/report_builder.py
backend/app/ops/data_health.py
backend/app/cli/data_commands.py
backend/app/cli/main.py
backend/app/review/metrics.py
backend/app/review/report_builder.py
backend/app/datasources/fetch_ports/tdx_pytdx_port.py
backend/app/datasources/fetch_ports/mootdx_port.py
backend/app/datasources/normalizers/cn_market.py
specs/contracts/data_quality_rules.yaml
specs/contracts/backtest_metric_contract.yaml
specs/contracts/source_route_contract.yaml
tests/test_data_health_easyxt_ohlcv_rules.py
tests/test_qmd_data_health_cli_runtime.py
tests/test_backtest_review_metrics.py
tests/test_tdx_provider_port.py
```

**Tests / gates:**

- `qmd data health` calls the real data-health service, not `not_implemented_phase_c`.
- OHLC, required-field, missing-calendar, stale data, extreme-return, and volume anomaly tests pass on bounded evidence.
- TDX-like ports remain disabled/raw-only unless user authorization exists.
- Backtest/review metrics are computed only from QMD review result series, not from copied EasyXT execution engine state.
- No Backtrader/Cerebro runtime dependency is introduced for the first read-only review slice.

**Not done if:**

- CLI health remains placeholder.
- Data health has only generic `PASS`/`FAIL` with no profile-specific issue details.
- Backtest metrics exist but are not connected to a runnable read-only QMD review scenario.
- TDX provider lifecycle is copied with auto-login, account control, full-market scan, or silent fallback.

---

### 2.3 OpenBB → Provider catalog and provider metadata

**Reference paths to inspect:**

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
参考项目/OpenBB/desktop/src/components/
参考项目/OpenBB/desktop/src/routes/
```

**Borrowable structure / logic:**

- Provider-per-package/catalog organization.
- Provider README shape: external provider, installation/auth note, docs link, supported domains.
- Provider-specific metadata separated from runtime fetcher.
- Optional provider/extras concept as architecture only.
- Desktop route/component organization may inform non-final frontend integration contracts, but not user-facing layout design.

**Dangerous capability to delete / forbid:**

- No OpenBB AGPL runtime source copy.
- No copied provider fetcher classes.
- No `openbb` runtime dependency in QMD provider ports.
- No OpenBB UI source wholesale copy.
- No broad provider search/fetch behavior bypassing QMD SourceRoutePlan.

**QMD-owned target files:**

```text
specs/datasource_registry/provider_catalog.yaml
backend/app/datasources/provider_catalog.py
backend/app/datasources/auth/license_gate.py
backend/app/datasources/fetch_ports/**
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
tests/test_provider_catalog.py
tests/test_reference_adoption_guardrails.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
```

**Tests / gates:**

- Provider catalog covers every source in `source_registry.yaml` and `source_capabilities.yaml`.
- Each provider has owner, license/terms note, auth mode, enabled-by-default posture, allowed domains, resource caps, and evidence posture.
- AGPL/source-copy guard stays green.
- Route planner never treats catalog metadata as adapter readiness.

**Not done if:**

- Catalog exists but omits proposed/disabled sources.
- Catalog marks a source production-ready without R3H evidence.
- OpenBB fetcher/runtime code appears under QMD backend.

---

### 2.4 agents-for-openbb / TradingAgents / TradingAgents-astock → Agent artifacts and evidence summaries

**Reference paths to inspect:**

```text
参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
参考项目/agents-for-openbb/31-vanilla-agent-reasoning-steps/
参考项目/agents-for-openbb/32-vanilla-agent-raw-widget-data-citations/
参考项目/agents-for-openbb/34-vanilla-agent-tables/vanilla_agent_tables/main.py
参考项目/agents-for-openbb/39-vanilla-agent-html-artifacts/vanilla_agent_html/main.py
参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py
参考项目/TradingAgents/
参考项目/TradingAgents-astock/
```

**Borrowable structure / logic:**

- Artifact shape: facts table, citation/evidence list, reasoning steps, limitations, bounded context.
- Explicit context retrieval: only use supplied tool context or QMD service output.
- Latest-context-only or capped-context pattern to avoid unbounded prompt expansion.
- Dashboard/widget output shape for internal artifact contracts only.

**Dangerous capability to delete / forbid:**

- No OpenAI/client/model invocation loop copied into QMD Agent runtime.
- No external agent orchestrator dependency.
- No free web fetch, free SQL, or arbitrary DB reads from Agent.
- No Agent-triggered source fetch or clean write.
- No Agent output as factual source.
- No buy/sell/add/reduce/position/order language.
- User-facing page/display design is out of scope for this plan.

**QMD-owned target files:**

```text
backend/app/agents/tool_registry.py
backend/app/agents/execution_policy.py
backend/app/agents/tools/source_readiness.py
backend/app/agents/tools/evidence_context.py
backend/app/agents/output_contract.py
backend/app/api/routes/agent_tools.py
backend/app/api/schemas/agent_tools.py
specs/contracts/agent_contract.yaml
specs/contracts/user_input_privacy_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_agent_contract.py
tests/test_agent_policy.py
tests/test_agent_tools_source_readiness.py
tests/test_no_action_semantics.py
```

**Tests / gates:**

- First Agent tool returns evidence-bound source/readiness summary from QMD service/API, not direct DB/YAML/free web.
- Prompt injection cannot call forbidden tools.
- Output validator rejects action semantics.
- Tool output includes facts used, evidence refs or missing evidence, limitations, and contract refs.
- No runtime import from `参考项目/**`.

**Not done if:**

- Only policy classes or empty package shell exist.
- Agent can query arbitrary SQL, web, or DB tables.
- Agent output contains trade/action instructions.
- Agent summarizes unverified text without evidence refs.

---

## 3. Production-incomplete module inventory

The following modules have meaningful implementation but are not yet full production-stable. Each must either reach `R6_FULL_PRODUCTION_STABLE` for its declared scope or be explicitly narrowed by ADR/release limitation.

| Module                                         | Current evidence observed                                        | Current production gap                                                                            | Required closure phase              |
| ---------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------- |
| Project scaffold/config/test harness           | scaffold, pytest catalog, config templates                       | not release-packaged as a stable operator distribution                                            | Batch05 release/security packaging  |
| DuckDB schema/migration foundation             | migrations and schema tests exist                                | release migration hygiene and final schema drift gate still needed                                | Batch05 / DB release gate           |
| WriteManager + DbValidationGate                | write/validation infrastructure exists                           | needs sandbox and limited production clean-write proof                                            | R3G-01 to R3G-03                    |
| RawStore/FileRegistry/fetch_log                | evidence primitives exist                                        | every in-scope source must bind real fetch evidence                                               | R3H-01 to R3H-05                    |
| ResourceGuard / perf budget                    | guard and tests exist                                            | not yet enforced across every real adapter/API/review path                                        | R3H + Batch04 + Batch05 smoke       |
| Source registry/capability/route planner       | route and capability tests exist                                 | many sources are disabled/proposed without adapter/evidence                                       | R3H all source cards                |
| Provider catalog/license gate                  | planning/guardrail exists                                        | provider catalog must cover every source with auth/license/resource posture                       | R3FR-05 + R3H                       |
| DataSourceService / sync facade                | production fetch facade exists                                   | real production fetch requires injected source-specific ports and FileRegistry; many ports absent | R3H + sync smoke                    |
| Vendor adapters/provider fetch ports           | skeleton adapters for only a subset                              | most target sources lack real fetch port/auth/replay/evidence                                     | R3H-01 to R3H-04                    |
| Source conflict validator                      | pure conflict validator exists                                   | must be wired to each ready source/domain before write/readiness claims                           | R3H + R3G                           |
| Data quality validator / data health           | read-only service exists; CLI path split                         | `qmd data health` packaged command still placeholder; EasyXT-style profiles incomplete            | R3FR-02 + R3FR-06                   |
| `qmd data` CLI                                 | route-preview/sync-plan/init-basic exist                         | health and limited production write operator flows incomplete                                     | R3FR-06 + R3G                       |
| Sync orchestration                             | incremental/backfill/reconcile runners exist; full-load deferred | production-equivalent source/service integration and release smoke incomplete                     | R3G/R3H + Batch05                   |
| Layer1 axes                                    | staged macro/evidence ingestion exists                           | real official/macro source binding missing for production-entry scope                             | R3H-01 + R3H-05                     |
| Layer2 sensors                                 | staged fixture sensors/snapshots exist                           | real cross-asset source binding and source conflict evidence missing                              | R3H-02/03 + R3H-05                  |
| Layer3 chains                                  | staged industry-chain bundle exists                              | real CN/industry-chain source evidence missing                                                    | R3H-03 + R3H-05                     |
| Layer4 markets                                 | CN_A staged market structure fixture exists                      | real market/calendar/breadth sources and ResourceGuard caps missing                               | R3H-02/03 + R3H-05                  |
| Layer5 evidence                                | staged evidence-chain pieces exist                               | real source_fetch_id/content_hash/schema_hash binding for declared scope incomplete               | R3H-05                              |
| Sandbox clean write / limited production entry | planning and tests exist                                         | must execute rehearsal/audit/limited write gate                                                   | R3G-01 to R3G-03                    |
| API backend                                    | FastAPI placeholder with `/health` only                          | no real read-only readiness/source API yet                                                        | Batch04 B04_01                      |
| Agent layer                                    | package shell only                                               | no enforceable runtime policy/tool                                                                | Batch04 B04_02                      |
| Frontend dashboard                             | not covered here for user-facing design                          | API-bound data shape still needed; layout is user-owned                                           | Batch04 B04_01/B04_03 contract only |
| Notifications/reports                          | package shell/planning only                                      | no event-to-report runtime                                                                        | Batch04 B04_04                      |
| Backtest/review                                | planning only                                                    | no QMD-owned read-only review scenario/report                                                     | Batch04 B04_05                      |
| Release/security packaging                     | planning only                                                    | no final release manifest/security/integration gate                                               | Batch05                             |

---

## 4. Tracer-bullet vertical slices

### Slice 0 — Reference adoption gate closure

**Blocked by:** None - can start immediately.

**User stories covered:** As an implementer, I can reuse mature reference-project ideas without copying unsafe runtime code or starting from a blank design.

**What to build:** Close the reference-adoption guardrail so every card that touches JQ2PTrade, EasyXT, OpenBB, agents-for-openbb, TradingAgents, or TradingAgents-astock contains local executable adaptation details.

**Acceptance criteria:**

- [ ] Each adapting task card names exact reference paths.
- [ ] Each card lists borrowable logic, forbidden semantics, QMD target files, tests, and not-done conditions.
- [ ] AGPL/OpenBB runtime copy is forbidden and tested.
- [ ] Trading/order/auto-login/scheduler/runtime-import guards stay green.
- [ ] No central reference inventory becomes an executable dependency.

---

### Slice 1 — EasyXT-style data health profiles and packaged `qmd data health`

**Blocked by:** Slice 0.

**User stories covered:** As an operator, I can run one packaged data-health command and see actionable evidence-quality findings before any clean write or readiness claim.

**What to build:** Convert the existing split data-health implementation into a QMD-owned packaged CLI path with EasyXT-inspired profile rules for OHLCV, required fields, stale/freshness, calendar gaps, outliers, and volume anomalies.

**Acceptance criteria:**

- [ ] `qmd data health` no longer returns `not_implemented_phase_c`.
- [ ] The packaged CLI calls `DataHealthService` or a successor service boundary.
- [ ] Profiles produce structured checks with source/domain/evidence path/row count/message.
- [ ] Output supports JSON and text.
- [ ] No production DB mutation or source fetch happens during health checks.
- [ ] Tests cover pass, warn, fail, blocked, missing evidence, stale data, OHLC relation violation, and unknown profile.

---

### Slice 2 — Provider catalog + license/auth posture for every registry source

**Blocked by:** Slice 0.

**User stories covered:** As an operator, I can see which external sources exist, what they require, and whether they are usable without confusing registry presence with adapter readiness.

**What to build:** Implement an OpenBB-inspired but QMD-owned provider catalog covering every source in `source_registry.yaml` and `source_capabilities.yaml`, including auth/license/resource posture and R3H final decision fields.

**Acceptance criteria:**

- [ ] Every source has provider metadata, allowed domains, auth mode, license/terms note, enabled-by-default posture, resource caps, and evidence posture.
- [ ] Catalog loader validates source IDs against registry/capabilities.
- [ ] Route planner and API do not treat catalog presence as `READY_WITH_EVIDENCE`.
- [ ] OpenBB runtime import/copy tests stay green.
- [ ] Missing provider metadata blocks R3H audit closure.

---

### Slice 3 — Official macro/disclosure adapters to R3H final decision

**Blocked by:** Slices 1 and 2.

**User stories covered:** As a macro/disclosure user, I can consume official low-frequency data only when adapter, license, route, evidence, health, and layer binding are complete.

**What to build:** Complete `fred`, `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, and `world_bank` to either `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

**Acceptance criteria:**

- [ ] Each source has a source-specific fetch port or explicit ADR-disabled boundary.
- [ ] Auth/license/rate-limit posture is documented and tested.
- [ ] ResourceGuard caps bound series, filings, rows, and window.
- [ ] Replay fixture or sandbox sample exists.
- [ ] Fetch results include fetch_log, content_hash, schema_hash, and source_fetch_id.
- [ ] Data health/freshness and source conflict rules are applied where relevant.
- [ ] Layer1/Layer5 binding is declared and audited.

---

### Slice 4 — Market/crypto adapters to R3H final decision

**Blocked by:** Slices 1 and 2.

**User stories covered:** As a market-data consumer, I can use market/crypto sources only within explicit caps and without aggregator silent-primary behavior.

**What to build:** Complete `alpha_vantage`, `stooq`, `yahoo_finance`, `deribit`, and `coingecko` to final R3H decisions with route/evidence/health/layer binding.

**Acceptance criteria:**

- [ ] Each source has a bounded fetch port or ADR-disabled status.
- [ ] Option-chain and crypto derivatives paths have strict breadth/window/row caps.
- [ ] Aggregators cannot silently become primary.
- [ ] Replay/sandbox evidence exists with schema/content hashes.
- [ ] Layer2/Layer4/Layer5 binding is audited for declared scope.

---

### Slice 5 — CN market adapters to R3H final decision

**Blocked by:** Slices 1 and 2.

**User stories covered:** As a CN market user, I can distinguish primary, validation-only, and authorization-disabled CN sources without hidden fallback or unbounded scans.

**What to build:** Complete `baostock`, `akshare`, `cninfo`, `tdx_pytdx`, `mootdx`, `eastmoney`, `sina_finance`, `ths_ifind`, `qmt_xtdata`, and `qmt_xqshare` to final R3H decisions.

**Acceptance criteria:**

- [ ] Each source has fetch port, validation-only boundary, authorization-disabled boundary, or ADR-disabled status.
- [ ] QMT/iFinD/xqshare remain disabled unless explicit user environment/license proof exists.
- [ ] No source performs full-market/full-history/minute default scan.
- [ ] TDX/mootdx do not silently replace another source.
- [ ] Source conflict checks prove validation/fallback posture.
- [ ] Layer3/Layer4/Layer5 binding is audited.

---

### Slice 6 — Prediction-market and web evidence adapters

**Blocked by:** Slices 1 and 2.

**User stories covered:** As an evidence reviewer, I can use prediction/web sources as probability or manual-review evidence without polluting factual clean tables.

**What to build:** Complete `kalshi`, `polymarket`, and `web_search` as evidence/probability/manual-review paths or ADR-disabled statuses.

**Acceptance criteria:**

- [ ] No prediction/web source writes clean factual tables.
- [ ] Prediction market prices are probability signals only, not factual resolution truth.
- [ ] Web search remains manual-review/evidence staging only.
- [ ] Query/market/event/row/window caps are enforced.
- [ ] Layer5/manual-review binding is audited.

---

### Slice 7 — Sandbox clean-write rehearsal and limited production entry

**Blocked by:** Slices 1 and source-specific R3H evidence for candidate sources.

**User stories covered:** As an operator, I can prove clean-write safety in sandbox before any limited production write.

**What to build:** Execute the R3G sequence: sandbox rehearsal, adversarial audit, and limited production clean write only if PASS/WARN allows it.

**Acceptance criteria:**

- [ ] Sandbox rehearsal writes only to sandbox and produces before/after/rollback proof.
- [ ] Data health, source conflict, WriteManager, DbValidationGate, ResourceGuard, and Layer5 evidence are all present.
- [ ] Limited production write requires explicit operator approval with source/domain/symbol/window/row cap.
- [ ] Any failure produces no-mutation or rollback evidence.

---

### Slice 8 — Layer1 real official/macro binding

**Blocked by:** Slice 3.

**User stories covered:** As a research user, I can trust Layer1 macro axes because their observations point to real official source evidence or a narrowed ADR.

**What to build:** Replace staged-only Layer1 source assumptions with R3H-approved official/macro source evidence for declared axes.

**Acceptance criteria:**

- [ ] Layer1 no longer defaults to staged fixture for production-entry scope.
- [ ] Every declared production axis has source_fetch_id/content_hash/schema_hash lineage or ADR-disabled/narrowed scope.
- [ ] Observation writer records real source/evidence lineage.
- [ ] Tests fail if staged fixture is claimed as production-ready.

---

### Slice 9 — Layer2 real cross-asset sensor binding

**Blocked by:** Slices 4 and 5.

**User stories covered:** As a risk user, I can trust Layer2 cross-asset sensors because they come from R3H-approved source evidence, not staged-only fixtures.

**What to build:** Bind Layer2 sensors to real approved market/CN source envelopes for the declared scope.

**Acceptance criteria:**

- [ ] Staged fixture loader remains available only for tests/rehearsal.
- [ ] Real Layer2 sensor inputs cite source_fetch_id/content_hash/schema_hash.
- [ ] ResourceGuard applies to sensor windows and row counts.
- [ ] Source conflict / validation-only posture is visible in sensor reports.

---

### Slice 10 — Layer3 real industry-chain binding

**Blocked by:** Slice 5.

**User stories covered:** As an industry-chain user, I can tell which chain signals are backed by real CN evidence and which remain out of scope.

**What to build:** Move Layer3 chain snapshots from staged bundle only to R3H-approved CN source/evidence paths or ADR-narrowed chain scope.

**Acceptance criteria:**

- [ ] Production-entry chain rows cannot use staged bundle IDs as primary evidence.
- [ ] Chain anchors and bar/event evidence carry source_fetch_id/content_hash/schema_hash.
- [ ] ResourceGuard caps chain breadth and input row counts.
- [ ] Deterministic rebuild tests cover full row tuples.

---

### Slice 11 — Layer4 real market-structure binding

**Blocked by:** Slices 4 and 5.

**User stories covered:** As a market-structure user, I can trust market/calendar/breadth rows because their source posture is explicit.

**What to build:** Bind Layer4 market registry/calendar/breadth data to real R3H-approved market/CN sources or ADR-disabled scope.

**Acceptance criteria:**

- [ ] CN_A staged fixture is not production-entry evidence.
- [ ] Calendar/breadth inputs cite source_fetch_id/content_hash/schema_hash.
- [ ] ResourceGuard caps market count, date window, and rows.
- [ ] Unsupported markets return explicit disabled/out-of-scope status.

---

### Slice 12 — Layer5 evidence-chain production binding

**Blocked by:** Slices 3 to 6.

**User stories covered:** As an auditor, I can trace every production-entry insight to immutable source evidence.

**What to build:** Close Layer5 binding so declared production-entry scope has real source_fetch_id/content_hash/schema_hash lineage and release-ready evidence posture.

**Acceptance criteria:**

- [ ] Every production-entry Layer1–4 artifact links to Layer5 source evidence.
- [ ] Staged bundle fallback cannot be reported as production-ready.
- [ ] Missing evidence creates `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` or release limitation.
- [ ] R3H-05 audit template is fully populated with final decisions.

---

### Slice 13 — API source/readiness runtime

**Blocked by:** R3H-05 PASS or WARN.

**User stories covered:** As a product user or Agent tool, I can query source/capability/readiness through a real read-only API instead of reading files directly.

**What to build:** Replace the FastAPI placeholder shell with one authenticated read-only source/readiness endpoint backed by QMD service contracts and R3H final decisions.

**Acceptance criteria:**

- [ ] Endpoint returns only R3H-closed source posture: `READY_WITH_EVIDENCE`, `ADR_DISABLED_OUT_OF_SCOPE`, or `DISABLED_SOURCE` limitation entries.
- [ ] Endpoint exposes route/evidence status, limitation, auth/license posture, and source caps.
- [ ] No write/fetch trigger is exposed.
- [ ] Auth/security/error-redaction contract tests pass.

---

### Slice 14 — Agent read-only evidence-bound tool

**Blocked by:** Slice 13.

**User stories covered:** As a user, I can ask the Agent for source/readiness or evidence summaries without it inventing facts or taking actions.

**What to build:** Implement one policy-guarded read-only Agent tool using the API/service boundary and agents-for-openbb-inspired artifact shape.

**Acceptance criteria:**

- [ ] Tool registry rejects unknown/forbidden tools.
- [ ] Tool output includes facts used, evidence refs or missing evidence, limitations, and contract refs.
- [ ] Prompt injection cannot bypass policy.
- [ ] No free SQL, free web, direct DB write, source fetch, or trading-action output.

---

### Slice 15 — Notification/report runtime

**Blocked by:** Slice 13.

**User stories covered:** As an operator, I can receive a bounded report artifact for a real event/readiness change without relying on schema-only placeholders.

**What to build:** Implement one event-to-report/notification_log flow with dedup/cooldown, evidence refs, and limitations.

**Acceptance criteria:**

- [ ] One real event type produces a report artifact and notification log entry.
- [ ] Report references source/readiness/evidence state from API/service contracts.
- [ ] Dedup/cooldown prevents repeated spam.
- [ ] No Agent/UI direct DB write or trading action language.

---

### Slice 16 — Backtest/review read-only vertical slice

**Blocked by:** Slices 0, 12, and 13.

**User stories covered:** As a researcher, I can run one bounded read-only review scenario that produces a reproducible report without strategy execution or action semantics.

**What to build:** Implement the QMD-owned review runtime described in §2.1 and §2.2.

**Acceptance criteria:**

- [ ] One scenario runs from QMD evidence refs through frozen loader, runner, metrics, no-action guard, and report artifact.
- [ ] Unsupported scenario types return `DEFERRED_BACKTEST_TYPE`.
- [ ] Forbidden JQ2PTrade APIs and action terms fail closed.
- [ ] Reproducibility and no-lookahead tests pass.
- [ ] No copied EasyXT/JQ2PTrade runtime source.

---

### Slice 17 — Sync orchestration production-equivalent smoke

**Blocked by:** Slices 3 to 7.

**User stories covered:** As an operator, I can prove DataSyncOrchestrator works with real DataSourceService paths under resource and write gates.

**What to build:** Add a bounded integration smoke that exercises incremental/backfill/reconcile/data-quality paths with R3H-approved sources or explicit disabled outcomes.

**Acceptance criteria:**

- [ ] Incremental and backfill smoke use DataSourceService, not adapter bypass, except where tests explicitly assert bypass is rejected.
- [ ] Full-load remains deferred and fail-closed.
- [ ] ResourceGuard pause/hard-stop paths are tested.
- [ ] WriteManager/DbValidationGate output is visible in job events.

---

### Slice 18 — Release/security manifest gate

**Blocked by:** Slices 7, 12, 13, 14, 15, 16, and 17.

**User stories covered:** As a release owner, I can decide whether QMD is shippable based on exact source/module posture rather than optimistic claims.

**What to build:** Finalize Batch05 release manifest, security CI, integration/resource smoke, docs index, package cleanup, and production limitation carry-forward.

**Acceptance criteria:**

- [ ] Release manifest includes R3H source decisions, source limitations, route/evidence status, and module rating deltas.
- [ ] Missing R3H/R3G/Batch04 capabilities block release or are explicitly listed as limitations.
- [ ] Security/dependency/secret scan gates run.
- [ ] Integration/resource smoke proves bounded behavior.
- [ ] No release output upgrades a disabled/out-of-scope source to production-ready.

---

## 5. Completion rule

A module can be moved to `R6_FULL_PRODUCTION_STABLE` only when its vertical slice has:

- an executable runtime path for the declared scope;
- contract and regression tests;
- source/evidence/lineage binding where data is involved;
- ResourceGuard and security posture where external systems or APIs are involved;
- release/runbook/manifest representation;
- no open blocker contradicting the claimed scope.

If a module cannot meet that bar, the correct closure is a narrowed ADR plus release limitation, not a production-ready claim.
