# R3G-03 — Limited Production Clean Write

> **Batch:** Batch 3G — Sandbox Clean Write and Limited Production Entry  
> **Roadmap segment:** Round 3G.3  
> **Status:** future task; blocked until R3G-02 allows entry.  
> **Execution posture:** explicit user approval required; extreme caps; before/after proof and rollback dry run required.

---

## 1. Business purpose

Perform the first very small production clean-write entry only after R3G-01 sandbox rehearsal and R3G-02 adversarial audit prove that the path is bounded, reversible, and accurately reported.

This task does not broaden production ingestion. It authorizes only a capped pilot:

- 1–3 sources;
- 3–10 symbols/series total;
- 30–120 day window depending on source/domain;
- exact user approval artifact;
- before/after DB proof;
- rollback dry run.

---

## 2. Required preconditions

All must be true:

1. R3G-01 completed with sandbox report.
2. R3G-02 decision is `PASS_ALLOW_LIMITED_PROD_WRITE`, or `WARN_ALLOW_WITH_MANUAL_APPROVAL` plus explicit user approval.
3. `specs/contracts/sandbox_clean_write_contract.yaml` is present and matches this task.
4. `specs/contracts/reference_adoption_guardrails.yaml` includes Round3G scoped adoption rules.
5. Candidate sources are present in source registry and capability registry.
6. `qmd data health` supported profiles exist for candidate domains.
7. User approval artifact specifies exact source/domain/symbol/window/path.

---

## 3. Reference source implications

This task should not directly adapt reference project code. It consumes the QMD-owned implementation produced by R3G-01/R3G-02.

However, it must enforce the same source-specific guardrails:

### EasyXT-derived data-health requirements

From:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
```

Production entry must prove the QMD-owned implementation checks:

- required-field nulls;
- non-positive OHLC;
- OHLC relations;
- duplicate primary keys;
- extreme returns;
- volume anomalies;
- missing trading days or explicit calendar-quality warning;
- completeness ratio.

Do not import EasyXT. Do not copy EasyXT DB/query/calendar implementation into production runtime.

### JQ2PTrade-derived loader/report requirements

From:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/api_mapping.json
```

Production entry must prove:

- bounded data bundle is explicit;
- read stage and write stage are separate;
- report is generated from structured evidence;
- no strategy/backtest/order metrics are present;
- forbidden API names are not exposed.

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

### OpenBB-derived provider metadata requirements

From:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Production entry must prove candidate provider metadata is explicit and QMD-owned:

- provider/source id;
- allowed domain;
- auth/terms/cost notes;
- enabled-by-default posture;
- production default posture;
- explicit caps;
- OpenBB architecture reference only, no source copy.

### TradingAgents / agents-for-openbb exclusion

R3G-03 must not use TradingAgents, TradingAgents-astock, or agents-for-openbb. No Agent path may approve, trigger, expand, or summarize a production write in a way that replaces the required user approval artifact.

---

## 4. Suggested implementation files

```text
backend/app/ops/sandbox_clean_write/limited_production_entry.py
backend/app/ops/sandbox_clean_write/approval_contract.py
backend/app/ops/sandbox_clean_write/rollback_plan.py
backend/app/cli/data_commands.py
specs/contracts/sandbox_clean_write_contract.yaml
tests/test_round3g_limited_production_clean_write.py
tests/test_round3g_limited_production_rollback.py
```

---

## 5. Required command shape

Suggested CLI shape:

```bash
qmd data sandbox-clean-write promote \
  --approval-file approvals/r3g_limited_write_YYYYMMDD.yaml \
  --audit-decision .audit-sandbox/round3g/audit_decision.json \
  --before-proof .audit-sandbox/round3g/before_proof.json \
  --after-proof .audit-sandbox/round3g/after_proof.json \
  --rollback-plan .audit-sandbox/round3g/rollback_plan.json
```

The command must fail closed unless approval file and audit decision agree exactly on:

- source id;
- domain;
- symbol/series list;
- start/end date;
- target table;
- max rows;
- production DB path;
- rollback plan path;
- approver identity or explicit user authorization marker.

---

## 6. Approval file minimum schema

```yaml
approval_id: ""
approver: ""
approved_at: ""
audit_decision_file: ""
source_candidates:
  - source_id: baostock
    domain: cn_equity_daily_bar
    symbols: []
    start_date: ""
    end_date: ""
    max_rows: 0
  - source_id: cninfo
    domain: cn_announcements
    symbols: []
    start_date: ""
    end_date: ""
    metadata_only: true
    max_rows: 0
  - source_id: fred
    domain: macro_series
    series: []
    start_date: ""
    end_date: ""
    max_rows: 0
    live_fetch_authorized: false
production_db_path: ""
rollback_required: true
no_agent_triggered_write: true
no_cap_expansion: true
```

---

## 7. Required before/after proof

Before proof must include:

- target table row count;
- affected key range count;
- target schema hash;
- latest write operation id if any;
- backup or snapshot pointer;
- ResourceGuard decision.

After proof must include:

- inserted/updated row count;
- unchanged row count for non-target range;
- validation status;
- source_fetch_id coverage;
- content_hash/schema_hash coverage;
- WriteManager operation id;
- rollback plan id;
- data-health status.

Rollback dry run must prove affected rows can be identified and removed/reverted without touching non-target keys.

---

## 8. Forbidden scope

- No cap expansion beyond approval file.
- No broad source fallback.
- No full-market or full-history write.
- No minute bars.
- No QMT, TDX, xqshare, Yahoo production primary.
- No Agent-triggered write.
- No full PDF downloads.
- No runtime import from `参考项目/**`.
- No OpenBB runtime source copy.
- No JQ2PTrade trading API compatibility layer.

---

## 9. Tests / gates

Required verification:

```bash
uv run pytest tests/test_round3g_limited_production_clean_write.py -q
uv run pytest tests/test_round3g_limited_production_rollback.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Test expectations:

- missing approval file blocks;
- mismatched approval and audit decision blocks;
- cap expansion blocks;
- missing before proof blocks;
- missing rollback plan blocks;
- Agent-triggered write marker blocks;
- forbidden source/domain blocks;
- WriteManager/DbValidationGate bypass blocks;
- runtime import from `参考项目/**` blocks;
- OpenBB/JQ2PTrade unsafe copy blocks.

---

## 10. Done criteria

R3G-03 is done only when:

- every production write is explicitly approved and capped;
- before/after proof is generated and machine-checkable;
- rollback dry run is generated and machine-checkable;
- no reference project runtime code is imported or copied unsafely;
- no Agent/UI path can initiate or broaden the write;
- release notes state the exact source/domain/symbol/window and limitations.
