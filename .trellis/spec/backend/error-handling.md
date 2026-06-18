# Error Handling Guidelines

> Backend error semantics and logging (Round 0–2).

## Overview

- Domain errors use typed exceptions (`ValidationRejected`, `InvalidRegistryError`, etc.).
- User/operator facing messages redacted via `redact_error_message`.
- Resource pauses emit stderr banner via `format_pause_event`.

## Patterns

| Layer | Pattern |
|---|---|
| ValidationGate | `ValidationRejected` / `ValidationGateError` → failed write + audit |
| WriteManager | DuckDB errors → ROLLBACK + FAILED audit when `own_transaction=True` |
| ResourceGuard | PAUSE/HARD_STOP logged to `resource_guard_log` when `con` provided |
| Adapters | Map port errors to `FetchResult.status` + `fetch_log` row |

## Broad Exception Policy

`except Exception` allowed only when:
1. Re-raising after ROLLBACK (WriteManager outer safety net), or
2. Logging resource guard failure after ROLLBACK, or
3. Migration wrapper with explicit ROLLBACK (migrate.py).

Prefer catching `duckdb.Error`, `OSError`, `yaml.YAMLError` where possible.

## Testing

- Failure-path tests must assert audit row status and clean row count unchanged.
- Do not swallow validation failures silently.
