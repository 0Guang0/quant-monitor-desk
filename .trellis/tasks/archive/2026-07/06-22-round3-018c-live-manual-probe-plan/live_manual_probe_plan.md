# 018C — TDX Live Manual Probe Plan (Future Execute)

> **Status:** planning-only · branch `debt/r3b275-018c-live-manual-probe-plan`  
> **This document does not authorize or perform live network access.**

## 1. Purpose and boundaries

### 1.1 Why this plan exists

018C low-cost probe accepted `tdx_pytdx` as a **disabled validation candidate** (`PROBE_ACCEPT_DISABLED_CANDIDATE`) but deferred the actual live TDX network probe (`tdx_pytdx_live_probe: PROBE_REDEFERRED`). Batch 2.75 Request 2 (`R3-B2.75-REQ2-EM`) — Eastmoney `stock_zh_a_hist` / push2his — remains open.

This plan defines how a **later**, **user-authorized** session may run a bounded live `tdx_pytdx` probe without weakening QMD governance.

### 1.2 What success does **not** mean

- Does **not** enable `tdx_pytdx` by default
- Does **not** promote `tdx_pytdx` to Primary
- Does **not** close `R3-B2.75-REQ2-EM` or claim Eastmoney hist is fixed
- Does **not** unblock production-live readiness
- Does **not** authorize automatic fallback from Eastmoney → Sina/TDX/QMT/xqshare

### 1.3 Prior 018C evidence (base branch)

| Candidate                             | Outcome                            |
| ------------------------------------- | ---------------------------------- |
| `tdx_pytdx` registry/capability draft | `PROBE_ACCEPT_DISABLED_CANDIDATE`  |
| `akshare_sina_sidecar`                | `PROBE_REDEFERRED`                 |
| `tdx_pytdx_live_probe`                | `PROBE_REDEFERRED` ← **this plan** |

Evidence: `.trellis/tasks/06-22-round3-018c-low-cost-probe/execute-evidence/interface_probe_decision.md`

---

## 2. Source context index (Plan-stage summary)

| Input                                           | Summary for live probe                                                                                      |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `AGENTS.md`                                     | Phase 8D Repair/Debt Lite for debt slices; one worktree per agent; no production DB writes in debt planning |
| `CLAUDE.md`                                     | Project conventions; follow Trellis workflow for execute                                                    |
| `.trellis/workflow.md`                          | Plan → Execute → Audit; complex tasks use MASTER.plan.md gates                                              |
| `complex-task-planning-protocol.md` Phase 8D    | Lightweight slice plan with owner, base branch, allowed/forbidden files, verification, merge gate           |
| `round3-repair-debt-worktree-plan.md`           | Parallel debt branches; registry reconciliation at merge; `debt/r3b275-018c-*` stream                       |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md`            | `R3-018C-LIVE-MANUAL-PROBE-PLAN` alias; PROMPT_10; does not block staged `019`                              |
| `018C_tdx_pytdx_low_cost_probe.md`              | Three operations, row caps, sandbox-only, external reference boundaries                                     |
| `R3D_018C_low_cost_source_probe.md`             | Landing wrapper; henrylin99/tdx_quant primary Python reference                                              |
| `R3D_018C_live_manual_probe_plan.md`            | Task card for this planning slice                                                                           |
| `AUDIT_DEFERRED_REGISTRY.md`                    | `R3-B2.75-REQ2-EM` deferred to 018C; Batch 2.75 `PILOT_FAIL_SOURCE` resolved                                |
| `UNRESOLVED_ISSUES_REGISTRY.md`                 | Request 2 open; Batch 3 staged-only                                                                         |
| `production_live_pilot_policy.md`               | Authorization fields, phase gates 0–5, raw-only first pass, sandbox write target                            |
| `BATCH3_STAGED_DOWNSTREAM_GATE.md`              | 018C parallel OK; 018C PASS does not open production-live                                                   |
| `source_registry.yaml`                          | `tdx_pytdx`: disabled, Validation, three domains                                                            |
| `source_capabilities.yaml`                      | `proposed_disabled_source`; ops disabled by default                                                         |
| `source_route_contract.yaml`                    | Route statuses: READY, DISABLED_SOURCE, CAPABILITY_MISSING, USER_AUTH_REQUIRED, etc.                        |
| `datasource_service_contract.yaml`              | Fetch via service facade; route plan before adapter                                                         |
| `resource_limits.yaml`                          | eco/normal/batch profiles; API row caps                                                                     |
| `data_quality_rules.yaml`                       | Validation before clean write (not in scope — no clean write)                                               |
| `source_conflict_rules.yaml`                    | No silent primary substitution                                                                              |
| `backend/app/datasources/adapters/tdx_pytdx.py` | Skeleton adapter; not factory-registered as Primary                                                         |
| `backend/app/ops/interface_probe.py`            | Sidecar probe runner; 018C deferred non-equity-daily TDX ops                                                |
| `tests/test_interface_probe_018c.py`            | Disabled-by-default, no Primary, no Request 2 closeout                                                      |

### 2.1 External references (inspection only — do not vendor)

| Project              | URL                                     | Use in live probe                                                                                     |
| -------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| henrylin99/tdx_quant | https://github.com/henrylin99/tdx_quant | Primary pytdx shape: security list, daily bars, index bars, market codes, paging, fail-closed no-data |
| afute/TdxQuantNet    | https://github.com/afute/TdxQuantNet    | Follow-up only — inspect license/tests/API before any borrow                                          |
| hlh2518/tdx-quant    | https://github.com/hlh2518/tdx-quant    | Follow-up only — same boundary as TdxQuantNet                                                         |

Borrow **interface shape** from henrylin99/tdx_quant only. Do not copy screener, indicators, parquet pipelines, minute/tick/F10, or direct DB write behavior.

---

## 3. Authorization (exact requirements)

See `authorization_checklist.md` for the checklist. Execute **must** record:

1. Verbatim user authorization phrase (Chinese or English template in checklist §1)
2. File `docs/quality/tdx_pytdx_live_manual_probe_authorization_<YYYY-MM-DD>.md`
3. Per-request table matching §4 below — no extra sources/domains/operations

**Gate implementation:** use `backend/app/ops/tdx_live_manual_probe_gate.py` — **`validate_tdx_live_manual_probe_authorization()`**.  
**Do not** call `live_pilot.validate_authorization()` (Batch 2.75 batch275 triples only).

Entry point for live execute: **`run_tdx_live_manual_probe()`** (future) — must call gate before any `TdxPytdxProbeFetchPort` with `authorization_verified=True`.

**Forbidden entrypoints (no live HQ connect):**

- `backend.app.ops.interface_probe.run_interface_probe`
- `TdxPytdxProbeFetchPort(...)` without `authorization_verified=True` and user host/port from auth file

Tests: `tests/test_tdx_live_manual_probe_authorization.py` (no network).

---

## 4. Allowed operations, symbols, and row caps

Only these three operations are in scope for the first live pass:

| probe_id                  | baseline_018c_probe_id | source_id   | data_domain           | operation               | symbol / market    | window                    | max_rows |
| ------------------------- | ---------------------- | ----------- | --------------------- | ----------------------- | ------------------ | ------------------------- | -------- |
| `probe-tdx-security-list` | same                   | `tdx_pytdx` | `security_list`       | `fetch_security_list`   | `sh` (market code) | per-market cap            | **20**   |
| `probe-tdx-equity-daily`  | same                   | `tdx_pytdx` | `cn_equity_daily_bar` | `fetch_daily_bar`       | `sh.600519`        | recent **5** trading days | **10**   |
| `probe-tdx-index-daily`   | same                   | `tdx_pytdx` | `cn_index_daily_bar`  | `fetch_index_daily_bar` | `000001.SH`        | recent **5** trading days | **10**   |

**Symbol resolution:**

- Equity: `sh.` / `sz.` prefix → pytdx market `1` / `0`, code = suffix after dot.
- Index: `000001.SH` / `*.SZ` → use `tdx_live_manual_probe_gate.parse_index_instrument()` (market `1`/`0`, code without suffix). **Do not** use equity `[3:]` slicing on index ids.

**Execute prerequisite (ports):** before live Phase 3, implement fetch ports for `get_security_list` and `get_index_bars` (henrylin99/tdx_quant shape). Until then, auth file may declare **partial scope** (equity daily only) and closeout records deferred ops — see §11.4.

**Aggregate cap:** ≤ **40** rows total across all requests (Batch 2.75 precedent); hard policy ceiling **100** (`production_live_pilot_policy.md`).

**Forbidden symbols/ops:** full-market lists, minute/tick, F10, backfill windows, any symbol not listed in the authorization file amendment.

---

## 5. TDX host and port

| Rule            | Detail                                                                                                                                                    |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source of truth | User-provided values in authorization file § host/port table                                                                                              |
| Who may set     | Project owner / operator only — not the planning agent                                                                                                    |
| Recording       | `host`, `port`, `provided_by`, `provided_on`, `reachability_note`, `reference_only_default`, `user_attestation`                                           |
| Runtime wiring  | Future execute passes host/port via env e.g. `TDX_PROBE_HOST`, `TDX_PROBE_PORT` or explicit probe request fields — **never** silently override user table |
| Reference       | Community defaults (e.g. `119.147.212.81:7709`) documented in henrylin99/tdx_quant — usable only if user explicitly selects them in authorization         |

018C sandbox code used a hardcoded host for stub/live experiments; **live manual probe execute must reject fetch if authorization file host/port ≠ runtime config.**

---

## 6. Sandbox output path

| Artifact           | Path                                                                                                              |
| ------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Raw JSON payloads  | `.audit-sandbox/tdx-pytdx-live-manual-probe/raw/`                                                                 |
| Route matrix       | `.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/execute-evidence/interface_probe_live_route_matrix.json` |
| Raw evidence index | `.../interface_probe_live_raw_evidence.json`                                                                      |
| No-mutation proof  | `.../interface_probe_live_no_mutation_proof.md`                                                                   |
| Validation summary | `.../interface_probe_live_validation_summary.md`                                                                  |
| Closeout decision  | `.../interface_probe_live_decision.md`                                                                            |

Each raw record must include: `probe_id`, `baseline_018c_probe_id`, `source_id`, `operation`, `vendor_api` label (`pytdx.get_security_list` / `pytdx.get_security_bars` / `pytdx.get_index_bars`), `upstream` (`tdx_hq_host:<host>:<port>`), request params, `row_count`, `content_hash`, `timestamp`, `sandbox_path`, `status`, `failure_reason` if any.

**Policy evidence chain** (`production_live_pilot_policy.md` §6) — live execute must also capture:

| Evidence               | Path / note                                                 |
| ---------------------- | ----------------------------------------------------------- |
| ResourceGuard decision | `execute-evidence/interface_probe_live_resource_guard.json` |
| Route preview          | `interface_probe_live_route_matrix.json`                    |
| Raw file + hash        | sandbox `raw/` + index JSON                                 |
| `file_registry` row    | read-only index or sandbox DB row id in evidence JSON       |
| `fetch_log` row        | sandbox-equivalent metadata in evidence JSON                |
| Authorization path     | copy path + `authorized_session_id`                         |

No production `WriteManager` clean write; sandbox metadata may use isolated audit paths only.

---

## 7. No-mutation proof method

Follow 018C `capture_no_mutation_proof()` pattern (`interface_probe.py`):

1. **Before any network call:** confirm `data/duckdb/quant_monitor.duckdb` **exists**; if absent → `PROBE_REDEFERRED`, proof flag `db_absent: true` (never treat as `zero_mutation: true`).
2. Read DB bytes + `KEY_TABLES` row counts via read-only inspector.
3. **After all probe activity:** re-read bytes + counts.
4. **Pass criteria:** `zero_mutation: true` — byte-identical DB file and identical key table counts.
5. **Evidence:** markdown table in `interface_probe_live_no_mutation_proof.md` + SHA-256 before/after in JSON sidecar.
6. **Fail:** any delta ⇒ abort closeout as `PROBE_REDEFERRED` or `PROBE_REJECT_SOURCE`.

No `WriteManager`, no clean table writes, no migration, no registry DB sync in the same session.

---

## 8. Route preview — expected states

Use `SourceRoutePlanner` + `build_route_matrix()` pattern before each live fetch phase.

### 8.1 Phase 2 dry-run (default registry — no ephemeral enable)

Authoritative invariant (matches `tests/test_interface_probe_018c.py::test_routeMatrix_tdxFailClosed` and 018C `interface_probe_route_matrix.json`):

- For every `tdx_pytdx` row: `source_enabled_by_default` is **false** and `selected_source_id` is **never** `tdx_pytdx`.

| probe_id (018C baseline)  | Typical `route_status` | `selected_source_id`                  | Pass?                  |
| ------------------------- | ---------------------- | ------------------------------------- | ---------------------- |
| `probe-tdx-equity-daily`  | `READY`                | `baostock` (or other non-tdx Primary) | Yes — tdx not selected |
| `probe-tdx-security-list` | `NO_AVAILABLE_SOURCE`  | `null`                                | Yes                    |
| `probe-tdx-index-daily`   | `NO_AVAILABLE_SOURCE`  | `null`                                | Yes                    |

| Hard fail | Condition                                                                                                                                     |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **BLOCK** | `selected_source_id == "tdx_pytdx"` while on-disk registry YAML still has `enabled_by_default: false` and no documented ephemeral pilot scope |

### 8.2 Phase 2 vs Phase 3 route semantics (`production_live_pilot_policy` alignment)

| Phase     | Purpose                           | `route_status` for tdx rows                                              | May fetch?                 |
| --------- | --------------------------------- | ------------------------------------------------------------------------ | -------------------------- |
| 2 dry-run | Production-path fail-closed check | `READY`+non-tdx selected, or `NO_AVAILABLE_SOURCE`                       | **No**                     |
| 3 live    | Authorized sidecar only           | `READY` with `selected_source_id=tdx_pytdx` **inside probe runner only** | **Yes**, one row at a time |

Phase 2 `NO_AVAILABLE_SOURCE` for security_list / index is **expected**, not a pilot failure.

### 8.3 Ephemeral enable contract (execute)

Within `run_tdx_live_manual_probe()` only:

1. Call `validate_tdx_live_manual_probe_authorization()` first.
2. Enter `with_ephemeral_capability_enable(source_id="tdx_pytdx", domain, operation)` — in-memory overlay on `SourceCapabilityRegistry` / route planner context; **must not** write YAML or DB registry.
3. Recompute route for the single authorized triple; require `route_status=READY` and `selected_source_id=tdx_pytdx`.
4. Fetch via authorized `TdxPytdxProbeFetchPort(host=..., port=..., authorization_verified=True)`.
5. On exit context manager: restore registry; assert `test_routeMatrix_tdxFailClosed` semantics again.

Scope: single process / single session; destroyed on process exit or explicit `finally`.

### 8.4 Phase 3 live fetch (after §8.3)

Execute may use **in-memory or session-scoped** enablement for `tdx_pytdx` **only** when authorization + ResourceGuard pass. Expected:

| Field                       | Expected                                                                                            |
| --------------------------- | --------------------------------------------------------------------------------------------------- |
| `source_enabled_by_default` | still `false` in YAML (disk unchanged)                                                              |
| `route_status`              | `READY` for the authorized operation only                                                           |
| `selected_source_id`        | `tdx_pytdx` **only** inside the bounded probe runner — never persisted as Primary in `domain_roles` |
| `quality_flags`             | must **not** include silent fallback flags                                                          |

Production orchestrator routes must continue to show `tdx_pytdx` skipped with `disabled_reason` after probe session ends.

---

## 9. ResourceGuard caps

Apply `specs/contracts/resource_limits.yaml` **default_profile: eco** unless user authorizes `batch` (requires `requires_user_confirm: true`).

| Guard                           | eco value                   | Live probe binding                  |
| ------------------------------- | --------------------------- | ----------------------------------- |
| `max_threads`                   | 2                           | Single-threaded probe runner        |
| `preferred_threads`             | 1                           | Default for pytdx connect/fetch     |
| `process_rss_hard_stop_mb`      | 1800                        | Stop probe if exceeded              |
| `max_parallel_non_core_jobs`    | 1                           | No concurrent probes                |
| `api_limits` daily_bar_max_days | 365                         | Window capped to 5 trading days     |
| Row cap                         | ≤40 (probe) / ≤100 (policy) | Enforced in probe request validator |

On `RESOURCE_GUARD_PAUSED` or hard stop: status `FAILED`, taxonomy `RESOURCE_GUARD_BLOCKED`, no retry without human confirm.

---

## 10. Failure taxonomy

| Code                     | Meaning                              | Evidence                   | Next action                                 |
| ------------------------ | ------------------------------------ | -------------------------- | ------------------------------------------- |
| `AUTH_MISSING`           | No phrase or authorization file      | Route blocked before fetch | Re-defer; user must authorize               |
| `AUTH_SCOPE_MISMATCH`    | Request not in approved table        | Validator log              | Fix authorization or narrow request         |
| `HOST_PORT_MISMATCH`     | Runtime ≠ authorization host/port    | Config audit               | User corrects config                        |
| `DISABLED_SOURCE`        | tdx not enabled for production route | route_matrix.json          | Expected in Phase 2 dry-run                 |
| `CAPABILITY_MISSING`     | Operation not declared               | capability registry        | Fix specs on mainline branch                |
| `USER_AUTH_REQUIRED`     | QMT-style gate (if reused)           | route plan                 | Not applicable unless extended              |
| `NETWORK_ERROR`          | TCP connect failed                   | raw evidence `FAILED`      | Record host; re-defer or user fixes network |
| `EMPTY_RESPONSE`         | pytdx returned no rows               | raw evidence               | `PROBE_REJECT_SOURCE` if persistent         |
| `PYTDX_NOT_INSTALLED`    | Import error                         | stderr capture             | Document dependency; re-defer               |
| `RESOURCE_GUARD_BLOCKED` | RSS/disk/thread guard                | guard log                  | Reduce scope or eco retry                   |
| `MUTATION_DETECTED`      | DB bytes/counts changed              | no_mutation_proof          | **Rollback session**; incident note         |
| `ROW_CAP_EXCEEDED`       | > max_rows                           | validator                  | Truncate forbidden — fail closed            |

---

## 11. Close / re-defer criteria

### 11.1 Close live slice — `per_candidate.tdx_pytdx_live_probe`

| Outcome                           | When                                                                     | Registry                                                                           |
| --------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `PROBE_ACCEPT_DISABLED_CANDIDATE` | ≥1 authorized op SUCCESS, shape OK, `zero_mutation`, YAML still disabled | Update evidence only; **does not** change `tdx_pytdx` low-cost registry conclusion |
| `PROBE_REJECT_SOURCE`             | Persistent network/empty/shape/policy failure                            | Keep `R3-B2.75-REQ2-EM` open                                                       |
| `PROBE_REDEFERRED`                | No auth, missing ports, partial scope declined                           | No registry enablement                                                             |

Distinct from low-cost `per_candidate.tdx_pytdx` (registry draft). Live success updates **`tdx_pytdx_live_probe`** from `PROBE_REDEFERRED` → `PROBE_ACCEPT_DISABLED_CANDIDATE` only; never implies production-live.

### 11.2 Close as `PROBE_ACCEPT_DISABLED_CANDIDATE` (live shape validated)

All must be true:

- User authorization on file for **this** session
- All three operations attempted OR documented skip with reason for unreachable op only after user approves partial scope
- At least **one** operation returns `SUCCESS` with valid raw JSON shape (date, OHLC, volume fields present at shape level)
- `zero_mutation: true`
- `tdx_pytdx` still `enabled_by_default: false` in committed registry after session
- Closeout explicitly states: `does_not_close_R3-B2.75-REQ2-EM: true`, `does_not_unblock_production_live_readiness: true`

### 11.3 Close as `PROBE_REJECT_SOURCE`

- Persistent `NETWORK_ERROR` / `EMPTY_RESPONSE` across retries within cap
- Shape incompatible with capability contract
- Policy violation (mutation, row cap breach, Primary promotion attempt)

### 11.4 Close as `PROBE_REDEFERRED`

- User revokes authorization
- Host/port not provided
- Environment blocks pytdx install
- Partial success insufficient and user declines amendment
- Fetch ports for `fetch_security_list` / `fetch_index_daily_bar` not implemented yet (equity-only partial auth allowed)

---

## 12. Rollback and cleanup

1. **Disconnect** all pytdx sessions (`api.disconnect()` in finally block)
2. **Remove ephemeral enablement** — restart process or drop in-memory registry overrides
3. **Retain** sandbox raw files and evidence for audit; do not copy into `data/raw/` production tree
4. **Verify** production DB hash unchanged (re-run no-mutation proof)
5. **Do not** commit `enabled_by_default: true` for `tdx_pytdx`
6. **Do not** add `tdx_pytdx` to `domain_roles.cn_equity_daily_bar.primary`
7. If mutation detected: restore DB from last known good backup; file incident in `AUDIT_DEFERRED_REGISTRY.md`
8. Delete transient env vars `TDX_PROBE_HOST` / `TDX_PROBE_PORT` from shell profile if set for probe only

---

## 13. Execute phases (future session)

| Phase | Action                                                             | Live network?             |
| ----- | ------------------------------------------------------------------ | ------------------------- |
| 0     | Authorization file + phrase + host/port + `authorized_session_id`  | No                        |
| 1     | Read-only DB/data-root baseline + registry snapshot                | No                        |
| 2     | Route preview dry-run; assert fail-closed routes                   | No                        |
| 3     | Raw-only micro-fetch per approved row                              | **Yes** (authorized only) |
| 4     | Shape validation vs baostock/sidecar metadata (no clean write)     | No                        |
| 5     | Closeout decision + registry narrative update (no YAML enablement) | No                        |

---

## 14. Verification commands (planning branch)

```bash
pytest tests/test_interface_probe_018c.py -q
pytest tests/test_tdx_live_manual_probe_authorization.py -q
pytest tests/test_source_capabilities.py -q
pytest tests/test_production_live_pilot_policy.py -q
pytest tests/test_round3_audit_registry_alignment.py -q
python scripts/check_doc_links.py
```

Future execute adds: authorization-block tests without network; live evidence files under task `execute-evidence/`.

---

## 15. Merge gate report (required wording)

> **Production-live readiness remains blocked.** This branch prepared the TDX live manual probe plan only. `tdx_pytdx` stays disabled-by-default and validation-only. `R3-B2.75-REQ2-EM` is not closed. A future user-authorized live probe must succeed with no-mutation proof before any reconsideration of TDX as a production validation path.
