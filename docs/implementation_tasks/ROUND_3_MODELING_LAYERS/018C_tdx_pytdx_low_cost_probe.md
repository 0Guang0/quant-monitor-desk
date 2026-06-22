# 018C — Low-cost `tdx_pytdx` Data Interface Probe

> Round 3 Batch 2.75 follow-up. This is an isolated sidecar probe task after Batch 2.75 evidence reconciliation.
>
> Status: original execution task card. This file does not enable `tdx_pytdx`, Eastmoney, QMT, xqshare, or any production data path by itself.

## 0. Scope ledger

Batch 2.75 surfaced a Request 2 endpoint problem: the original `akshare / fetch_daily_bar_validation / stock_zh_a_hist` path depends on Eastmoney `push2his.eastmoney.com`, which was judged unavailable in the current pilot environment. A separate Sina path (`ak.stock_zh_a_daily`) produced raw rows, but that evidence is only a sidecar/candidate signal and must not close the original Eastmoney hist request.

`018C` must start only after Batch 2.75 records `phase3_request2_evidence_reconciliation.md` or an equivalent closeout note.

| Alias                                    | Meaning                                                                                                 | Closeout style                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE` | Isolated, raw-only, sandbox-only probe for low-cost A-share data interface candidates after Batch 2.75. | Candidate decision only: accept as disabled-by-default candidate, reject, or re-defer. |

## 1. Goal

Evaluate whether a project-owned `tdx_pytdx` source candidate and an explicitly named AkShare Sina validation endpoint can reduce reliance on unstable Eastmoney `push2his` without weakening QMD source governance.

The goal is evidence for future source registry and capability design, not production readiness.

## 2. Non-goals

- No mutation of `data/duckdb/quant_monitor.duckdb`.
- No production clean DB write.
- No default enablement of `tdx_pytdx`.
- No promotion of `tdx_pytdx` to Primary.
- No silent fallback from Eastmoney hist to Sina, TDX, QMT, xqshare, or any other endpoint.
- No QMT/xqshare live connection unless separately authorized by the user.
- No automatic login, port probing, trading, or order API.
- No full-market, full-history, minute, tick, F10, PDF, backfill, reconcile, or production CLI scope.
- No Batch 3 Layer 2 modeling implementation.
- No DB-GPT or DB-GPT-Hub in the data acquisition layer.

## 3. External-reference boundary

External projects are references only. Execute must not assume prior knowledge of these projects; the URLs and boundaries below are part of this task card.

| Reference project | URL                                           | Borrowable details                                                                                                                                                                                              | Required boundary in QMD                                                                                                                                                                                                                                                                                            |
| ----------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EasyXT            | `https://github.com/quant-king299/EasyXT`     | Candidate-source-chain thinking, especially the documented order `QMT -> xqshare -> TDX -> Eastmoney`; xqshare remote-host/port configuration shape; data-health categories and operator troubleshooting style. | Do not copy trading APIs, automatic login, captcha handling, GUI, automatic source switching, hardcoded DB paths, or any behavior that silently promotes fallback data. QMD must express every source switch through SourceRegistry, CapabilityRegistry, RoutePreview, ResourceGuard, raw evidence, and validation. |
| JQ2PTrade         | `https://github.com/quant-king299/JQ2PTrade`  | Explicit API/capability mapping pattern and local CLI ergonomics such as user-specified DuckDB path.                                                                                                            | Do not copy JoinQuant/PTrade strategy conversion or order APIs. Only use the mapping/CLI pattern to shape QMD source capability and probe contracts.                                                                                                                                                                |
| ptqmt-site        | `https://github.com/quant-king299/ptqmt-site` | Local-only / not-uploaded documentation wording for future operator UI and docs.                                                                                                                                | Do not treat it as a data adapter or runtime dependency.                                                                                                                                                                                                                                                            |
| DB-GPT            | `https://github.com/eosphoros-ai/DB-GPT`      | Future read-only SQL assistant, sandboxed analysis, and report-generation ideas.                                                                                                                                | Do not use it in the data acquisition layer or as a live source probe dependency.                                                                                                                                                                                                                                   |
| DB-GPT-Hub        | `https://github.com/eosphoros-ai/DB-GPT-Hub`  | Future Text-to-SQL evaluation methodology.                                                                                                                                                                      | Do not use model fine-tuning/evaluation work to satisfy live market-data probe evidence.                                                                                                                                                                                                                            |
| bebopze/tdx-quant | `https://github.com/bebopze/tdx-quant`        | TDX ecosystem awareness and possible future implementation research.                                                                                                                                            | Do not import Java/Spring trading architecture or unreviewed code.                                                                                                                                                                                                                                                  |
| afute/TdxQuantNet | `https://github.com/afute/TdxQuantNet`        | Listed for follow-up only.                                                                                                                                                                                      | Current GitHub fetch was not reliably reviewable; do not base implementation on it until source, license, tests, and API behavior are inspected.                                                                                                                                                                    |

## 4. Candidate interfaces

### 4.1 AkShare Sina daily sidecar

This is not the original Batch 2.75 Request 2 endpoint. It must be named separately if retained.

```yaml
source_id: akshare
data_domain: cn_equity_daily_bar
operation: fetch_daily_bar_sina_validation
vendor_api: stock_zh_a_daily
upstream: finance.sina.com.cn
role: Validation
enabled_by_default: false
pilot_only: true
```

Probe target: `sh.600519`, recent 5 trading days, `max_rows=10`, `raw_only=true`, `write_target=sandbox`, `allow_clean_write=false`.

Success does not close `stock_zh_a_hist` / Eastmoney hist.

### 4.2 `tdx_pytdx` disabled candidate

Initial registry/capability shape is subject to evidence:

```yaml
source_id: tdx_pytdx
source_name: TDX / pytdx compatible market data
enabled_by_default: false
default_role: Validation
validation_only: true
allowed_domains:
  - security_list
  - cn_equity_daily_bar
  - cn_index_daily_bar
```

Initial operations only:

| Domain                | Operation               | Probe window/cap                                  | Purpose                                                                |
| --------------------- | ----------------------- | ------------------------------------------------- | ---------------------------------------------------------------------- |
| `security_list`       | `fetch_security_list`   | `max_rows=20` per market                          | Verify market/code/name/security_type and symbol resolver assumptions. |
| `cn_equity_daily_bar` | `fetch_daily_bar`       | `sh.600519`, recent 5 trading days, `max_rows=10` | Low-cost A-share daily-bar candidate shape.                            |
| `cn_index_daily_bar`  | `fetch_index_daily_bar` | `000001.SH`, recent 5 trading days, `max_rows=10` | Index daily-bar candidate shape.                                       |

## 5. Required gates

Every probe request must pass explicit source/domain/operation/symbol/window/max_rows declaration, route preview, capability declaration, ResourceGuard check, task-level authorization for real network fetch, raw-only sandbox output, no production DB mutation proof, and validation-only role preservation.

## 5.1 Architecture implementation path

Implementation must follow the existing QMD data-source architecture rather than importing an external project wholesale.

Allowed implementation shape:

1. Add only draft/disabled registry and capability entries needed for the probe, for example in `specs/datasource_registry/source_registry.yaml` and `specs/datasource_registry/source_capabilities.yaml`.
2. Add or extend adapter code only behind existing ports and gates. A future `tdx_pytdx` adapter must be called through SourceRegistry -> CapabilityRegistry -> RoutePreview -> ResourceGuard -> fetch port -> raw evidence.
3. Add a probe runner only as a bounded sidecar, for example under `backend/app/ops/` or a narrowly scoped script, and write evidence under an isolated sandbox such as `.audit-sandbox/data-interface-probe/`.
4. Store only raw evidence, fetch metadata, file-registry/fetch-log equivalent records, validation summary, and no-mutation proof. Do not write clean production tables.
5. Compare candidate rows only at shape level against `baostock` and/or existing sidecar evidence: date, symbol/exchange, OHLC, volume, amount if present, and source-specific extra fields.
6. Express every endpoint label explicitly: `stock_zh_a_daily` / Sina, `stock_zh_a_hist` / Eastmoney hist, and `tdx_pytdx` operation names must not be conflated.

Files that may be touched in an implementation task, if needed and explicitly planned:

- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `backend/app/datasources/adapters/` for a small disabled candidate adapter
- `backend/app/ops/` for a sidecar probe runner
- `tests/` for route, disabled-by-default, no-primary-promotion, raw-evidence, and no-mutation assertions
- `docs/quality/` or task-local `execute-evidence/` for probe evidence and decision records

Files or behavior that must not be touched by this task:

- No production DB migration.
- No mutation of `data/duckdb/quant_monitor.duckdb`.
- No Batch 2.75 closeout rewrite except referencing its completed reconciliation evidence.
- No `qmd data` production CLI release gate.
- No trading/order API, auto-login, automatic fallback, broad source-health release, or DB-GPT runtime integration.

## 6. Evidence requirements

| Evidence                                                 | Purpose                                                                     |
| -------------------------------------------------------- | --------------------------------------------------------------------------- |
| `execute-evidence/interface_probe_plan.md`               | Exact candidate list and caps.                                              |
| `execute-evidence/interface_probe_route_matrix.json`     | Route/capability/guard status.                                              |
| `execute-evidence/interface_probe_raw_evidence.json`     | Raw fetch results or failure records with endpoint/vendor labels.           |
| `execute-evidence/interface_probe_no_mutation_proof.md`  | Production DB unchanged proof.                                              |
| `execute-evidence/interface_probe_validation_summary.md` | Shape comparison against baostock and/or existing sidecar evidence.         |
| `execute-evidence/interface_probe_decision.md`           | Accepted/rejected/re-deferred decision with owner, phase, and closure test. |

## 7. Closeout outcomes

| Outcome                           | Meaning                                                                      |
| --------------------------------- | ---------------------------------------------------------------------------- |
| `PROBE_ACCEPT_DISABLED_CANDIDATE` | Candidate is suitable to add as disabled-by-default / validation-only draft. |
| `PROBE_REJECT_SOURCE`             | Candidate is unsuitable or unstable; keep failure evidence.                  |
| `PROBE_REDEFERRED`                | Probe could not run safely; record owner, phase, and closure test.           |

No outcome in this task may imply production readiness.

## 8. Round 3 sequencing / branch boundary

This task is a Phase 8D debt/probe branch candidate: recommended branch `debt/r3b275-018c-low-cost-probe`. It may run in parallel with staged-only `019`, but it blocks any future production-live readiness claim that depends on replacing or closing the original Eastmoney hist Request 2 failure. It owns only sidecar probe evidence and disabled-candidate decisions; it must not alter Batch 2.75 closeout semantics.

## 9. Minimum tests

- `tdx_pytdx` is disabled by default.
- `tdx_pytdx` cannot become Primary in this task.
- Missing capability blocks route/fetch.
- `stock_zh_a_daily` candidate cannot satisfy Batch 2.75 `stock_zh_a_hist` Request 2 closeout.
- Every probe raw file includes source, operation, endpoint/vendor label, request params, content hash, timestamp, and sandbox path.
- Production DB no-mutation proof remains true.
