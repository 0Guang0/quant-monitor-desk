# Logging Guidelines

> How logging is done in this project.

---

## Overview

<!--
Document your project's logging conventions here.

Questions to answer:
- What logging library do you use?
- What are the log levels and when to use each?
- What should be logged?
- What should NOT be logged (PII, secrets)?
-->

(To be filled by the team)

---

## Log Levels

<!-- When to use each level: debug, info, warn, error -->

(To be filled by the team)

---

## Structured Logging

<!-- Log format, required fields -->

(To be filled by the team)

---

## What to Log

<!-- Important events to log -->

(To be filled by the team)

---

## What NOT to Log

<!-- Sensitive data, PII, secrets -->

**Persisted error text (Batch C/D policy):** Any user- or vendor-facing error string written to durable stores must pass through `backend.app.util.error_redaction.redact_error_message` before INSERT/UPDATE.

| Sink | Module | When |
|------|--------|------|
| `fetch_log.error_message` | `FetchLogWriter` | Batch C |
| `write_audit_log` detail fields | write manager | Batch C |
| `job_event_log.message` | `backend.app.sync.jobs` (`_safe_event_message`) | Batch D Repair |

**Orchestrator transitions:** `SyncJobManager.transition(..., error_message=...)` and `emit_custom_event(..., message=...)` redact at write time. Do not bypass with raw exception strings.

**Tests:** `tests/test_sync_orchestrator.py::test_orchestrator_fetchFailure_redactsErrorInJobEventLog`

**Deferred (Round 3 API):** When `job_event_log` is exposed via HTTP, apply operator-only field ACL — see `BATCH_D_STATUS.md` D-A6-1.
