# Production Live Pilot Policy

> Applies to Round 3 Batch 2.75 (`R3-B2.75-PROD-LIVE-PILOT`) and any future task that attempts to touch live/production data before formal production release.
>
> This policy permits a narrow live-data pilot only when it is explicitly authorized, sandbox-first, evidence-rich, and fail-closed. It does not enable production data by default.

## 1. Policy intent

Production/live data is useful because it exposes source drift, missing fields, timestamp differences, vendor failures, validation gaps, conflict behavior, and lineage defects that fixture or staged data can hide.

The pilot must expose those issues without polluting clean production DB state, without bypassing source authorization, and without letting staged evidence be promoted to production-live readiness.

## 2. Default stance

| Control                                | Default                                             |
| -------------------------------------- | --------------------------------------------------- |
| Live source access                     | Disabled                                            |
| QMT/xqshare/Yahoo/FRED                 | Disabled unless explicitly authorized for the pilot |
| `dry_run`                              | `true`                                              |
| `raw_only`                             | `true` for the first live pass                      |
| `write_target`                         | `sandbox`                                           |
| `allow_clean_write`                    | `false`                                             |
| Production clean DB mutation           | Forbidden                                           |
| Full-market/full-history/backfill      | Forbidden                                           |
| Silent fallback to fixture/staged data | Forbidden                                           |

## 3. Authorization requirements

A live pilot must fail closed unless the task evidence records all fields below:

| Field                    | Requirement                                                                   |
| ------------------------ | ----------------------------------------------------------------------------- |
| `source_id`              | Exactly one source unless the Trellis plan explicitly names a tiny allowlist. |
| `data_domain`            | Exactly one domain.                                                           |
| `operation`              | Exactly one operation.                                                        |
| `symbols_or_indicators`  | One indicator/instrument by default.                                          |
| `as_of` or `date_window` | Single date or short bounded window.                                          |
| `max_rows`               | Hard row cap; target default `<= 100`.                                        |
| `dry_run`                | Must default to `true`.                                                       |
| `raw_only`               | Must default to `true` for the first live pass.                               |
| `write_target`           | Must default to `sandbox`.                                                    |
| `allow_clean_write`      | Must default to `false`; if changed, sandbox-only.                            |
| `authorization_evidence` | Human-readable path or config marker proving user approval.                   |

## 4. Source restrictions

1. QMT and xqshare must remain disabled by default.
2. Yahoo must remain auxiliary/validation-only unless a future policy changes its role.
3. FRED primary live access for `ENV-E1-DGS10` remains deferred until the pilot records user authorization and evidence.
4. Akshare or other aggregators may be useful for small-shape pilots but must not be treated as sole authoritative production primary when the relevant source registry says otherwise.
5. A route/capability result of `DISABLED_SOURCE`, `CAPABILITY_MISSING`, `USER_AUTH_REQUIRED`, or ResourceGuard failure stops the pilot.

## 5. Required phase gates

### Phase 0 — authorization

- Record the exact source/domain/operation/window/row cap/write target.
- Record why the selected source is appropriate for the first pilot.
- Record user authorization evidence.

### Phase 1 — read-only baseline

- Capture read-only DB inventory.
- Capture data-root inventory.
- Capture source registry/capability status.
- Prove no production DB mutation.

### Phase 2 — dry-run route gate

- Route preview happens before fetch.
- Selected route must be `READY`.
- No fixture/staged fallback can satisfy this phase.

### Phase 3 — raw-only micro-fetch

- First live fetch is raw-only.
- Raw evidence writes only to sandbox-controlled paths or equivalent sandbox evidence stores.
- Evidence includes source, request parameters, content hash, fetch timestamp, raw path, file registry row, and fetch log row.
- Production clean DB remains unchanged.

### Phase 4 — sandbox validation and optional clean write

- Validation must pass before clean write.
- Source conflicts or severe validation failures block clean write.
- WriteManager is the only allowed clean write boundary.
- Clean write target is sandbox DB or isolated sandbox schema only.
- Snapshot lineage must use real fetch IDs/content hashes.
- Synthetic lineage is forbidden for a production/live pilot.

### Phase 5 — closeout

- End with an explicit pilot state.
- Update `docs/AUDIT_DEFERRED_REGISTRY.md` and `docs/UNRESOLVED_ISSUES_REGISTRY.md`.
- Do not close broad Batch 6 production items from pilot evidence alone.

## 6. Evidence checklist

A closed pilot must preserve:

- Authorization evidence.
- Source/capability snapshot.
- Route preview JSON.
- ResourceGuard decision.
- DB/data-root before inventory.
- Raw file evidence and content hash.
- `file_registry` evidence.
- `fetch_log` evidence.
- Validation report.
- Conflict report or explicit no-conflict evidence.
- Sandbox write audit and lineage evidence, if clean write is enabled.
- Production DB after inventory proving no mutation.
- Registry update or explicit re-deferral.

## 7. Promotion rule

Passing Batch 2.75 does not mean formal production data access is open.

A passing pilot may allow Batch 3–5 to reference real source-shape evidence, but formal production release still belongs to Batch 6 closeout: production CLI, backfill/reconcile closure, source health, migration/check coverage, packaging, runbook, and full regression evidence.

## 8. Verification

Planning and policy changes must be covered by:

```bash
pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q
```

Future implementation must add tests that prove:

- No authorization means no live fetch.
- Disabled source means no live fetch.
- Route not `READY` means no live fetch.
- First pass is raw-only.
- Sandbox target is enforced.
- Production DB row counts are unchanged.
- No fixture/staged fallback satisfies live pilot evidence.
