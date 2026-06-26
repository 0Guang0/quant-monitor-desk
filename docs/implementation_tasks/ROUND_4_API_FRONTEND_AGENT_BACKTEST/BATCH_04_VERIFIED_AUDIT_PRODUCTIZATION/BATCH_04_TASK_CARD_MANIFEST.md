# Batch 04 Task Card Manifest — API / Frontend / Agent / Backtest Productization

> **Canonical batch folder:** `docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/`  
> **Roadmap:** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 4.  
> **Round3H gate:** Batch04 cannot start until R3H-05 returns `PASS_ROUND4_REAL_DATA_READY` or `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR`; `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` blocks this manifest.  
> **Global reference rule:** `PROJECT_IMPLEMENTATION_ROADMAP.md` §1.4 applies to backtest, Agent, UI artifact, and provider-facing work.  
> **Historical input cards:** loose `024`–`030` files remain source material, not the default execution entrypoint.

---

## 1. Canonical Batch 04 cards

| Card                                           | Round segment   | Owns / source                                      | Business outcome                                                                                                      | Reference-adoption requirement                                                                                              |
| ---------------------------------------------- | --------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `B04_01_api_runtime_security.md`               | Round 4.1 track | `VR-API-001`, loose `024`                          | first real read-only API vertical slice: source/capability/readiness endpoint with auth, pagination, and query budget | Provider/source APIs must use QMD registry/capability contracts; no free SQL                                                |
| `B04_02_agent_policy_runtime.md`               | Round 4.2 track | `VR-AGENT-001`, loose `025`, loose `030`           | runtime agent tool policy plus one policy-guarded read-only tool                                                      | Agent/UI artifacts must evaluate TradingAgents / TradingAgents-astock / agents-for-openbb before from-scratch design        |
| `B04_03_frontend_error_boundary_and_routes.md` | Round 4.3 track | `VR-FE-001`, `VR-FE-002`, loose `026`, loose `027` | frontend shell plus one API-bound dashboard/readiness page; deferred states only for non-owned pages                  | Dashboard widgets/artifacts should evaluate agents-for-openbb examples where relevant                                       |
| `B04_04_notification_report_runtime.md`        | Round 4.4 track | `VR-NOTIF-001`, loose `028`                        | one event → report/notification_log runtime flow with dedup/cooldown                                                  | Report/artifact format should reuse established QMD evidence and reference artifact patterns where suitable                 |
| `B04_05_backtest_review_runtime.md`            | Round 4.5 track | `VR-BT-001`, loose `029`, 3F-R `R3FR-04`           | one executable read-only review scenario and report artifact                                                          | Must adapt JQ2PTrade MiniPTrade DuckDB loader/report lifecycle and evaluate EasyXT backtest metrics; no blank engine design |

---

## 2. Historical loose task mapping

| Loose card                                   | Canonical Batch 04 owner                                                 | Status                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| `024_implement_fastapi_routes.md`            | `B04_01_api_runtime_security.md`                                         | historical input                                                    |
| `025_implement_agent_tool_layer.md`          | `B04_02_agent_policy_runtime.md`                                         | historical input                                                    |
| `026_implement_frontend_shell.md`            | `B04_03_frontend_error_boundary_and_routes.md`                           | historical input                                                    |
| `027_implement_frontend_layer_pages.md`      | `B04_03_frontend_error_boundary_and_routes.md`                           | historical input                                                    |
| `028_implement_reports_and_notifications.md` | `B04_04_notification_report_runtime.md`                                  | historical input                                                    |
| `029_implement_backtest_and_review.md`       | `B04_05_backtest_review_runtime.md`                                      | historical input; must be read with roadmap §1.4 and 3F-R `R3FR-04` |
| `030_implement_no_action_semantics_guard.md` | `B04_02_agent_policy_runtime.md` and `B04_05_backtest_review_runtime.md` | historical input                                                    |

---

## 3. Required execution order

1. API runtime/security (`B04_01`) before frontend depends on live API responses; it must expose at least one real read-only source/capability/readiness endpoint.
2. Agent runtime policy (`B04_02`) before exposing any agent endpoints; it must include at least one allowed read-only tool and one forbidden-tool rejection path.
3. Frontend shell/routes (`B04_03`) can run with deferred states but must include one API-bound page or panel and must not fake data.
4. Notification/report runtime (`B04_04`) can run after API/report contracts are stable; it must include one event-to-report/log vertical flow.
5. Backtest/review runtime (`B04_05`) must wait for 3F-R `R3FR-04` planning updates and must follow roadmap §1.4; it must include one read-only review scenario.

---

## 4. Batch 04 acceptance

Batch 04 is complete only when:

- canonical cards are used as execution entrypoints;
- loose cards have redirect/pointer notes or are clearly historical inputs;
- Agent, UI, and backtest work comply with roadmap §1.4;
- each canonical card delivers a real first vertical slice, not only a shell, contract note, or deferred route;
- no module is planned beyond three implementation batches to full production-stable supported scope;
- no agent/frontend path bypasses read-only API contracts;
- no runtime exposes execution instructions or broker-side actions;
- backtest/review uses QMD evidence/frozen data contracts and adapts JQ2PTrade/EasyXT patterns where applicable.
