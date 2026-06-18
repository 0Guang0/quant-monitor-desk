# Logging Guidelines

> Backend logging and operator messaging (Round 0–2).

## Overview

- Structured persistence: `resource_guard_log`, `write_audit_log`, `fetch_log`, `job_event_log`.
- Operator stderr banners for PAUSE/HARD_STOP via `format_pause_event`.
- Secrets redacted in error messages via `redact_error_message`.

## Required Patterns

| Event | Destination |
|---|---|
| ResourceGuard PAUSE/HARD_STOP | stderr banner + optional `resource_guard_log` row |
| Write success/failure | `write_audit_log` with validation/conflict status |
| Fetch outcomes | `fetch_log` via adapter skeleton |
| Sync transitions | `job_event_log` via `SyncJobStateMachine` |

## Forbidden Patterns

- Logging raw tokens, passwords, API keys in `error_message` fields.
- Silent swallow of validation failures without audit row.

## Testing

- ResourceGuard tests assert log row count for PAUSE/HARD_STOP.
- WriteManager tests assert audit status on FAILED paths.
