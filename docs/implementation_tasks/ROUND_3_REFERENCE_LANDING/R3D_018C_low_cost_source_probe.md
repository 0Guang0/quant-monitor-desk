# R3D_018C_low_cost_source_probe — Low-cost Source Probe Landing Task

## 1. Round / batch / branch

| Field                | Value                                                                                                                                                                   |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Round                | Round 3                                                                                                                                                                 |
| Batch                | Batch 2.75 follow-up / Phase 8D Repair-Debt Lite                                                                                                                        |
| Branch               | `debt/r3b275-018c-low-cost-probe`                                                                                                                                       |
| Can run in parallel? | Yes, with staged-only `019`; no dependency on `feature/round3-019-layer2-sensor` except shared staged-only semantics.                                                   |
| Blocking?            | Blocks only future production-live readiness claims that depend on replacing/closing the original Eastmoney hist Request 2 failure. Does not block staged-only Batch 3. |

## 2. Source of truth

This card is a landing wrapper. The canonical original task card remains:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`

Required audit/deferred IDs:

- `R3-B2.75-REQ2-EM`
- `R3-B2.75-FOLLOWUP-DATA-INTERFACE-PROBE`
- Batch 2.75 closeout: `PILOT_FAIL_SOURCE`

## 3. External project links execute must see

| Project              | URL                                           | Use in this task                                                                                                                                                     | Boundary                                                                                           |
| -------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| henrylin99/tdx_quant | `https://github.com/henrylin99/tdx_quant`     | Primary Python/pytdx reference for `TdxDownloader`, security list, daily bars, index daily bars, explicit market handling, paging, and fail-closed no-data behavior. | Do not copy screener/indicator/full parquet pipeline/minute/tick/F10. Borrow interface-shape only. |
| EasyXT               | `https://github.com/quant-king299/EasyXT`     | Candidate-source-chain thinking, xqshare shape, data-health/troubleshooting categories.                                                                              | Do not copy trading APIs, automatic login, GUI, automatic source fallback, or hardcoded DB paths.  |
| JQ2PTrade            | `https://github.com/quant-king299/JQ2PTrade`  | API/capability mapping and local CLI ergonomics.                                                                                                                     | Do not copy strategy conversion or order APIs.                                                     |
| ptqmt-site           | `https://github.com/quant-king299/ptqmt-site` | Local-only documentation wording.                                                                                                                                    | Not a data adapter or runtime dependency.                                                          |
| bebopze/tdx-quant    | `https://github.com/bebopze/tdx-quant`        | TDX ecosystem awareness only.                                                                                                                                        | Do not import Java/Spring trading architecture.                                                    |
| afute/TdxQuantNet    | `https://github.com/afute/TdxQuantNet`        | Follow-up only.                                                                                                                                                      | Must not be used until source/license/tests/API behavior are inspected.                            |
| hlh2518/tdx-quant    | `https://github.com/hlh2518/tdx-quant`        | Follow-up only.                                                                                                                                                      | Must not be used until source/license/tests/API behavior are inspected.                            |
| DB-GPT               | `https://github.com/eosphoros-ai/DB-GPT`      | Future read-only SQL/reporting research only.                                                                                                                        | Not part of this data acquisition task.                                                            |
| DB-GPT-Hub           | `https://github.com/eosphoros-ai/DB-GPT-Hub`  | Future Text-to-SQL evaluation research only.                                                                                                                         | Not part of this data acquisition task.                                                            |

## 4. Plan-stage input index

Plan must read and summarize:

- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`

Plan must cite the external URLs above in its Source Context Index so Execute can open them without relying on chat memory.

## 5. Execute manifest policy

Execute must stay narrow. Include only:

- task MASTER / AUDIT / current slice plan
- `018C_tdx_pytdx_low_cost_probe.md`
- registry/capability files if the slice explicitly edits disabled candidate entries
- route/resource/data-quality/source-conflict contract files if tests require them
- narrow adapter/probe files only if implementation is approved
- tests selected by MASTER

Do not include DB-GPT, full EasyXT runtime, trading framework files, broad CLI/backfill files, or production DB files.

## 6. Allowed changes

- Add disabled-by-default `tdx_pytdx` draft candidate if evidence requires it.
- Add validation-only operation declarations for `security_list`, `cn_equity_daily_bar`, `cn_index_daily_bar`.
- Add route-preview/no-primary-promotion/no-mutation tests.
- Add bounded sidecar probe evidence under a task-local or audit-sandbox path.

## 7. Forbidden changes

- No production DB mutation.
- No production clean write.
- No default enablement of `tdx_pytdx`.
- No Primary role for `tdx_pytdx`.
- No automatic fallback from Eastmoney hist to Sina/TDX/QMT/xqshare.
- No trading/order API, auto-login, broad source health release, or DB-GPT runtime integration.

## 8. Acceptance criteria

- `tdx_pytdx` remains disabled by default and validation-only if added.
- Route/capability tests fail closed when capability, authorization, or ResourceGuard is missing.
- `stock_zh_a_daily` / Sina is not conflated with `stock_zh_a_hist` / Eastmoney hist.
- Evidence records endpoint/vendor label, params, row count, content hash, timestamp, sandbox path, and failure reason.
- Production DB no-mutation proof is attached.
- Closeout is one of `PROBE_ACCEPT_DISABLED_CANDIDATE`, `PROBE_REJECT_SOURCE`, or `PROBE_REDEFERRED`.
