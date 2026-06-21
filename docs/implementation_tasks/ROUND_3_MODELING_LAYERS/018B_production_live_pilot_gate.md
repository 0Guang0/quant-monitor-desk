# 018B — Production Live Pilot Gate

> Round 3 Batch 2.75 · controlled production/live-data pilot after Batch 2.5 and before Batch 3.
>
> Status: planning task card. This file defines the gate for a future implementation task; it does not enable any live source, network fetch, CLI, or clean production DB write by itself.

## 0. Batch 2.75 scope ledger

Batch 2.75 必须把以下项纳入同一个 Trellis MASTER/AUDIT 计划，并逐项给出 acceptance criterion、evidence、registry closeout 或 explicit re-deferral：

| Item / alias                                 | 必须处理的内容                                                                                                                                      | Batch 2.75 关闭方式                                                                                                     |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `R3-B2.75-PROD-LIVE-PILOT`                   | 受控 production/live-data pilot 本体：授权、只读 baseline、route dry-run、raw-only micro-fetch、sandbox validation、可选 sandbox-only clean write。 | 产出 pilot outcome 与证据包；不得直接打开正式 production data access。                                                  |
| `R3-B2.75-01` / `GLOBAL-P2-01` / `B2.5-O-05` | Batch 2.5 仍为 staged-only，外部真实源 controlled live pilot 未执行。                                                                               | 执行 pilot 并记录 `PILOT_*` 结果，或在 registry 中明确 re-defer 到后续 phase、owner 与 closure test。                   |
| `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`    | A6 production-equivalent benchmark / performance-budget evidence artifact 未刷新。                                                                  | 在 bounded、non-full-market 条件下刷新 evidence artifact，或明确 re-defer 到 CI nightly / Batch6，并写清 closure test。 |
| Batch 3 handoff note                         | Batch 3 / `019` 能否引用 pilot 的 source-shape facts。                                                                                              | closeout 必须说明 Batch 3 可引用什么、不能引用什么；不得把 staged evidence 升级成 production-live readiness。           |

本任务卡不包含：migration 008 CHECK closeout（`B2.5-O-06` / `A9-*`）、ingestion split R2b–R2d（`R3-B25-HYG-01`）、前端 Vitest / bundle budget（`R3-B25-HYG-02`）、Batch6 production CLI/backfill/reconcile/source-health release gates、general-purpose `qmd data` production CLI、Batch 3 Layer 2 modeling implementation。另据 `docs/architecture/layer1_ingestion_refactor_rollback_plan.md`，Batch 2.75 live pilot 与 ingestion split R2b–R2d 并行禁止，不得同 sprint 混做。

## 1. Goal

Run one strictly scoped, user-authorized live-data pilot after the Batch 2.5 Layer 1 observation ingestion bridge and before Batch 3 downstream modeling consumes production-facing assumptions.

The pilot exists to expose real source issues—schema drift, timestamp formats, missing values, route/capability mismatch, raw evidence gaps, validation behavior, conflict behavior, and lineage gaps—without polluting clean production DB state.

## 2. Non-goals

- No migration 008 CHECK closeout.
- No ingestion monolith split / R2b-R2d refactor.
- No frontend Vitest or bundle budget implementation.
- No Batch 3 Layer 2 modeling implementation.
- No Batch6 production CLI/backfill/reconcile/source-health release gate closure.
- No full-market fetch.
- No full-history fetch.
- No backfill or broad reconcile execution.
- No default enablement of QMT, xqshare, Yahoo, FRED, or any user-authorized source.
- No direct mutation of `data/duckdb/quant_monitor.duckdb`.
- No production CLI scope expansion beyond the pilot gate.
- No general-purpose `qmd data` production CLI implementation; that remains Batch 6 / task 035 prep scope.
- No silent fallback from a live source to a staged fixture.
- No promotion of Batch 2.5 staged evidence to production-live readiness.

## 3. Required authorization input

The implementation must fail closed unless a user-authorized pilot request explicitly declares all fields below:

| Field                    | Requirement                                                                             |
| ------------------------ | --------------------------------------------------------------------------------------- |
| `source_id`              | One source per pilot request; Batch 2.75 default uses the tiny allowlist in §3.1 only.  |
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

### 3.1 User-approved default pilot set

Plan must include the approved narrow pilot set before Phase -1. Details are specified below and must not be broadened during execution.

Default authorization uses 2 sources and 3 separate micro-pilot requests. Purpose: expose route, capability, schema, timestamp, field convention, raw evidence, validation, conflict, and no-mutation issues without opening broad production access.

Required defaults for every request: `dry_run=true`, `raw_only=true`, `write_target=sandbox`, `allow_clean_write=false`. Authorization evidence: `docs/quality/batch275_user_authorization_2026-06-21.md`. Total row cap must stay `<=100`; recommended actual total is `<=40`.

| Request | source_id  | data_domain           | operation                    | symbols_or_indicators | window                 | max_rows | Purpose                                                                                                                  |
| ------- | ---------- | --------------------- | ---------------------------- | --------------------- | ---------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1       | `baostock` | `cn_equity_daily_bar` | `fetch_daily_bar`            | `sh.600519`           | recent 5 trading days  | `10`     | A-share daily-bar primary path: symbol format, trade_date, OHLCV, volume/amount, raw evidence, fetch_log, file_registry. |
| 2       | `akshare`  | `cn_equity_daily_bar` | `fetch_daily_bar_validation` | `sh.600519`           | recent 5 trading days  | `10`     | Validation-only path: compare shape against `baostock`; must not be silently promoted to Primary.                        |
| 3       | `akshare`  | `macro_supplementary` | `fetch_macro_series`         | `DGS10`               | recent 7 calendar days | `20`     | Macro supplementary shape for `ENV-E1-DGS10`; success does not close FRED primary access.                                |

Optional third source: add `cninfo / cn_announcements / fetch_announcement_index / 600519 / recent 7 calendar days / max_rows=20` only if MASTER explicitly needs announcement metadata, URL, publish timestamp, raw evidence, and file_registry shape. Do not fetch PDF bodies or perform announcement backfill in Batch 2.75.

Guardrails:

- Current low-risk default sources are `baostock` and `akshare`; `cninfo` is optional.
- `fred` is not a registered source_id in the current source registry/capability files; do not bypass those gates in Batch 2.75.
- `qmt_xtdata`, `qmt_xqshare`, and `yahoo_finance` remain outside the default plan unless separately authorized and route/capability checks pass.
- `DISABLED_SOURCE`, `CAPABILITY_MISSING`, `USER_AUTH_REQUIRED`, or `RESOURCE_GUARD_PAUSED` stops the relevant request and records failure evidence.
- No fixture/staged fallback may satisfy pilot evidence.
- No write to `data/duckdb/quant_monitor.duckdb`; no production clean DB mutation.
- Raw evidence, file_registry, fetch_log, validation/conflict evidence, and no-mutation proof must be sandbox-scoped.
- This default plan has no clean write. Any future clean write requires separate approval, must stay sandbox-only, and must go through WriteManager.

## 4. Phase -1 — current-state reconciliation

Acceptance criteria:

1. Read `ROUND3_BATCH_IMPLEMENTATION_MAP.md`, `docs/AUDIT_DEFERRED_REGISTRY.md`, `docs/UNRESOLVED_ISSUES_REGISTRY.md`, `docs/RESOLVED_ISSUES_REGISTRY.md`, and `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md` before selecting a source.
2. Confirm `R3-B2.75-01`, `GLOBAL-P2-01`, `B2.5-O-05`, `R3-B25-PERF-BUDGET-01`, and `R3-B25-HYG-03` are mapped to acceptance criteria.
3. Confirm already-closed follow-ups (`R3-B25-DOC-01`, `A08-P1-02`, `R3-B25-HYG-04`) are not reopened.
4. Confirm out-of-scope items remain deferred or assigned to their own future batches, not silently absorbed into Batch 2.75.

Required evidence:

- Source Context Index entries for the five Batch 2.75 tracked IDs/aliases.
- Audit Source Trace from each tracked ID/alias to an acceptance criterion.
- A short “not in Batch 2.75” note for migration 008, ingestion split, frontend bundle budget, Batch6 release gates, `qmd data` production CLI, and Batch 3 modeling.
- A sprint-scope note proving Batch 2.75 live pilot is not mixed with ingestion split R2b–R2d in the same sprint.

## 5. Phase 0 — authorization and source selection

Acceptance criteria:

1. The Trellis plan names the exact source, domain, operation, symbol/indicator, date/window, row cap, and sandbox target.
2. The plan states why the chosen source is lower risk than QMT/xqshare/Yahoo/FRED for the first pilot, or explains why a higher-risk source is necessary.
3. QMT/xqshare/Yahoo/FRED remain disabled unless the user explicitly authorizes that source for this pilot.
4. The pilot cannot proceed if authorization evidence is absent.

## 6. Phase 1 — read-only baseline

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

## 7. Phase 2 — route and capability dry-run

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

## 8. Phase 3 — raw-only live micro-fetch

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

## 9. Phase 4 — sandbox validation and optional clean write

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

## 10. Phase 4.5 — performance-budget evidence gate

Acceptance criteria:

1. `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03` must be handled before closeout, either by refreshing the A6 production-equivalent benchmark artifact or by explicit re-deferral.
2. Any benchmark run must be bounded, non-full-market, non-full-history, and compatible with `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`.
3. Evidence must include the command/profile used, row/window caps, runtime summary, threshold/budget decision, and whether the artifact is suitable for CI nightly or only local audit evidence.
4. Benchmark evidence must not be used as live source authorization and must not mutate the production clean DB.
5. If deferred, the registry update must name the next owner/phase and the exact closure test, not just “later”.

Required evidence:

- `production_equivalent_smoke.py` command/profile or explicit reason it was not run.
- Performance-budget artifact path or explicit re-deferral row.
- ResourceGuard / row-window cap evidence.
- Registry delta for `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`.

## 11. Phase 5 — decision and handoff

The pilot ends in exactly one of these states:

| State                      | Meaning                                                                 | Required follow-up                                                                               |
| -------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `PILOT_PASS_RAW_ONLY`      | Live raw fetch succeeded; clean write not attempted.                    | Batch 3 may reference pilot raw-shape evidence, but production clean readiness remains deferred. |
| `PILOT_PASS_SANDBOX_CLEAN` | Live raw fetch, validation, sandbox clean write, and lineage succeeded. | Batch 3 may reference pilot evidence; Batch 6 still owns formal production release.              |
| `PILOT_FAIL_SOURCE`        | Route/capability/fetch/source failed.                                   | Record source limitation and keep downstream modeling staged.                                    |
| `PILOT_FAIL_VALIDATION`    | Fetch succeeded but validation/conflict blocked clean write.            | Add data-quality or mapping closure task before production release.                              |
| `PILOT_REDEFERRED`         | User did not authorize live pilot or source is unsuitable.              | Keep Batch 2.5 staged semantics and preserve registry deferral.                                  |

## 12. Required registry updates

On closeout, update both registries consistently:

- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`

If the pilot passes, add evidence to `docs/RESOLVED_ISSUES_REGISTRY.md` only for the exact pilot item closed. Do not close broad Batch 6 production CLI/backfill/reconcile/source-health items unless those items have their own implementation and tests.

Closeout must also update or explicitly preserve:

- `R3-B2.75-01` / `GLOBAL-P2-01` / `B2.5-O-05` live-pilot state.
- `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03` performance-budget state.
- Batch 3 handoff note for `019`, including whether `R3-B2.75-01` remains `DEFERRED` and whether Batch 3 must remain staged-only.
- A statement that `B2.5-O-06`, `R3-B25-HYG-01`, `R3-B25-HYG-02`, broad Batch6 release gates, and general-purpose `qmd data` production CLI were not closed by Batch 2.75 unless separate evidence exists.
- A statement that ingestion split R2b–R2d was not mixed into the Batch 2.75 sprint, per `layer1_ingestion_refactor_rollback_plan.md`.

## 13. Verification commands

The planning-only gate must start with document/policy tests:

```bash
pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q
```

The future implementation task must add focused implementation tests before any live source is enabled. Those tests must prove fail-closed authorization, sandbox-only writes, no fixture fallback, row/window caps, and no production DB mutation.
