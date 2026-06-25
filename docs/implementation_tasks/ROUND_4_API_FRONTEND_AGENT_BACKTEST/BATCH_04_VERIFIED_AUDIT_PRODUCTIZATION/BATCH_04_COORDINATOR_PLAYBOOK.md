# Batch 04 Coordinator Playbook

## 0. Scope

Coordinate Round4 productization work from the canonical Batch 04 folder. Loose `024`–`030` files are historical inputs only.

Batch 04 may implement API, Agent, frontend, notifications/reports, and read-only backtest/review runtime. It must not introduce production writes or execution semantics.

## 1. Dispatch tracks

| Track                       | Card                                           | Suggested branch                             | Can run in parallel?                                                                      |
| --------------------------- | ---------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| API runtime/security        | `B04_01_api_runtime_security.md`               | `feature/round4-api-runtime-security`        | first; must produce a real read-only endpoint, not router-only scaffolding                |
| Agent policy runtime        | `B04_02_agent_policy_runtime.md`               | `feature/round4-agent-policy-runtime`        | after API contracts are stable enough; must include one allowed read-only tool            |
| Frontend routes/pages       | `B04_03_frontend_error_boundary_and_routes.md` | `feature/round4-frontend-routes`             | after route contracts or with deferred states; must include one API-bound panel/page      |
| Notification/report runtime | `B04_04_notification_report_runtime.md`        | `feature/round4-notification-report-runtime` | parallel after API/report contracts; must include one event-to-log/report flow            |
| Backtest/review runtime     | `B04_05_backtest_review_runtime.md`            | `feature/round4-backtest-review-runtime`     | after 3F-R `R3FR-04` planning is complete; must include one executable read-only scenario |

## 2. Required cross-reading

Every Batch 04 branch must read:

- `PROJECT_IMPLEMENTATION_ROADMAP.md` §1.4 and Round4
- `BATCH_04_TASK_CARD_MANIFEST.md`
- `BATCH_04_HARDENING_RULES.md`
- the relevant `B04_*` card
- loose historical card(s) mapped by the manifest

Backtest/review branches must additionally read:

- `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`
- `参考项目/JQ2PTrade/README.md`
- `参考项目/JQ2PTrade/api_mapping.json`
- relevant JQ2PTrade `ptrade_local/**` files
- relevant EasyXT `easyxt_backtest/**` files after forbidden-symbol review

## 3. File locks

Avoid parallel edits to:

- `docs/modules/backtest_review_lifecycle.md`
- `specs/contracts/review_sandbox_contract.yaml`
- `backend/app/agent_tools/**`
- `backend/app/review/**`
- shared API contract files
- shared frontend API client files

## 4. Reference-adoption rule

If a branch implements any of the following from scratch, it must include an ADR:

- backtest engine/data loader/report builder
- Agent analyst/workflow/report artifact pattern
- dashboard/chart/table/PDF artifact pattern
- provider/source metadata surfacing

Without ADR, adapt the relevant reference project as required by roadmap §1.4.

## 5. Batch close criteria

Batch 04 closes only when:

- canonical cards, not loose cards, are the execution entrypoints;
- every B04 card has produced a real first vertical slice, not only a shell, deferred UI, policy note, or schema-only artifact;
- no module plan requires more than three implementation batches to full production-stable supported scope;
- API/Agent/frontend/report/backtest outputs remain read-only and bounded;
- no action/execution semantics are exposed;
- backtest/review follows JQ2PTrade/EasyXT adoption planning;
- frontend/Agent artifact work has either adopted or ADR-deferred relevant reference examples;
- tests and docs identify failure meaning for new gates.
