# B04_05 — Backtest and Review Runtime

> **Batch:** Batch 04 — Verified Audit Productization  
> **Owns:** `VR-BT-001`, loose historical card `029_implement_backtest_and_review.md`, 3F-R card `R3FR-04`  
> **Roadmap:** Round 4.5 track + mature reference-adoption rule.  
> **Execution posture:** read-only review/backtest vertical slice; no strategy execution, no order API, no live-readiness claim.

---

## 1. Business purpose

Move backtest/review from docs/schema-only capability to the first executable read-only review vertical slice: one bounded scenario, one loader path, one report artifact, ResourceGuard enforcement, and no-action semantics.

This task is not complete if it only adds registry/contract scaffolding.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
specs/contracts/backtest_contract.yaml
specs/contracts/backtest_metric_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/review_sandbox_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/snapshot_lineage_contract.yaml
specs/contracts/resource_limits.yaml
docs/modules/backtest_and_review.md
docs/modules/layer5_security_evidence.md
docs/modules/data_validation_and_conflict.md
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md (coverage map only; B04_05 remains the execution card)
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md
```

---

## 3. Reference project source to inspect

Read these files under `参考项目/**` before implementation:

```text
参考项目/JQ2PTrade/api_mapping.json
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/api.py
参考项目/JQ2PTrade/ptrade_local/engine/context.py
参考项目/JQ2PTrade/ptrade_local/engine/backtester.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/ptrade_local/run_backtest.py
参考项目/EasyXT/easyxt_backtest/performance.py
参考项目/EasyXT/easyxt_backtest/portfolio_daily_result.py
参考项目/EasyXT/easyxt_backtest/core/backtest_core.py
```

Useful ideas to adapt into QMD-owned code, based on source audit:

- From JQ2PTrade `data_loader.py`:
  - `DataBundle` idea for deterministic in-memory data bundle;
  - `load(start_date, end_date)` bounded-window shape;
  - read-only DuckDB connection;
  - pre-grouped symbol/date data frame for fast lookup;
  - `get_stock_history(...)` as a narrow lookup shape, not a broad scan.
- From JQ2PTrade `backtester.py`:
  - daily replay loop shape: set current date, evaluate bounded inputs, append one daily result;
  - final report handoff after loop;
  - structured warning capture idea, but not console-only `print(...)`.
- From JQ2PTrade `report.py`:
  - reporting separated from loader/runtime;
  - compact deterministic metric/report text from structured series.
- From JQ2PTrade `api.py` and `api_mapping.json`:
  - forbidden API name source for QMD no-action guard;
  - read-style naming can inform documentation only; do not expose PTrade compatibility runtime.
- From EasyXT `performance.py`:
  - return/risk/risk-adjusted metric grouping;
  - deterministic empty-input metrics;
  - total return, annual return, max drawdown, volatility, Sharpe, Calmar, win-rate, and profit/loss ratio formulas when computed from QMD-owned result series.
- From EasyXT `portfolio_daily_result.py`:
  - daily result dataframe shape: date, turnover, commission, PnL fields, balance, drawdown, summary statistics;
  - use only for non-action historical review output, not account simulation.
- From EasyXT `core/backtest_core.py`:
  - analyzer/result extraction boundary as an architectural idea only.

Must rewrite or exclude:

- hardcoded DuckDB paths such as `D:/StockData/stock_data.ddb`;
- hardcoded table/domain assumptions such as `stock_daily`, `period='1d'`, and `symbol_type IN ('stock', 'index')`;
- broad full-universe stock/index scans;
- `.SH` → `.SS` mutation that loses raw source identity;
- JQ2PTrade `compile(..., 'exec')` / `exec(...)` arbitrary strategy execution;
- JQ2PTrade `run_backtest.py` `sys.path` mutation and arbitrary strategy file entrypoint;
- EasyXT Backtrader/Cerebro execution engine dependency in the first QMD read-only review slice;
- trading limits/order/commission/win-rate/portfolio action metrics unless represented as non-action historical review metrics with limitations;
- any order, broker, account, position, or scheduler API names.

Forbidden API names include:

```text
order
order_value
order_target
order_target_value
cancel_order
get_open_orders
get_portfolio
get_positions
get_orders
get_trades
run_daily
run_weekly
run_monthly
```

---

## 4. Target QMD files

Create/update QMD-owned files only:

```text
backend/app/review/__init__.py
backend/app/review/scenario_registry.py
backend/app/review/frozen_loader.py
backend/app/review/review_runner.py
backend/app/review/report_builder.py
backend/app/review/no_action_guard.py
backend/app/review/resource_budget.py
backend/app/review/metrics.py
backend/app/api/routes/backtest_review.py
backend/app/api/schemas/backtest_review.py
specs/contracts/backtest_contract.yaml
specs/contracts/backtest_metric_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/review_sandbox_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_backtest_review.py
tests/test_backtest_reproducibility.py
tests/test_no_action_semantics.py
tests/test_review_sandbox_contract.py
tests/test_backtest_review_metrics.py
tests/test_catalog.yaml
```

If final names differ, the PR must document the mapping.

---

## 5. Implementation plan as vertical slices

These are issue-style tracer bullets. Each completed slice must be independently testable.

### Slice B04_05-A — Frozen loader

**Blocked by:** R3H source/evidence closure for at least one supported scenario input.

**What to build:** QMD-owned bounded loader inspired by JQ2PTrade `DataBundle`, reading only explicit QMD evidence refs and preserving raw source identity.

**Acceptance criteria:**

- Inputs include `scenario_id`, evidence refs, symbols/series, `start_date`, `end_date`, `max_rows`, and `max_events`.
- Loader uses QMD evidence/frozen datasets and ResourceGuard; no broad scans.
- Raw source IDs and source_fetch_id/content_hash/schema_hash are preserved.
- Tests reject broad universe, full history, missing caps, missing evidence refs, and `.SH -> .SS` style identity mutation.

### Slice B04_05-B — No-action guard

**Blocked by:** Slice B04_05-A can run on bounded evidence.

**What to build:** Runtime and test deny-list using JQ2PTrade `api.py` / `api_mapping.json` action names.

**Acceptance criteria:**

- Forbidden API names and output action terms fail closed.
- No PTrade compatibility namespace is exposed.
- No broker/account/order/position API can be called.
- Tests cover order/action/scheduler names plus user-output action terms.

### Slice B04_05-C — First read-only review runner

**Blocked by:** Slices B04_05-A and B04_05-B.

**What to build:** One supported scenario, preferably `event_study` or `evidence_chain_review`, using a daily replay loop shape without strategy execution.

**Acceptance criteria:**

- No user strategy file, `compile`, `exec`, Backtrader/Cerebro, or copied runtime source.
- No-lookahead and window boundaries are enforced.
- Unsupported scenario types return `DEFERRED_BACKTEST_TYPE`.
- ResourceGuard rejects over-budget runs.

### Slice B04_05-D — Report artifact and metrics

**Blocked by:** Slice B04_05-C.

**What to build:** Deterministic report builder using QMD result series and EasyXT-style metric grouping.

**Acceptance criteria:**

- Report includes `scenario_id`, `scenario_type`, `input_evidence_ids`, window, row/event counts, metrics, limitations, `no_action_semantics: true`, resource budget, and report hash.
- Metrics are computed from QMD-owned review series only.
- Same input evidence produces the same report hash.
- Report never claims live trading readiness.

### Slice B04_05-E — Read-only API binding

**Blocked by:** B04_01 source/readiness API and Slice B04_05-D.

**What to build:** Read-only HTTP route/schema for the first review scenario.

**Acceptance criteria:**

- Route requires API auth and error redaction.
- Route cannot trigger write/fetch outside the approved bounded review runner.
- Tests cover success, deferred scenario type, forbidden action, over-budget, missing evidence, and auth failure.

---

## 6. Forbidden scope

- No execution instructions.
- No broker/account/order/portfolio action API.
- No arbitrary user strategy runtime.
- No broad historical scan.
- No direct DB write outside approved report/run-log writer.
- No runtime import from `参考项目/**`.
- No copied EasyXT/JQ2PTrade source files.
- No simulation output claiming live readiness.

---

## 7. Tests / gates

Required commands:

```bash
uv sync --locked
uv run pytest tests/test_backtest_review.py tests/test_backtest_reproducibility.py tests/test_no_action_semantics.py tests/test_review_sandbox_contract.py tests/test_backtest_review_metrics.py -q
uv run ruff check backend/app/review backend/app/api tests
```

Test expectations:

- one supported review scenario runs end-to-end against bounded fixture/frozen evidence;
- unsupported types return `DEFERRED_BACKTEST_TYPE`;
- no-lookahead and window-boundary violations fail;
- ResourceGuard rejects over-budget scans;
- forbidden JQ2PTrade API names are rejected;
- EasyXT-style metrics are computed only from QMD-owned review series;
- report artifact includes evidence refs, limitations, deterministic hash, and no-action semantics;
- no runtime import from `参考项目/**`.

---

## 8. Done criteria

B04_05 is done only when at least one backtest/review type has QMD-owned runtime, tests, and a report artifact. Blank-engine design, registry-only scaffolding, metric-only micro-slices, copied reference runtime, or arbitrary strategy execution are not acceptable.
