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
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md
```

---

## 3. Reference project source to inspect

Read these files under `参考项目/**` before implementation:

```text
参考项目/JQ2PTrade/api_mapping.json
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/context.py
参考项目/JQ2PTrade/ptrade_local/engine/backtester.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/ptrade_local/run_backtest.py
参考项目/EasyXT/easyxt_backtest/performance.py
参考项目/EasyXT/easyxt_backtest/portfolio_daily_result.py
参考项目/EasyXT/easyxt_backtest/core/backtest_core.py
```

Useful ideas to adapt into QMD-owned code:

- From JQ2PTrade `data_loader.py`:
  - `DataBundle` idea for deterministic in-memory data bundle;
  - `load(start_date, end_date)` bounded-window shape;
  - read-only DuckDB connection;
  - pre-grouped symbol/date data frame for fast lookup.
- From JQ2PTrade `report.py`:
  - reporting separated from loader/runtime;
  - compact deterministic metric/report text from structured series.
- From JQ2PTrade `api_mapping.json`:
  - allow/deny map source, especially order/trading API names that must be forbidden.
- From EasyXT backtest:
  - metric organization and report/portfolio-result shape only if non-execution and license-safe.

Must rewrite or exclude:

- hardcoded DuckDB paths such as `D:/StockData/stock_data.ddb`;
- broad full-universe stock/index scans;
- `.SH` → `.SS` mutation that loses raw source identity;
- trading limits/order/commission/win-rate/portfolio action metrics in first QMD review slice;
- any arbitrary strategy execution runtime;
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
tests/test_catalog.yaml
```

If final names differ, the PR must document the mapping.

---

## 5. Implementation plan

1. **Scenario registry**
   - Implement a machine-readable registry for supported and deferred scenario types.
   - First supported scenario must be one of:
     - `event_study`, or
     - `evidence_chain_review`.
   - All other contract-listed backtest types must return `DEFERRED_BACKTEST_TYPE` and must not appear runnable.

2. **Frozen/read-only loader**
   - Implement a bounded loader inspired by JQ2PTrade `DataBundle`, but QMD-owned.
   - Inputs must be explicit: `scenario_id`, `source/evidence refs`, `symbols/series`, `start_date`, `end_date`, `max_rows`, `max_events`.
   - Loader must use QMD evidence/frozen datasets and ResourceGuard; no broad scans.
   - Preserve raw source IDs and source lineage.

3. **Review runner**
   - Execute only the first supported read-only scenario.
   - No user strategy code execution.
   - No order/action API surface.
   - Enforce no-lookahead and window boundaries.

4. **Report artifact**
   - Build a deterministic report from structured run output.
   - Required fields:
     - `scenario_id`
     - `scenario_type`
     - `input_evidence_ids`
     - `window_start/window_end`
     - `row_count/event_count`
     - `metrics`
     - `limitations`
     - `no_action_semantics: true`
     - `resource_budget`
   - Do not claim live trading readiness.

5. **No-action / deny-list guard**
   - Convert JQ2PTrade `api_mapping.json` into a QMD deny-list test fixture or contract section.
   - Runtime must reject forbidden API names and forbidden output terms.

6. **API binding**
   - If adding HTTP routes, expose only read-only review endpoints from `backtest_contract.yaml`.
   - Route must require auth and ResourceGuard budget.

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
uv run pytest tests/test_backtest_review.py tests/test_backtest_reproducibility.py tests/test_no_action_semantics.py tests/test_review_sandbox_contract.py -q
uv run ruff check backend/app/review backend/app/api tests
```

Test expectations:

- one supported review scenario runs end-to-end against bounded fixture/frozen evidence;
- unsupported types return `DEFERRED_BACKTEST_TYPE`;
- no-lookahead and window-boundary violations fail;
- ResourceGuard rejects over-budget scans;
- forbidden JQ2PTrade API names are rejected;
- report artifact includes evidence refs, limitations, and no-action semantics;
- no runtime import from `参考项目/**`.

---

## 8. Done criteria

B04_05 is done only when at least one backtest/review type has QMD-owned runtime, tests, and a report artifact. Blank-engine design, registry-only scaffolding, or metric-only micro-slices are not acceptable.
