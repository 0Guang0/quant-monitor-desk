# Architecture Decision Records

| ADR                                                                   | Title                                                             |
| --------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [ADR-001](ADR-001-ingestion-validation-write-transaction-boundary.md) | Ingestion validation / write transaction boundary                 |
| [ADR-002](ADR-002-db-check-vs-app-validation.md)                      | DB CHECK vs application-layer validation                          |
| [ADR-003](ADR-003-implementation-path-mapping.md)                     | Implementation path mapping (task docs vs code)                   |
| [ADR-024](ADR-024-source-health-snapshot-boundary.md)                 | source_health_snapshot boundary (Batch 3F)                        |
| [ADR-025](ADR-025-r3h10-sync-fail-closed-datasource-service.md)       | Sync production fail-closed without `datasource_service` (R3H-10) |
| [ADR-026](ADR-026-r3h07-us-trading-calendar-ssot.md)                  | US equity trading calendar SSOT — `trading_sessions` (R3H-07)     |
| [ADR-030](ADR-030-bounded-backfill-cap-and-ci-nightly.md)             | Bounded backfill cap + CI nightly layering (R3-DCP-09)            |

Ponytail audit equivalence: this project uses the `ponytail-review` / `code-simplification` skills as the formal simplification audit path when the standalone `ponytail` CLI is unavailable (Round2 audit P3-04).
