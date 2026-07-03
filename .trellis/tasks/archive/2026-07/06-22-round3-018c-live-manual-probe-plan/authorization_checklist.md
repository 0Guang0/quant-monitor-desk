# 018C TDX Live Manual Probe — Authorization Checklist

> Planning-only gate. **No live fetch may start until every required box is checked in a user-authored authorization record.**

## 1. Required user authorization phrase

The project owner must post **verbatim** (in chat or in the authorization file) a phrase that includes:

```
我授权执行 Round 3 018C TDX 实时手工探测（tdx_pytdx live manual probe），
任务卡：docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md，
执行计划：.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md，
本清单：.trellis/tasks/06-22-round3-018c-live-manual-probe-plan/authorization_checklist.md，
授权文件：docs/quality/tdx_pytdx_live_manual_probe_authorization_<YYYY-MM-DD>.md。
仅允许下列 operation 列表中的项；禁止生产库写入；禁止将 tdx_pytdx 提升为 Primary；
禁止用本探测结论关闭 Eastmoney stock_zh_a_hist / Request 2（R3-B2.75-REQ2-EM）。
```

English equivalent:

```
I authorize the Round 3 018C TDX live manual probe (tdx_pytdx) scoped to
docs/quality/tdx_pytdx_live_manual_probe_authorization_<YYYY-MM-DD>.md only.
Execute plan: .trellis/tasks/06-22-round3-018c-live-manual-probe-plan/live_manual_probe_plan.md.
Allowed operations are limited to authorization_checklist.md §4. Production DB must remain read-only.
tdx_pytdx must not become Primary. This probe does not close Eastmoney stock_zh_a_hist / R3-B2.75-REQ2-EM.
```

**Fail-closed:** Missing phrase, missing date file, scope wider than §4, or `authorized_session_id` mismatch ⇒ no fetch.

## 2. Authorization evidence file

| Field                   | Requirement                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| Path                    | `docs/quality/tdx_pytdx_live_manual_probe_authorization_<YYYY-MM-DD>.md`                      |
| `authorized_session_id` | User-confirmed id for **this** execute session (Trellis task id or user-supplied uuid)        |
| Approved by             | User (project owner)                                                                          |
| Approved on             | ISO date                                                                                      |
| Task card               | `018C_tdx_pytdx_low_cost_probe.md` + `live_manual_probe_plan.md` + this checklist             |
| Policy                  | `docs/quality/production_live_pilot_policy.md`                                                |
| Gate module             | `backend/app/ops/tdx_live_manual_probe_gate.py` — **not** `live_pilot.validate_authorization` |
| Revocation              | If revoked before Phase 3, closeout = `PROBE_REDEFERRED`                                      |

## 3. TDX host / port (user-provided)

| Field            | Requirement                                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------------------------- |
| Who provides     | **User only**                                                                                                   |
| Record location  | Authorization file §「TDX 行情主机」                                                                            |
| Required columns | `host`, `port`, `provided_by`, `provided_on`, `reachability_note`, `reference_only_default`, `user_attestation` |
| Forbidden        | Silent hardcoded HQ IP (`119.147.212.81:7709`) without explicit user selection in table                         |
| Runtime          | Must match `TdxLiveManualProbeRequest.tdx_host` / `tdx_port` validated by gate                                  |

Example (user fills all columns):

| host     | port     | provided_by   | provided_on | reachability_note        | reference_only_default                                 | user_attestation           |
| -------- | -------- | ------------- | ----------- | ------------------------ | ------------------------------------------------------ | -------------------------- |
| _(user)_ | _(user)_ | project owner | YYYY-MM-DD  | user network attestation | false if custom; true only if citing community default | bounded read-only probe OK |

## 4. Per-request declaration (copy into authorization file)

Max **three** rows; partial scope (equity-only) allowed if §4 rows 1/3 omitted with user note.

| #   | probe_id                  | source_id   | data_domain           | operation               | symbol / market | window                | max_rows |
| --- | ------------------------- | ----------- | --------------------- | ----------------------- | --------------- | --------------------- | -------- |
| 1   | `probe-tdx-security-list` | `tdx_pytdx` | `security_list`       | `fetch_security_list`   | `sh` market     | `max_rows=20`         | 20       |
| 2   | `probe-tdx-equity-daily`  | `tdx_pytdx` | `cn_equity_daily_bar` | `fetch_daily_bar`       | `sh.600519`     | recent 5 trading days | 10       |
| 3   | `probe-tdx-index-daily`   | `tdx_pytdx` | `cn_index_daily_bar`  | `fetch_index_daily_bar` | `000001.SH`     | recent 5 trading days | 10       |

Index symbol `000001.SH` uses `parse_index_instrument()` — not equity `sh.` slicing.

**Hard caps:** total rows ≤ **40**; policy ceiling ≤ **100**.

## 5. Global defaults (every request)

| Control                 | Required value                                                             |
| ----------------------- | -------------------------------------------------------------------------- |
| `dry_run`               | `true` through Phase 2; `false` only Phase 3 per approved row              |
| `raw_only`              | `true`                                                                     |
| `write_target`          | `sandbox` → `.audit-sandbox/tdx-pytdx-live-manual-probe/`                  |
| `allow_clean_write`     | `false`                                                                    |
| Production DB           | must **exist** at `data/duckdb/quant_monitor.duckdb` for no-mutation proof |
| Fixture/staged fallback | **Forbidden**                                                              |

## 6. Explicitly not authorized (default)

- `run_interface_probe()` for live TDX HQ traffic
- `tdx_pytdx` as Primary
- Minute/tick/F10/full-market/backfill/reconcile
- Request 2 Eastmoney hist closeout via Sina/TDX sidecar
- `qmt_*`, `yahoo_finance`, `fred` unless separate authorization
- Production clean DB write

## 7. Pre-flight checklist (execute session)

- [ ] Authorization phrase + dated file + `authorized_session_id` match
- [ ] Host/port table complete (all seven columns)
- [ ] Gate: `validate_tdx_live_manual_probe_authorization()` passes
- [ ] Production DB file exists (else `PROBE_REDEFERRED` / `db_absent`)
- [ ] Phase 1 DB baseline captured
- [ ] Phase 2 route dry-run per `live_manual_probe_plan.md` §8.1–§8.2
- [ ] ResourceGuard eco profile; row caps wired
- [ ] **Not** using forbidden entrypoints (§6)

## 8. Post-probe checklist

- [ ] `interface_probe_live_raw_evidence.json` with `upstream: tdx_hq_host:<host>:<port>`
- [ ] `interface_probe_live_no_mutation_proof.md` → `zero_mutation: true`
- [ ] `per_candidate.tdx_pytdx_live_probe` updated per plan §11.1
- [ ] `AUDIT_DEFERRED_REGISTRY.md` — `R3-B2.75-REQ2-EM` unchanged unless separate EM evidence
- [ ] Merge report: production-live still blocked
