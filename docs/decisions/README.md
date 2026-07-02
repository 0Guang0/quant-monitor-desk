# Architecture Decision Records

| ADR                                                                   | Title                                                             |
| --------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [ADR-001](ADR-001-ingestion-validation-write-transaction-boundary.md) | Ingestion validation / write transaction boundary                 |
| [ADR-002](ADR-002-db-check-vs-app-validation.md)                      | DB CHECK vs application-layer validation                          |
| [ADR-003](ADR-003-implementation-path-mapping.md)                     | Implementation path mapping (task docs vs code)                   |
| [ADR-024](ADR-024-source-health-snapshot-boundary.md)                 | source_health_snapshot boundary (Batch 3F)                        |
| [ADR-025](ADR-025-r3h10-sync-fail-closed-datasource-service.md)       | Sync production fail-closed without `datasource_service` (R3H-10) |
| [ADR-026](ADR-026-r3h07-us-trading-calendar-ssot.md)                  | US equity trading calendar SSOT — `trading_sessions` (R3H-07)     |
| [ADR-028](ADR-028-dcp05-tier-a-clean-domain-extension.md)             | DCP-05 Tier A clean domain extension                              |
| [ADR-029](ADR-029-dcp06-layer1-five-axis-clean-read.md)               | DCP-06 Layer1 five-axis clean read                                |
| [ADR-032](ADR-032-dcp07-layer2-vix-clean-read.md)                     | DCP-07 Layer2 L2-VIX clean read (VIXCLS / axis_observation)       |

Ponytail audit equivalence: this project uses the `ponytail-review` / `code-simplification` skills as the formal simplification audit path when the standalone `ponytail` CLI is unavailable (Round2 audit P3-04).
