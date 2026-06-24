# Batch 01 Hardening Rules

> Applies to every new and legacy task card included in `BATCH_01_MODEL_SOURCE_READINESS`.  
> These rules are mandatory. If they conflict with a legacy card, the stricter safety rule wins.

---

## 1. Canonical execution rule

Every executor must treat the batch as a controlled source-readiness package, not a production-entry package.

Allowed output language:

- `model input whitelist established`
- `raw/staging evidence collected`
- `sandbox evidence collected`
- `source readiness assessed`
- `validation-only candidate evaluated`
- `eligible for later sandbox clean-write rehearsal` only when the relevant card explicitly permits that wording

Forbidden output language:

- `production-live ready`
- `production clean write enabled`
- `full-market ingestion complete`
- `full-history backfill complete`
- `TDX production primary enabled`
- `FRED production source enabled`
- `AkShare primary source enabled`
- `Layer2/3/4 production data fully connected`

---

## 2. Legacy-card conflict rule

Legacy cards are included for context and historical constraints. They are not authorization to bypass new batch gates.

When a legacy card and a new card differ:

1. Use the stricter source-safety rule.
2. Use the smaller cap unless the user explicitly approves a larger cap.
3. Preserve disabled-by-default and validation-only statuses.
4. Preserve no-production-write rules.
5. Record the conflict in task evidence.

Examples:

- Legacy `018C` may mention small TDX probe caps; the new addendum may mention broader candidate shape. Use the smaller cap unless authorized.
- Legacy v2 pilot can guide staged evidence format; v3 must still be whitelist-driven.
- Legacy data health v1 can guide checks; v2 still cannot create `source_health_snapshot`.

---

## 3. Authorization rule

Live source access is not implied by a task card.

Before any live fetch, evidence must contain:

```yaml
authorization_present: true
authorized_by: user | coordinator
authorized_at: iso timestamp or documented session
source_id: string
domain: string
operation: string
symbols_or_series: list
window: string
max_rows: integer
max_calls: integer
write_target: raw_or_staging_or_sandbox
allow_production_clean_write: false
```

If this evidence is absent, the task must run mocked/dry-run checks or return an explicit `FAIL_AUTH` / `BLOCKED_AUTH` / `REDEFERRED` status.

---

## 4. Registry closure rule

Deferred rows may not be closed by similarity, sidecar evidence, or a different source.

Closure requires:

- exact row ID,
- exact required source/domain/operation,
- exact evidence path,
- tests or report proving the closure criterion,
- registry update or explicit re-defer with owner/phase/closure test.

Specific hardening:

- `B2.5-O-05` requires FRED-only evidence. `macro_supplementary` is insufficient.
- `R3-B2.75-REQ2-EM` cannot close merely because TDX or Sina works.
- `R3-PROMPT14-AKSHARE-VAL-01` cannot close unless AkShare validation-only behavior is proven or explicitly re-deferred.

---

## 5. Source role rule

No task in Batch 01 may promote source roles beyond this table:

| Source          | Maximum allowed Batch 01 role                                      |
| --------------- | ------------------------------------------------------------------ |
| `baostock`      | sandbox/raw primary candidate for selected A-share daily bars only |
| `cninfo`        | sandbox/raw metadata candidate only                                |
| `akshare`       | validation-only                                                    |
| `fred`          | authorized sandbox/raw candidate only                              |
| `tdx_pytdx`     | disabled-by-default validation-only candidate                      |
| `qmt_xtdata`    | disabled/deferred unless separate user authorization task exists   |
| `qmt_xqshare`   | disabled/deferred unless separate user authorization task exists   |
| `yahoo_finance` | disabled/deferred unless separate validation-only task exists      |

---

## 6. Data-scope rule

Batch 01 cannot default to broad ingestion.

Maximum default behavior:

- model-input whitelist only,
- bounded symbols/issuers/series,
- bounded rows,
- bounded network calls,
- raw/staging/sandbox paths only.

Forbidden default behavior:

- full A-share scan,
- all US equities,
- all ETFs,
- all futures/options,
- full FRED catalog,
- all cninfo PDFs,
- all history,
- minute/tick data,
- scheduled production polling.

---

## 7. Evidence rule

Every successful source/evidence-producing task must emit or verify:

- `source_id`,
- `domain`,
- `operation`,
- `symbol_or_series`,
- request window,
- row count,
- cap status,
- `source_fetch_id`,
- `content_hash`,
- `as_of_timestamp` or `retrieved_at`,
- relative evidence path,
- production DB no-mutation or no-open statement,
- source role used at the time of collection.

---

## 8. Testing rule

Every new or changed test must explain:

- coverage scope,
- test object,
- purpose/goal.

Tests must assert business safety, not only implementation shape. Required negative tests include:

- AkShare cannot become Primary.
- TDX cannot become production primary.
- FRED cannot be marked production-ready by macro_supplementary.
- Missing authorization blocks live fetch.
- Missing evidence blocks sandbox-clean eligibility.
- Source conflict summary cannot write clean table.

---

## 9. Stop-and-escalate rule

Stop and ask for user/coordinator approval if implementation requires:

- new external dependency,
- live API key or credential,
- broader row/symbol/window cap,
- production DB access,
- clean table write,
- migration,
- full-market/full-history scan,
- changing source role semantics,
- closing a registry row without exact source evidence.

---

## 10. Batch audit status

These rules are the required hardening output of the first Batch 01 adversarial audit. Future executors must cite this file in their plan and closeout evidence.
