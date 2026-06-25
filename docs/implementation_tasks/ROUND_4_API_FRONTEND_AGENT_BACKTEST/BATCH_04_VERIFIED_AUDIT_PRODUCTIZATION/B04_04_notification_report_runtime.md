# B04_04 — Notification and Report Runtime

> Owns: `VR-NOTIF-001`.  
> Roadmap: Round 4.4.  
> Suggested branch: `feature/round4-notification-report-runtime`.  
> Parallel: can run after schema ownership is clear; does not block API source list.

---

## Goal

Implement the minimum notification/report runtime and schema plan needed to make notification/report contracts enforceable.

## Scope

- Define or migrate `report_registry`, `report_section`, and `notification_log` if still absent.
- Decide dedup unique boundary: `dedup_key` alone or `(dedup_key, as_of_date)`.
- Implement minimal `NotificationService`: alert event → dedup/cooldown/throttle → notification_log.
- Add tests for dedup, cooldown, notification failure, facts/evidence traceability.

## Forbidden scope

- No SMS/webhook/email fan-out unless explicitly approved.
- No trading-action notifications.
- No notification failure should roll back report generation unless contract says so.
- No frontend notification center work in this backend/schema branch unless split.

## Gates

```bash
uv sync --locked
uv run pytest tests/test_notification_report_contract.py tests/test_notifications.py -q
uv run ruff check backend/app/notifications tests
```

## Done criteria

- `VR-NOTIF-001` resolved or precisely re-deferred.
- Notification/report schema and runtime state are no longer contract-only.
- Dedup/cooldown behavior is testable.
