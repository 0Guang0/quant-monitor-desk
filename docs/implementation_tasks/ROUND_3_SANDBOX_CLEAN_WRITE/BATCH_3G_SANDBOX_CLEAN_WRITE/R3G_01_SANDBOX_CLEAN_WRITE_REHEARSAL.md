# R3G-01 — Sandbox Clean-Write Rehearsal

> **Batch:** Batch 3G — Sandbox Clean Write and Limited Production Entry  
> **Roadmap segment:** Round 3G.1  
> **Status:** future task; **preconditions satisfied** @ R3FR-07 (Batch 3F-R closed).  
> **Execution posture:** sandbox only; no production mutation; no live source default enablement.

---

## 1. Business purpose

Rehearse the first clean-write path in a sandbox database using only tightly bounded candidate domains:

- `baostock` → `cn_equity_daily_bar`
- `cninfo` → `cn_announcements` metadata only
- `fred` → P0 macro sample only, and only with explicit authorization/evidence requirements satisfied

The goal is not to broaden data coverage. The goal is to prove that raw/staged evidence can pass QMD-owned data-quality, validation, lineage, write, and rollback gates before any limited production entry is considered.

---

## 2. Required reading before implementation

### QMD files

- `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3F-R and Round 3G
- `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_02_EASYXT_DATA_HEALTH_REFACTOR.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_06_QMD_DATA_HEALTH_CLI_RUNTIME.md`
- `backend/app/datasources/service.py`
- `backend/app/datasources/route_planner.py`
- `backend/app/db/write_manager.py`
- `backend/app/db/validation_gate.py`
- `backend/app/core/resource_guard.py`
- `backend/app/ops/data_health.py`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`

### Reference source files to inspect and adapt from

- `参考项目/EasyXT/data_manager/data_integrity_checker.py`
- `参考项目/EasyXT/data_manager/smart_data_detector.py`
- `参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py`
- `参考项目/JQ2PTrade/ptrade_local/engine/report.py`
- `参考项目/JQ2PTrade/api_mapping.json`
- `参考项目/OpenBB/openbb_platform/providers/` directory layout
- `参考项目/OpenBB/openbb_platform/providers/fred/README.md`

Do not create a separate `reference_adoption_inventory.md` for this task. Put adoption decisions directly in this task card or in the concrete implementation PR notes.

---

## 3. Existing QMD wheel to replace or avoid

This task must not create a new ad-hoc clean-write runner that bypasses existing QMD gates.

Use or extend existing QMD gates:

- `DataSourceService` for source routing/fetch evidence.
- `SourceRoutePlanner` for provider choice.
- `ResourceGuard` before bounded rehearsal jobs.
- `DbValidationGate` before clean-table merge.
- `WriteManager` for any sandbox clean write.
- R3F-R data-health profiles before write admission.

If existing code lacks a narrow sandbox entrypoint, add a small orchestrator that composes those gates; do not bypass them.

---

## 4. Reference adoption details

### 4.1 EasyXT data-integrity checker

Reference path:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
```

Useful parts to adapt:

- `DataQualityReport` shape: collect `issues`, `warnings`, `info`, and summary counts.
- `check_integrity(...)` orchestration order:
  1. missing trading days
  2. null/required-field checks
  3. OHLC relation checks
  4. extreme return checks
  5. volume anomaly checks
- `_check_data_quality(...)` rule ideas:
  - empty data is error
  - null required fields are error
  - non-positive `open/high/low/close` is error
- `_check_price_relations(...)` rule ideas:
  - `high >= max(open, close)`
  - `low <= min(open, close)`
- `_check_outliers(...)` rule idea:
  - single-period return above threshold becomes warning
- `_check_volume_anomalies(...)` rule idea:
  - volume above rolling/statistical threshold becomes info/warning
- `generate_integrity_report(...)` summary idea:
  - total checked symbols/series
  - pass/warn/fail counts
  - first N issue details only

Must rewrite before QMD use:

- Remove `sys.path.insert(...)`.
- Remove default DB path lookup from EasyXT (`get_default_db_path`).
- Remove hardcoded `stock_daily` table name.
- Remove string-interpolated SQL.
- Do not instantiate EasyXT `DataIntegrityChecker` or import from `参考项目/**` at runtime.
- Convert logic into QMD-owned pure functions under `backend/app/ops/data_health_profiles/**` or the R3F-R-defined final path.
- Return QMD structured data-health result objects, not free-form strings only.
- Support both market bars and macro/metadata candidates through profile-specific rule sets.

Concrete QMD adaptation target:

```text
backend/app/ops/data_health_profiles/ohlcv_rules.py
backend/app/ops/data_health_profiles/calendar_gap_rules.py
backend/app/ops/data_health_profiles/report_builder.py
backend/app/ops/data_health.py
specs/contracts/data_quality_rules.yaml
tests/test_data_health_easyxt_ohlcv_rules.py
```

R3G-01 must call those QMD-owned profiles; it must not reimplement another local rule set.

### 4.2 EasyXT smart missing-data detector

Reference path:

```text
参考项目/EasyXT/data_manager/smart_data_detector.py
```

Useful parts to adapt:

- `TradingCalendar.get_trading_days(start, end)` idea.
- `TradingCalendar.get_missing_trading_days(start, end, existing_dates)` idea.
- `_group_continuous_dates(...)` idea for grouping missing days into segments.
- `detect_missing_data(...)` result shape:
  - expected trading days
  - existing count
  - first/last existing date
  - missing days
  - missing segments
  - completeness ratio

Must rewrite before QMD use:

- Do not copy EasyXT's hardcoded holiday generation as authoritative calendar.
- Use QMD's approved exchange calendar source/fixture/registry, or mark calendar gap checks as WARN until official calendar evidence is available.
- Remove direct DuckDB query from detector.
- Input should be a bounded candidate dataframe / staged evidence snapshot, not a DB path.
- `get_download_plan(...)` must not be copied into R3G-01 because this task is a write rehearsal, not a downloader.

Concrete QMD adaptation target:

```text
backend/app/ops/data_health_profiles/calendar_gap_rules.py
backend/app/ops/data_health_profiles/report_builder.py
specs/contracts/data_quality_rules.yaml
```

### 4.3 JQ2PTrade data-loader pattern

Reference path:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
```

Useful parts to adapt for R3G-01 only as a frozen-data loading pattern:

- `DataBundle` idea: return a simple object containing available dates and available symbols/series.
- `load(start_date, end_date)` bounded window idea.
- Read-only DuckDB connection idea.
- Pre-grouping rows by code/series into in-memory frames before downstream checks.
- `get_stock_history(...)` idea: narrow history lookup by code/date/fields.

Must rewrite before QMD use:

- Remove default path `D:/StockData/stock_data.ddb`.
- Remove `print(...)` side effects; use QMD logging/evidence artifact instead.
- Remove broad stock/index load; R3G-01 must accept explicit capped candidates only.
- Remove hardcoded `stock_daily`, `period='1d'`, `symbol_type IN ('stock', 'index')` assumptions unless mapped through QMD domain contracts.
- Do not copy `.SH → .SS` conversion into storage; any symbol normalization must live in QMD normalizers and preserve raw source code.
- Do not calculate trading limits (`high_limit`, `low_limit`) in R3G-01 unless needed by a data-health rule and separately specified.
- Do not import JQ2PTrade code at runtime.

Concrete QMD adaptation target:

```text
backend/app/ops/sandbox_clean_write/rehearsal_loader.py
backend/app/ops/sandbox_clean_write/rehearsal_plan.py
tests/test_round3g_sandbox_rehearsal_loader.py
```

The loader should operate on QMD raw/staged evidence and should expose a deterministic bounded data bundle for `baostock`, `cninfo`, and authorized `fred` samples.

### 4.4 JQ2PTrade report pattern

Reference path:

```text
参考项目/JQ2PTrade/ptrade_local/engine/report.py
```

Useful parts to adapt as a report-shape idea only:

- Compute compact summary metrics from a deterministic time series.
- Keep report generation separated from data loading.
- Return text/structured report rather than mutating external state.

Must rewrite before QMD use:

- R3G-01 is not a strategy/backtest task; do not copy portfolio, trade, benchmark, win-rate, commission, or order-related metrics.
- Replace performance metrics with write-rehearsal metrics:
  - candidate source/domain
  - row count raw/staged/sandbox clean
  - validation pass/warn/fail counts
  - source_fetch_id coverage
  - content_hash/schema_hash coverage
  - duplicate primary-key count
  - missing trading-day/required-field/OHLC violations
  - WriteManager operation id
  - rollback artifact path

Concrete QMD adaptation target:

```text
backend/app/ops/sandbox_clean_write/rehearsal_report.py
tests/test_round3g_sandbox_rehearsal_report.py
```

### 4.5 JQ2PTrade API mapping guardrail

Reference path:

```text
参考项目/JQ2PTrade/api_mapping.json
```

Allowed as read-only naming reference only:

- `get_price`
- `get_current_data`
- `get_fundamentals`
- `get_security_info`
- `record`
- `plot`

Forbidden in R3G-01 and all 3G work:

- `order`
- `order_value`
- `order_target`
- `order_target_value`
- `cancel_order`
- `get_open_orders`
- `get_portfolio`
- `get_positions`
- `get_orders`
- `get_trades`
- scheduler/execution hooks such as `run_daily`, `run_weekly`, `run_monthly`

Do not add any compatibility layer that exposes those names.

### 4.6 OpenBB provider architecture

Reference paths:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Useful parts to adapt as architecture only:

- Provider-per-package organization.
- Provider README that documents external provider, installation, and docs link.
- Provider-specific metadata separation.
- Optional provider extension pattern, but only conceptually.

Must not copy:

- OpenBB runtime source code.
- Provider fetcher implementation classes.
- AGPL-covered source into QMD runtime.

Concrete QMD adaptation target for R3G-01:

```text
specs/datasource_registry/provider_catalog.yaml
backend/app/datasources/provider_catalog.py
```

For the rehearsal candidates, provider metadata must at least state:

```yaml
provider_id: baostock | cninfo | fred
enabled_by_default: false for fred, as registry currently requires authorization
validation_only: true/false according to registry
production_default_allowed: false for R3G-01
requires_user_authorization: true for fred live fetch
allowed_domains: []
max_default_symbols_or_series: bounded explicit cap
max_default_window_days: bounded explicit cap
terms_or_license_notes: explicit note
reference_architecture: OpenBB provider package layout only; no source copy
```

### 4.7 TradingAgents / agents-for-openbb

R3G-01 must not use TradingAgents, TradingAgents-astock, or agents-for-openbb.

Reason: R3G-01 is a write rehearsal gate, not an Agent/UI artifact task. Any Agent-triggered write is forbidden. Future Round4 Agent/UI cards may evaluate these projects, but this task should only state the exclusion and enforce it through tests/guardrails.

---

## 5. Required implementation shape

Create or update QMD-owned files only. Suggested target files:

```text
backend/app/ops/sandbox_clean_write/__init__.py
backend/app/ops/sandbox_clean_write/rehearsal_plan.py
backend/app/ops/sandbox_clean_write/rehearsal_loader.py
backend/app/ops/sandbox_clean_write/rehearsal_runner.py
backend/app/ops/sandbox_clean_write/rehearsal_report.py
backend/app/cli/data_commands.py
specs/contracts/sandbox_clean_write_contract.yaml
tests/test_round3g_sandbox_clean_write_rehearsal.py
tests/test_round3g_sandbox_rehearsal_loader.py
tests/test_round3g_sandbox_rehearsal_report.py
```

The final implementation may choose different names, but the PR must document the mapping.

---

## 6. Candidate caps

Default R3G-01 rehearsal caps:

```yaml
baostock:
  domains: [cn_equity_daily_bar]
  max_symbols: 3
  max_window_days: 30
cninfo:
  domains: [cn_announcements]
  metadata_only: true
  max_symbols: 3
  max_window_days: 30
  full_pdf_download: false
fred:
  domains: [macro_series]
  max_series: 3
  max_window_days: 120
  requires_user_authorization: true
```

Any increase requires a task-card amendment or ADR.

---

## 7. Required command shape

Suggested CLI shape:

```bash
qmd data sandbox-clean-write rehearse \
  --candidate-set r3g_p0 \
  --sandbox-db .audit-sandbox/round3g/rehearsal.duckdb \
  --evidence-dir .audit-sandbox/round3g/evidence \
  --report .audit-sandbox/round3g/rehearsal_report.json \
  --no-production-mutation
```

The command must fail closed if `--no-production-mutation` is absent or if a production DB path is supplied.

---

## 8. Forbidden scope

- No production DB mutation.
- No default live fetch.
- No full market.
- No full history.
- No minute bars.
- No QMT, TDX, xqshare, Yahoo production primary.
- No full PDF downloads.
- No Agent-triggered write.
- No runtime import from `参考项目/**`.
- No OpenBB runtime source copy.
- No JQ2PTrade execution/trading API compatibility layer.

---

## 9. Tests / gates

Required verification:

```bash
uv run pytest tests/test_round3g_sandbox_clean_write_rehearsal.py -q
uv run pytest tests/test_round3g_sandbox_rehearsal_loader.py -q
uv run pytest tests/test_round3g_sandbox_rehearsal_report.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Test expectations:

- rehearsal refuses production DB path;
- rehearsal refuses broad candidate set;
- rehearsal uses `WriteManager` and `DbValidationGate` for sandbox clean write;
- data-health profile is invoked before write admission;
- report contains raw/staged/sandbox row counts and hash coverage;
- no `参考项目/**` import exists in runtime code;
- forbidden JQ2PTrade API names are not exposed;
- OpenBB reference is architecture-only.

---

## 10. Done criteria

R3G-01 is done only when:

- sandbox rehearsal writes only to a sandbox DB/path;
- all candidates are capped and explicit;
- EasyXT-derived data-health ideas are implemented as QMD-owned profile rules, not imported;
- JQ2PTrade-derived loader/report ideas are rewritten for rehearsal evidence, not copied as backtest code;
- OpenBB is used only as provider metadata architecture reference;
- rehearsal report proves row counts, validation status, hash lineage, WriteManager operation, and rollback artifact;
- no production write gate is opened.
