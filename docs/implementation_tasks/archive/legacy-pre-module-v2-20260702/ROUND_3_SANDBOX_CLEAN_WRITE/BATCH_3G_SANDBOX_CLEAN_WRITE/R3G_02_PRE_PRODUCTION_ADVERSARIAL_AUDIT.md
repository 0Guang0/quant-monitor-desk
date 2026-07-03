# R3G-02 — Strict Pre-Production Adversarial Audit

> **Batch:** Batch 3G — Sandbox Clean Write and Limited Production Entry  
> **Roadmap segment:** Round 3G.2  
> **Status:** future task; runs only after R3G-01 sandbox rehearsal produces evidence.  
> **Execution posture:** audit only; no production mutation.

---

## 1. Business purpose

Turn R3G-01 rehearsal evidence into a strict go/no-go decision before any limited production entry is discussed.

The audit outcome must be exactly one of:

- `PASS_ALLOW_LIMITED_PROD_WRITE`
- `WARN_ALLOW_WITH_MANUAL_APPROVAL`
- `BLOCK_PRODUCTION_WRITE`

This task must actively try to disprove readiness. It is not a sign-off formality.

---

## 2. Required inputs

- R3G-01 rehearsal report JSON.
- R3G-01 sandbox DB path.
- R3G-01 evidence directory.
- `specs/contracts/sandbox_clean_write_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- R3F-R data-health profile outputs.

Reference source files to inspect for audit criteria:

- `参考项目/EasyXT/data_manager/data_integrity_checker.py`
- `参考项目/EasyXT/data_manager/smart_data_detector.py`
- `参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py`
- `参考项目/JQ2PTrade/ptrade_local/engine/report.py`
- `参考项目/JQ2PTrade/api_mapping.json`
- `参考项目/OpenBB/openbb_platform/providers/` directory layout

Do not create a separate reference inventory file. Any reference-adoption finding must be written directly into this task result or the implementation PR notes.

---

## 3. Audit dimensions

### 3.1 Data-quality adversarial audit

Use EasyXT as the reference checklist source, but not as runtime code.

From `参考项目/EasyXT/data_manager/data_integrity_checker.py`, audit whether R3G-01 evidence covers:

- empty data error;
- required-field null checks;
- non-positive OHLC checks;
- OHLC relation checks;
- extreme return warnings;
- volume anomaly warnings;
- compact issue summary.

From `参考项目/EasyXT/data_manager/smart_data_detector.py`, audit whether R3G-01 evidence covers:

- expected calendar rows vs existing rows;
- missing trading-day count;
- missing segment grouping;
- completeness ratio;
- explicit status if official calendar evidence is not available.

Required audit behavior:

- If `cn_equity_daily_bar` lacks required OHLCV profile evidence, return `BLOCK_PRODUCTION_WRITE`.
- If calendar checks are only approximate, return at most `WARN_ALLOW_WITH_MANUAL_APPROVAL`.
- If data-health logic was reimplemented ad hoc inside R3G-01 instead of using R3F-R profiles, return `BLOCK_PRODUCTION_WRITE`.

### 3.2 Loader/boundedness audit

Use `参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py` only as a frozen-data loader pattern reference.

Audit for the following forbidden patterns:

- hardcoded DB path;
- broad `stock_daily` table scan without explicit source/domain/symbol/window caps;
- full stock/index universe load;
- symbol rewriting that loses raw-source identity;
- print-only evidence instead of structured report;
- runtime import from `参考项目/**`.

If any is present in QMD runtime code, return `BLOCK_PRODUCTION_WRITE`.

### 3.3 Report/evidence audit

Use `参考项目/JQ2PTrade/ptrade_local/engine/report.py` only as a separation-of-reporting reference.

Audit whether R3G-01 report contains:

- source/domain/candidate set;
- raw row count;
- staged row count;
- sandbox clean row count;
- validation pass/warn/fail counts;
- `source_fetch_id` coverage;
- `content_hash` coverage;
- `schema_hash` coverage;
- data-health issue counts;
- WriteManager operation id;
- rollback artifact path;
- no strategy/backtest/trade metrics.

If report only contains prose or omits write/rollback proof, return `BLOCK_PRODUCTION_WRITE`.

### 3.4 Provider architecture audit

Use OpenBB only as architecture reference:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Audit whether QMD has provider metadata for every R3G-01 candidate:

- provider/source id;
- allowed domain;
- auth requirement;
- enabled-by-default posture;
- production default allowed posture;
- cost/terms note;
- default cap;
- reference-architecture-only note for OpenBB.

If OpenBB runtime code is copied into QMD, return `BLOCK_PRODUCTION_WRITE`.

### 3.5 No-action / no-agent audit

R3G must not use TradingAgents, TradingAgents-astock, or agents-for-openbb.

Audit for:

- Agent-triggered write;
- Agent-generated candidate expansion;
- trading/order API names from `参考项目/JQ2PTrade/api_mapping.json`;
- scheduler-like execution hooks (`run_daily`, `run_weekly`, `run_monthly`).

Any finding returns `BLOCK_PRODUCTION_WRITE`.

---

## 4. Suggested implementation files

```text
backend/app/ops/sandbox_clean_write/adversarial_audit.py
backend/app/ops/sandbox_clean_write/audit_decision.py
backend/app/cli/data_commands.py
specs/contracts/sandbox_clean_write_contract.yaml
tests/test_round3g_pre_production_adversarial_audit.py
```

---

## 5. Required command shape

```bash
qmd data sandbox-clean-write audit \
  --rehearsal-report .audit-sandbox/round3g/rehearsal_report.json \
  --sandbox-db .audit-sandbox/round3g/rehearsal.duckdb \
  --evidence-dir .audit-sandbox/round3g/evidence \
  --decision-report .audit-sandbox/round3g/audit_decision.json
```

This command must not accept a production DB write path.

---

## 6. Forbidden scope

- No production DB mutation.
- No new source fetch unless it is a read-only evidence verification explicitly authorized by R3G-01 artifacts.
- No candidate cap expansion.
- No fallback from failed candidate to another source.
- No OpenBB runtime source copy.
- No JQ2PTrade execution API compatibility.
- No Agent/UI artifact integration.

---

## 7. Tests / gates

Required verification:

```bash
uv run pytest tests/test_round3g_pre_production_adversarial_audit.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Test expectations:

- missing R3G-01 report returns `BLOCK_PRODUCTION_WRITE`;
- missing data-health profile evidence returns `BLOCK_PRODUCTION_WRITE`;
- approximate calendar evidence returns at most `WARN_ALLOW_WITH_MANUAL_APPROVAL`;
- uncapped candidate set returns `BLOCK_PRODUCTION_WRITE`;
- runtime import from `参考项目/**` returns `BLOCK_PRODUCTION_WRITE`;
- forbidden trading/order API names return `BLOCK_PRODUCTION_WRITE`;
- copied OpenBB provider runtime returns `BLOCK_PRODUCTION_WRITE`;
- valid bounded evidence returns `PASS_ALLOW_LIMITED_PROD_WRITE` or warning state with explicit manual approval requirement.

---

## 8. Done criteria

R3G-02 is done only when:

- audit output uses the exact decision enum;
- every decision includes blocking/warning reasons and evidence paths;
- R3G-01 cannot proceed to R3G-03 unless audit decision allows it;
- no production mutation or cap expansion is performed by the audit;
- reference-adoption guardrails are enforced by tests.
