# Batch 04 — Verified Audit Productization Gaps

> Roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 4.  
> Scope: API, frontend, Agent, notification/report, and backtest/review findings from verified audit.  
> Production posture: read-only/productization first; no direct DB write by Agent/UI; no trading action semantics.

---

## 1. Owned verified audit findings

| Card                                           | Owns                     | Round4 batch |
| ---------------------------------------------- | ------------------------ | ------------ |
| `B04_01_api_runtime_security.md`               | `VR-API-001`             | 4.1          |
| `B04_02_agent_policy_runtime.md`               | `VR-AGENT-001`           | 4.2          |
| `B04_03_frontend_error_boundary_and_routes.md` | `VR-FE-001`, `VR-FE-002` | 4.3          |
| `B04_04_notification_report_runtime.md`        | `VR-NOTIF-001`           | 4.4          |
| `B04_05_backtest_review_runtime.md`            | `VR-BT-001`              | 4.5          |

---

## 2. Parallel rules

- API security can start before frontend pages.
- Frontend route shells may render deferred states before APIs exist, but must not fake data.
- Agent runtime policy must exist before exposing Agent endpoints.
- Notification/report schema/runtime should not block API source list work.
- Backtest/review is read-only and must not output trade recommendations.
