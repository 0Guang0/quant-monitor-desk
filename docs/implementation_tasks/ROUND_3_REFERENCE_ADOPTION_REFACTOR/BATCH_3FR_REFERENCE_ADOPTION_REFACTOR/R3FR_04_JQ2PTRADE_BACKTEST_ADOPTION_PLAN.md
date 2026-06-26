# R3FR-04 — Round4 Backtest/Review Adoption Rewrite

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Round4 backtest/review planning must move from blank-engine risk to a reference-adapted first vertical slice plan.  
> **Execution posture:** planning/task rewrite only in 3F-R; no backend backtest runtime unless explicitly authorized.

---

## 1. Purpose

Rewrite Round4 backtest/review task cards so the first implementation batch delivers a working read-only review/backtest vertical slice, and the full stable shape is reached within at most three implementation batches. Do not allow “add one metric per task” micro-slicing.

This card is closed only if the Round4 task card contains directly executable adaptation detail. A sentence such as “refer to JQ2PTrade / EasyXT” is not enough and is treated as from-scratch reinvention risk.

```yaml
reference_project:
  path:
    - 参考项目/JQ2PTrade/api_mapping.json
    - 参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
    - 参考项目/JQ2PTrade/ptrade_local/engine/api.py
    - 参考项目/JQ2PTrade/ptrade_local/engine/context.py
    - 参考项目/JQ2PTrade/ptrade_local/engine/backtester.py
    - 参考项目/JQ2PTrade/ptrade_local/engine/report.py
    - 参考项目/JQ2PTrade/ptrade_local/run_backtest.py
    - 参考项目/EasyXT/easyxt_backtest/performance.py
    - 参考项目/EasyXT/easyxt_backtest/portfolio_daily_result.py
    - 参考项目/EasyXT/easyxt_backtest/core/backtest_core.py
  license: MIT / project-local reference; verify before runtime adoption
  allowed_use: architecture_only
  qmd_target_files:
    - docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md
    - docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md
    - specs/contracts/backtest_contract.yaml
    - specs/contracts/backtest_metric_contract.yaml
    - specs/contracts/backtest_reproducibility_contract.yaml
    - specs/contracts/review_sandbox_contract.yaml
  direct_copy_allowed: false
  rewrite_required:
    - exclude_execution_style_api_names
    - replace_console_reporting_with_structured_evidence
    - replace_arbitrary_strategy_exec_with_qmd_read_only_scenarios
    - replace_reference_loader_db_paths_with_qmd_evidence_refs
  forbidden_semantics:
    - compile_exec_strategy_runtime
    - order
    - order_value
    - order_target
    - order_target_value
    - cancel_order
    - get_open_orders
    - get_positions
    - get_orders
    - get_trades
    - run_daily
    - run_weekly
    - run_monthly
    - backtrader_cerebro_first_slice_dependency
  attribution_required: true
```

---

## 2. Reference source files and audit findings

Round4 B04_05 must read and cite these reference files locally:

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

### 2.1 What can be adapted

From JQ2PTrade:

- `data_loader.py`
  - deterministic `DataBundle` shape;
  - bounded `load(start_date, end_date)` entrypoint;
  - read-only DuckDB connection;
  - pre-grouped symbol/date frames;
  - narrow history lookup shape.
- `backtester.py`
  - daily replay loop shape only: set date, evaluate bounded inputs, append daily result, hand off to report;
  - structured warning capture idea.
- `report.py`
  - report generation separated from loader/runner;
  - deterministic compact report from structured series.
- `api.py` / `api_mapping.json`
  - action API deny-list source for no-action guard tests.

From EasyXT backtest:

- `performance.py`
  - metric grouping into return, risk, and risk-adjusted sections;
  - stable empty-input metrics;
  - total return, annual return, drawdown, volatility, Sharpe, Calmar, win-rate, profit/loss ratio formulas when computed from QMD-owned series.
- `portfolio_daily_result.py`
  - daily-result dataframe/report shape and summary-statistics boundary.
- `core/backtest_core.py`
  - analyzer/result-extraction boundary as architecture only; not the Backtrader runtime.

### 2.2 What must be rewritten or excluded

- No arbitrary user strategy execution. JQ2PTrade `backtester.py` uses `compile(..., 'exec')` and `exec(...)`; QMD must not copy this.
- No `sys.path` mutation or arbitrary strategy file entrypoint from `run_backtest.py`.
- No PTrade compatibility runtime.
- No order/broker/account/position/scheduler API names.
- No hardcoded `D:/StockData/stock_data.ddb`, `stock_daily`, `period='1d'`, or full stock/index universe loading.
- No `.SH -> .SS` storage mutation that loses raw source identity.
- No Backtrader/Cerebro runtime dependency in the first QMD read-only review slice.
- No console-only report; all output must be QMD report artifact with evidence refs and limitations.

---

## 3. Directly executable Round4 landing plan

Round4 B04_05 must be implemented as issue-style vertical slices, also summarized in `docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md`.

### Slice B04_05-A — Frozen loader

- **Borrow from:** JQ2PTrade `DataBundle`, bounded `load`, read-only grouped lookup.
- **Rewrite into:** `backend/app/review/frozen_loader.py`.
- **Delete/forbid:** hardcoded DB path/table, broad universe, source-code mutation, no caps.
- **Tests:** broad-scan rejection, missing evidence rejection, source identity preservation, ResourceGuard cap.
- **Not done if:** loader can run with no evidence refs or unbounded universe.

### Slice B04_05-B — No-action guard

- **Borrow from:** JQ2PTrade `api.py` / `api_mapping.json` action names as deny-list material.
- **Rewrite into:** `backend/app/review/no_action_guard.py` and `tests/test_no_action_semantics.py`.
- **Delete/forbid:** PTrade namespace, orders, broker/account/position state, scheduler hooks.
- **Tests:** action API names and output action language fail closed.
- **Not done if:** report/API can emit buy/sell/add/reduce/order/position instructions.

### Slice B04_05-C — First read-only review runner

- **Borrow from:** JQ2PTrade daily loop shape only.
- **Rewrite into:** `backend/app/review/review_runner.py`.
- **Delete/forbid:** `compile`, `exec`, arbitrary strategy file, Backtrader/Cerebro engine.
- **Tests:** one `event_study` or `evidence_chain_review` runs with no-lookahead/window enforcement; unsupported scenarios return `DEFERRED_BACKTEST_TYPE`.
- **Not done if:** only scenario registry exists or runner executes user code.

### Slice B04_05-D — Report artifact and metrics

- **Borrow from:** JQ2PTrade `report.py` separation and EasyXT metric grouping.
- **Rewrite into:** `backend/app/review/report_builder.py` and `backend/app/review/metrics.py`.
- **Delete/forbid:** console-only report, live-trading readiness, metrics not tied to QMD evidence.
- **Tests:** deterministic report hash, evidence refs, limitations, metrics from QMD-owned series only.
- **Not done if:** metric-only micro-slice exists without a runnable review scenario.

### Slice B04_05-E — Read-only API binding

- **Borrow from:** none; use QMD API/security contracts.
- **Rewrite into:** `backend/app/api/routes/backtest_review.py` and `backend/app/api/schemas/backtest_review.py`.
- **Delete/forbid:** write/fetch triggers, direct DB mutation, unauthenticated route.
- **Tests:** auth, success, deferred, forbidden action, over-budget, missing evidence, error redaction.
- **Not done if:** API exposes shell route with fake success data.

---

## 4. Target files

Update:

```text
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_TASK_CARD_MANIFEST.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_HARDENING_RULES.md
specs/contracts/backtest_contract.yaml
specs/contracts/backtest_metric_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/review_sandbox_contract.yaml
specs/verification/contract_coverage.yaml
```

Round4 task cards must carry the detailed source-path adaptation instructions locally. Do not move executable details into a separate inventory.

---

## 5. Round4 required batch structure

Round4 backtest/review must fit at most three implementation batches:

1. **Batch A — read-only vertical slice:** scenario registry, bounded loader, deterministic runner, report artifact, no-action semantics.
2. **Batch B — production-complete supported scope:** event sets, metrics, evidence-chain review, reproducibility, API binding.
3. **Batch C — hardening/regression:** resource limits, reproducibility drift tests, report limitations, security boundaries.

The first batch cannot be a shell; it must run end-to-end against a bounded QMD evidence dataset.

---

## 6. Done criteria

R3FR-04 is done when Round4 backtest/review cards no longer describe a from-scratch engine and instead require JQ2PTrade/EasyXT-informed QMD-owned implementation with no action semantics, source/evidence binding, explicit tests, not-done conditions, and a three-batch ceiling to full stable shape.
