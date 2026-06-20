# 018B — Production Live Pilot Gate

> Round 3 Batch 2.75 · controlled production/live-data pilot after Batch 2.5 and before Batch 3.
>
> Status: planning task card. This file defines the gate for a future implementation task; it does not enable any live source, network fetch, CLI, or clean production DB write by itself.

## 1. Goal

Run one strictly scoped, user-authorized live-data pilot after the Batch 2.5 Layer 1 observation ingestion bridge and before Batch 3 downstream modeling consumes production-facing assumptions.

The pilot exists to expose real source issues—schema drift, timestamp formats, missing values, route/capability mismatch, raw evidence gaps, validation behavior, conflict behavior, and lineage gaps—without polluting clean production DB state.

## 2. Non-goals

- No full-market fetch.
- No full-history fetch.
- No backfill or broad reconcile execution.
- No default enablement of QMT, xqshare, Yahoo, FRED, or any user-authorized source.
- No direct mutation of `data/duckdb/quant_monitor.duckdb`.
- No production CLI scope expansion beyond the pilot gate.
- No silent fallback from a live source to a staged fixture.
- No promotion of Batch 2.5 staged evidence to production-live readiness.

## 3. Required authorization input

The implementation must fail closed unless a user-authorized pilot request explicitly declares all fields below:

| Field                    | Requirement                                                                             |
| ------------------------ | --------------------------------------------------------------------------------------- |
| `source_id`              | One source only. Must not be enabled by default solely because this task exists.        |
| `data_domain`            | One domain only.                                                                        |
| `operation`              | One operation only.                                                                     |
| `symbols_or_indicators`  | One indicator/instrument by default; small allowlist only if the plan names every item. |
| `as_of` or `date_window` | Single date or very short bounded window.                                               |
| `max_rows`               | Hard cap; default target is `<= 100`.                                                   |
| `dry_run`                | Must default to `true`.                                                                 |
| `raw_only`               | Must default to `true` for the first live pass.                                         |
| `write_target`           | Must default to `sandbox`.                                                              |
| `allow_clean_write`      | Must default to `false`; if true, clean write is sandbox-only.                          |
| `authorization_evidence` | Human-readable evidence path or explicit config marker proving user approval.           |

## 4. Phase 0 — authorization and source selection

Acceptance criteria:

1. The Trellis plan names the exact source, domain, operation, symbol/indicator, date/window, row cap, and sandbox target.
2. The plan states why the chosen source is lower risk than QMT/xqshare/Yahoo/FRED for the first pilot, or explains why a higher-risk source is necessary.
3. QMT/xqshare/Yahoo/FRED remain disabled unless the user explicitly authorizes that source for this pilot.
4. The pilot cannot proceed if authorization evidence is absent.

## 5. Phase 1 — read-only baseline

Acceptance criteria:

1. Capture read-only DB inventory before the pilot.
2. Capture data-root inventory before the pilot.
3. Capture source registry and source capability status for the selected source/domain/operation.
4. Prove the target production DB is not mutated in this phase.

Required evidence:

- DB inspect output.
- Data-root inventory output.
- Source registry/capability snapshot.
- No-mutation proof.

## 6. Phase 2 — route and capability dry-run

Acceptance criteria:

1. Route preview must be executed before any live fetch.
2. Route status must be `READY` for the selected source/domain/operation.
3. `DISABLED_SOURCE`, `CAPABILITY_MISSING`, `USER_AUTH_REQUIRED`, or ResourceGuard failure must stop the pilot.
4. No fallback to fixture/staged data may satisfy this phase.

Required evidence:

- Route preview JSON.
- Capability check result.
- ResourceGuard decision.
- Failure evidence if the pilot stops.

## 7. Phase 3 — raw-only live micro-fetch

Acceptance criteria:

1. Fetch writes only to sandbox raw/file-registry/fetch-log targets.
2. The first live pass is `raw_only=true`.
3. Raw evidence must include `source_used`, `data_domain`, `operation`, request parameters, content hash, and fetch timestamp.
4. The production clean DB remains unchanged.
5. Any network/source failure is captured as evidence and does not trigger clean write.

Required evidence:

- Raw file path(s).
- `file_registry` row(s) in sandbox or equivalent evidence store.
- `fetch_log` row(s) in sandbox or equivalent evidence store.
- Content hash(es).
- Before/after DB inspect delta proving no production clean mutation.

## 8. Phase 4 — sandbox validation and optional clean write

Acceptance criteria:

1. Validation must run against raw pilot evidence before any clean write.
2. Severe validation failure or unresolved source conflict blocks clean write.
3. Any clean write must use WriteManager only.
4. Any clean write must target sandbox DB or an isolated sandbox schema only.
5. Snapshot lineage must use real pilot fetch IDs/content hashes; synthetic lineage is not allowed for a production/live pilot.
6. The production target DB remains unchanged unless a later Batch 6 production release explicitly authorizes it.

Required evidence:

- Validation report.
- Conflict report or explicit no-conflict result.
- Write audit row(s), if sandbox clean write is enabled.
- Snapshot lineage rows, if sandbox snapshots are enabled.
- Before/after row-count deltas for sandbox and production targets.

## 9. Phase 5 — decision and handoff

The pilot ends in exactly one of these states:

| State                      | Meaning                                                                 | Required follow-up                                                                               |
| -------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `PILOT_PASS_RAW_ONLY`      | Live raw fetch succeeded; clean write not attempted.                    | Batch 3 may reference pilot raw-shape evidence, but production clean readiness remains deferred. |
| `PILOT_PASS_SANDBOX_CLEAN` | Live raw fetch, validation, sandbox clean write, and lineage succeeded. | Batch 3 may reference pilot evidence; Batch 6 still owns formal production release.              |
| `PILOT_FAIL_SOURCE`        | Route/capability/fetch/source failed.                                   | Record source limitation and keep downstream modeling staged.                                    |
| `PILOT_FAIL_VALIDATION`    | Fetch succeeded but validation/conflict blocked clean write.            | Add data-quality or mapping closure task before production release.                              |
| `PILOT_REDEFERRED`         | User did not authorize live pilot or source is unsuitable.              | Keep Batch 2.5 staged semantics and preserve registry deferral.                                  |

## 10. Required registry updates

On closeout, update both registries consistently:

- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

If the pilot passes, add evidence to `docs/RESOLVED_ISSUES_REGISTRY.md` only for the exact pilot item closed. Do not close broad Batch 6 production CLI/backfill/reconcile/source-health items unless those items have their own implementation and tests.

## 11. Verification commands

The planning-only gate must start with document/policy tests:

```bash
pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q
```

The future implementation task must add focused implementation tests before any live source is enabled. Those tests must prove fail-closed authorization, sandbox-only writes, no fixture fallback, row/window caps, and no production DB mutation.
