# Batch 04 — Verified Audit Productization Gaps

> Roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 4, with global reference-adoption rule §1.4.  
> Scope: API, frontend, Agent, notification/report, and backtest/review findings from verified audit.  
> Production posture: read-only/productization first; no direct DB write by Agent/UI; no trading action semantics.  
> Canonical batch package: this folder. Loose `024`–`030` cards are historical inputs unless explicitly referenced by a Batch 04 card.

---

## 1. Owned verified audit findings

| Card                                           | Owns                     | Round4 track                          |
| ---------------------------------------------- | ------------------------ | ------------------------------------- |
| `B04_01_api_runtime_security.md`               | `VR-API-001`             | API runtime/security                  |
| `B04_02_agent_policy_runtime.md`               | `VR-AGENT-001`           | Agent policy + first read-only tool   |
| `B04_03_frontend_error_boundary_and_routes.md` | `VR-FE-001`, `VR-FE-002` | Frontend shell + first API-bound page |
| `B04_04_notification_report_runtime.md`        | `VR-NOTIF-001`           | Notification/report event flow        |
| `B04_05_backtest_review_runtime.md`            | `VR-BT-001`              | Backtest/review first scenario        |

---

## 2. Parallel rules

- API security can start before frontend pages, but `B04_01` must deliver a real read-only HTTP vertical slice rather than only router scaffolding.
- Frontend route shells may render deferred states before every API exists, but `B04_03` must bind at least one real API-backed page or panel and must not fake success data.
- Agent runtime policy must exist before exposing Agent endpoints, and `B04_02` must include at least one policy-guarded read-only tool so the first Agent batch is not policy-only.
- Notification/report schema/runtime should not block API source list work, but `B04_04` must implement one event → report/notification_log flow rather than schema-only migration.
- Backtest/review is read-only and must not output execution instructions; `B04_05` must implement at least one executable read-only review scenario.
- Backtest/review must first read roadmap §1.4 and 3F-R `R3FR-04`, then adapt JQ2PTrade MiniPTrade DuckDB loader/report lifecycle and EasyXT performance/report ideas behind QMD no-action semantics.
- Agent/UI artifact work must first evaluate TradingAgents / TradingAgents-astock / agents-for-openbb as reference material, or write an ADR explaining why adaptation is not viable.

## 3. Anti-overengineering closure rule

Batch 04 has five productization tracks, but they are not permission to keep a module in five small batches. For each module, this canonical card is the first implementation batch and must produce a real minimum vertical slice. Any follow-up may use at most two more batches: one to complete the declared production-stable supported scope and one for hardening/regression/release gates.
