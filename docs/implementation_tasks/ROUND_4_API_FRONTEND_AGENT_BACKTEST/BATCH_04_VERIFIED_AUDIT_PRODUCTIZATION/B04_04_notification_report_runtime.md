# B04_04 — Notification and Report Runtime

> **Batch:** Batch 04 — Verified Audit Productization  
> **Owns:** `VR-NOTIF-001`, loose historical card `028_implement_reports_and_notifications.md`  
> **Roadmap:** Round 4.4 track.  
> **Execution posture:** backend/report runtime only; no external fan-out by default; no trading-action notifications.

---

## 1. Business purpose

Implement the first notification/report vertical slice: one bounded QMD event becomes a report entry and deduplicated notification log record with evidence/fetch/hash lineage where available.

This task is not complete if it only adds schema files or a service shell.

---

## 2. Required QMD inputs

Read these **本项目** files before implementation:

```text
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md
specs/contracts/notification_report_contract.yaml
specs/contracts/log_audit_contract.yaml
specs/contracts/data_quality_rules.yaml
specs/contracts/source_conflict_rules.yaml
specs/contracts/snapshot_lineage_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
docs/modules/data_validation_and_conflict.md
docs/modules/layer5_security_evidence.md
docs/modules/write_manager.md
```

If `notification_report_contract.yaml` is still a waiver-only contract, this task must either create the concrete runtime contract fields or precisely re-defer the missing pieces with owner and closure test.

Reference projects are not required for runtime logic. If report artifact formatting is inspired by `参考项目/agents-for-openbb/34-vanilla-agent-tables/` or `39-vanilla-agent-html-artifacts/`, use only shape ideas and do not import/copy runtime dependencies.

---

## 3. Target QMD files

Create/update QMD-owned files only:

```text
backend/app/notifications/__init__.py
backend/app/notifications/models.py
backend/app/notifications/service.py
backend/app/notifications/dedup.py
backend/app/reports/__init__.py
backend/app/reports/report_registry.py
backend/app/reports/report_builder.py
backend/app/db/migrations/**
specs/contracts/notification_report_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_notification_report_contract.py
tests/test_notifications.py
tests/test_report_runtime.py
tests/test_catalog.yaml
```

If final names differ, the PR must document the mapping.

---

## 4. Implementation plan

1. **Schema/runtime boundary**
   - Define or migrate `report_registry`, `report_section`, and `notification_log` if absent.
   - Do not bypass project migration/write governance. If migrations are required, use the existing migration registry path.

2. **Supported first event**
   - Implement exactly one supported input flow for the first vertical slice:
     - source-health failure, or
     - data-health WARN/FAIL, or
     - ResourceGuard breach.
   - Input event must be a structured QMD object, not free text.

3. **Report building**
   - Convert event into report registry/section state.
   - Include `source_id`, `domain`, `severity`, `facts_used`, `limitations`, `source_fetch_id`, `content_hash`, `schema_hash`, and `evidence_ids` when available.
   - If evidence is missing, report must include `missing_evidence` rather than inventing facts.

4. **Notification log**
   - Decide and implement dedup key boundary: `dedup_key` alone or `(dedup_key, as_of_date)`.
   - Implement cooldown/throttle in QMD-owned service.
   - Notification failure must not roll back report generation unless the contract explicitly says so.

5. **No-action notification copy**
   - Notification/report messages may say risk, warning, failure, needs review, or source unavailable.
   - They must not say buy/sell/add/reduce/position/order/trade action.

6. **Contract/test updates**
   - Update `notification_report_contract.yaml` to match implemented fields.
   - Update `contract_coverage.yaml` and `tests/test_catalog.yaml` for new tests.

---

## 5. Forbidden scope

- No SMS/webhook/email fan-out unless explicitly approved in a later task.
- No trading-action notifications.
- No report facts that are not backed by QMD evidence or explicit missing-evidence markers.
- No frontend notification center in this backend/schema task unless split into a separate task card.
- No direct production write outside approved report/notification persistence path.
- No import from `参考项目/**`.

---

## 6. Tests / gates

Required commands:

```bash
uv sync --locked
uv run pytest tests/test_notification_report_contract.py tests/test_notifications.py tests/test_report_runtime.py -q
uv run ruff check backend/app/notifications backend/app/reports tests
```

Test expectations:

- supported event creates a report entry;
- supported event creates or updates notification log state;
- duplicate event dedups according to contract;
- cooldown/throttle works;
- missing evidence is represented explicitly;
- notification failure does not corrupt report output;
- trading-action terms are rejected from notification/report text.

---

## 7. Done criteria

B04_04 is done only when one supported QMD event produces persisted/reportable report and notification state with tested dedup/cooldown behavior. Schema-only migrations or service-only shells are not acceptable.
