# PH-B3 Audit — HITL + Raw Fetch

## 结论

**PASS（带证据限制与中风险发现）**

PH-B3 的核心安全边界通过：HITL 证据存在且文件创建时间早于 raw fetch 证据创建时间；三项 fetch 请求均记录为 `raw_only=true`、`allow_clean_write=false`、`write_target=sandbox`；production DB hash/row-count 证明为 0 mutation；Request 2 的 Sina `stock_zh_a_daily` sidecar 没有被允许冒充原始 Eastmoney `stock_zh_a_hist` 成功；Request 3 明确保留 `fred_primary_deferred=true`，未关闭 FRED primary。

不过，`phase3_raw_micro_fetch_evidence.json` 中 `pilot-req-2` 仍保留 orchestration-layer `SUCCESS`，且 `8.5b-green.txt` 历史证据曾将其写成 `stock_zh_a_daily / sina` success。该风险已由 `phase3_request2_evidence_reconciliation.md` 和 `eastmoney_stock_zh_a_hist_verdict.md` 明确纠偏：Sina sidecar 只能作为 candidate/informational，不能关闭原始 Request 2，也不能支持 `PILOT_PASS_RAW_ONLY`。

## B3 Checklist

| ID                                 | 结论 | 审计判断                                                                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B3-1 HITL 文件存在且先于 fetch     | PASS | `phase3_hitl_user_confirmation.md` 存在，声明用户于 2026-06-21 明确确认「确认请执行」，并列出 sandbox/raw-only/no production mutation/Request 3 不关闭 FRED 等约束。文件 `CreationTimeUtc=2026-06-21T11:08:37.4827718Z`，raw evidence `CreationTimeUtc=2026-06-21T11:47:08.2032852Z`，支持 HITL 先于 fetch。限制：后续 `LastWriteTimeUtc` 被统一更新，不能用于先后证明。                                      |
| B3-2 sandbox raw evidence JSON     | PASS | `phase3_raw_micro_fetch_evidence.json` 存在，`phase=phase3_raw_micro_fetch`，sandbox root 为 `.audit-sandbox/batch275-live-pilot`，三条 request 均有 sandbox raw file path。只读抽查显示 sandbox 下存在三份 raw JSON 与每个 request 的 sandbox DuckDB 文件。                                                                                                                                                  |
| B3-3 production DB delta = 0       | PASS | `phase3_no_production_mutation_proof.md` 记录 `pilot-req-1/2/3 hash_unchanged=True row_counts_unchanged=True`；raw evidence 内每个 request 的 `production_mutation_proof.db_hash_unchanged=true` 且 `row_counts_unchanged=true`，关键表 before/after counts 一致，`fetch_log=0`、`write_audit_log=0`、`validation_report=0`。                                                                                 |
| B3-4 Request 2 不升 Primary        | PASS | Request 2 原授权为 `akshare` / `fetch_daily_bar_validation` / validation-only。raw evidence 中 Request 2 `operation=fetch_daily_bar_validation`、`source_id=akshare`、`raw_only=true`、`allow_clean_write=false`；route candidates 仍显示 `baostock=Primary`、`akshare=Validation`。`phase3_request2_evidence_reconciliation.md` 明确 “Request 2 is validation-only and must not be promoted to Primary.”     |
| B3-5 Request 3 不关闭 FRED primary | PASS | raw evidence 顶层与 `pilot-req-3` 均记录 `fred_primary_deferred=true`，note 为 “Request 3 akshare macro shape only; does not close FRED primary for ENV-E1-DGS10”。                                                                                                                                                                                                                                           |
| B3-6 content hash + fetch_log 字段 | PASS | 三个 `fetch_result` 均包含 `content_hash`、`schema_hash`、`fetch_time`、`latency_ms`、`retry_count`、`row_count`、`run_id`、`raw_file_paths`。production DB proof 中 `fetch_log` before/after 均为 0，符合 raw-only/no production mutation 约束。                                                                                                                                                             |
| B3-7 Request 2 endpoint 语义核对   | PASS | `eastmoney_stock_zh_a_hist_verdict.md` 判定原始 Eastmoney `stock_zh_a_hist` / `push2his.eastmoney.com` 不可用；`phase3_request2_evidence_reconciliation.md` 将 raw JSON 中的 `pilot-req-2` 保留为 historical/sidecar evidence，并明确 Sina `stock_zh_a_daily` 不得关闭原始 Eastmoney hist 请求，不支持 `PILOT_PASS_RAW_ONLY`。sandbox raw file 也可见 `vendor_api=stock_zh_a_daily`，与 reconciliation 一致。 |

## 证据路径

- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/AUDIT.plan.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/audit.jsonl`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/gitnexus-audit-summary.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase3_hitl_user_confirmation.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase3_raw_micro_fetch_evidence.json`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase3_no_production_mutation_proof.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/eastmoney_stock_zh_a_hist_verdict.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase3_request2_evidence_reconciliation.md`
- `.audit-sandbox/batch275-live-pilot/req-1/data/raw/baostock/cn_equity_daily_bar/2026-06-21/7f53f46d7bf41341d81debc4d60dd71ac8800a799fcbd39d0688eb1179862ec7.json`
- `.audit-sandbox/batch275-live-pilot/req-2/data/raw/akshare/cn_equity_daily_bar/2026-06-21/c94dc92f92cb8a7734e51d8d28d5353129ac24b7ef1280bf4cf6714c94163f92.json`
- `.audit-sandbox/batch275-live-pilot/req-3/data/raw/akshare/macro_supplementary/2026-06-21/1641f3f3fbe32795288f39aa4060e59fabe1684f2aaab7aa2c13011591397429.json`

## 发现项

| Severity | Finding                                                                                           | Impact                                                                                                                                                                                                                                                                                                                                                               | Evidence                                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Medium   | Request 2 raw evidence has a stale success-shaped envelope.                                       | `phase3_raw_micro_fetch_evidence.json` records `pilot-req-2.fetch_result.status=SUCCESS` with a content hash and row count, but reconciliation proves this is Sina `stock_zh_a_daily` sidecar, not the approved Eastmoney `stock_zh_a_hist` endpoint. Downstream readers must use the reconciliation/verdict files as authority and must not infer Request 2 passed. | `phase3_raw_micro_fetch_evidence.json`; `eastmoney_stock_zh_a_hist_verdict.md`; `phase3_request2_evidence_reconciliation.md`; `.audit-sandbox/.../c94dc92f....json` |
| Low      | HITL ordering is supported by creation time and content, but not by immutable timestamp evidence. | `CreationTimeUtc` supports HITL before raw fetch. `LastWriteTimeUtc` appears later and close to other evidence files, likely due later formatting/touching, so it should not be used as authoritative ordering proof.                                                                                                                                                | `phase3_hitl_user_confirmation.md`; `phase3_raw_micro_fetch_evidence.json`; local file metadata                                                                     |
| Low      | GitNexus live tool verification unavailable in this Codex session.                                | This PH-B3 audit did not run live GitNexus `query()` / `impact()` / `detect_changes()` and therefore cannot strengthen conclusions with fresh graph queries. The conclusion relies on frozen local index facts and file evidence.                                                                                                                                    | `research/gitnexus-audit-summary.md`; MCP resource listing returned `[]`                                                                                            |

## GitNexus 可用性限制

`research/gitnexus-audit-summary.md` records the frozen local GitNexus index at commit `43ce2ae65a262f35e8e2790b0db54cc91b0765d1`, indexed `2026-06-21T14:52:54.293Z`, with 6263 symbols, 10281 relationships, and 276 execution flows.

In this Codex session, GitNexus MCP resources are not exposed (`list_mcp_resources` returned an empty list). The recorded audit summary also says `node .gitnexus/run.cjs status` resolved to `npx` and failed under the network sandbox with npm registry `EACCES`, so live `query()` / `impact()` / `detect_changes()` calls are unavailable. This PH-B3 result is therefore a file-evidence audit, not a live GitNexus graph audit.
