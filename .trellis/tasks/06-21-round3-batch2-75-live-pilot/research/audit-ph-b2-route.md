# PH-B2 Route Preview Audit

## 结论

FAIL

Phase 2 happy-path route matrix exists and records three authorized requests as READY with ResourceGuard snapshots and zero-mutation proof. However, PH-B2 cannot be marked PASS because the batch-local gate evidence for "no fixture fallback" is incomplete, and the planned route-not-ready batch test listed in the test design is absent from `tests/test_batch275_live_pilot_gate.py`.

## B2 Checklist

| Item                               | Verdict                             | Evidence                                                                                                                                                                                                              | Notes                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B2-1 三请求 route preview JSON     | PASS                                | `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase2_route_preview_matrix.json`                                                                                                                  | `previews` contains `pilot-req-1`, `pilot-req-2`, `pilot-req-3`; all preserve request payload, auth path, `dry_run=true`.                                                                                                                                                                                                                            |
| B2-2 每请求 `route_status` 记录    | PASS                                | same matrix                                                                                                                                                                                                           | Each preview has `route_plan.route_status="READY"` and `explicit_source_route_status="READY"`. Request 2 is validation-source READY via candidate status while primary route selection remains baostock.                                                                                                                                             |
| B2-3 ResourceGuard 决策快照        | PASS                                | same matrix; `backend/app/ops/live_pilot.py`; `tests/test_batch275_live_pilot_gate.py`                                                                                                                                | Matrix records `resource_guard_decision="OK"` and `resource_guard_reason=""` per request. Code calls `DataSourceService.check_resource_guard()` before preview; phase2 test asserts guard fields.                                                                                                                                                    |
| B2-4 非 READY 停止码证据（若失败） | N/A for actual matrix; COVERAGE GAP | matrix; `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/batch275-live-pilot-gate-tests.md`; `tests/test_source_route_planner.py`; `tests/test_datasource_service.py`                                       | The three audited requests are all READY, so no failure artifact is expected for this run. But the batch test design lists `test_livePilot_routeNotReady_blocksBeforeFetch`, and that batch-local test is absent. Generic route/service tests cover non-READY statuses, but PH-B2 lacks direct Batch 2.75 stop-code evidence.                        |
| B2-5 无 fixture fallback           | FAIL                                | `backend/app/ops/live_pilot.py`; `backend/app/ops/live_pilot_fetch_ports.py`; `tests/test_batch275_live_pilot_gate.py`; `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/batch275-live-pilot-gate-tests.md` | Code rejects `StubFetchPort` and `LocalFixtureFetchPort`, and live fetch ports are real vendor ports. The only batch gate test asserts `StubFetchPort` rejection; the planned `test_livePilot_noFixtureFallbackSatisfiesEvidence` is absent and there is no explicit LocalFixtureFetchPort/staged-service fallback test in the Batch 2.75 gate file. |

## Evidence Paths

- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/AUDIT.plan.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/audit.jsonl`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/gitnexus-audit-summary.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase2_route_preview_matrix.json`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/8.4-red.txt`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/8.4-green.txt`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/batch275-live-pilot-gate-tests.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/original-plan-trace.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/integration-ledger.md`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `backend/app/datasources/service.py`
- `backend/app/ops/live_pilot.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `tests/test_batch275_live_pilot_gate.py`
- `tests/test_source_route_planner.py`
- `tests/test_datasource_service.py`

## Findings

### P1 — B2-5 fixture fallback gate evidence is incomplete

The implementation rejects both `StubFetchPort` and `LocalFixtureFetchPort` in `_assert_live_fetch_port`, and the live port factory returns real baostock/akshare ports. But the Batch 2.75 gate test only exercises `StubFetchPort`. The planned test name `test_livePilot_noFixtureFallbackSatisfiesEvidence` from the task-local test design is not present, and there is no explicit Batch 2.75 assertion that `LocalFixtureFetchPort` or `build_staged_fixture_service` cannot satisfy live pilot evidence.

Impact: a staged fixture fallback regression would not be caught by the named Batch 2.75 gate as planned. This blocks PH-B2 PASS.

### P2 — Batch-local route-not-ready stop-code test is missing

`source_route_contract.yaml` defines non-READY statuses and `datasource_service` tests cover `USER_AUTH_REQUIRED` / `RESOURCE_GUARD_PAUSED` / disabled outcomes generically. The Batch 2.75 test design, however, explicitly lists `test_livePilot_routeNotReady_blocksBeforeFetch`, and `tests/test_batch275_live_pilot_gate.py` does not contain it. The current Phase 2 matrix has all three requests READY, so no failure artifact is required for this run, but AC-P2-2 remains under-evidenced at the Batch 2.75 gate level.

Impact: lower than P1 because generic route/service coverage exists and actual matrix is READY, but the promised batch-specific stop-code proof is missing.

## GitNexus 可用性限制

Live GitNexus MCP resources were not exposed in this Codex session. The audit used the frozen local index summary in `research/gitnexus-audit-summary.md`: indexed at `2026-06-21T14:52:54.293Z`, commit `43ce2ae65a262f35e8e2790b0db54cc91b0765d1`, graph size 6263 symbols / 10281 relationships / 276 flows. `query()`, `impact()`, and `detect_changes()` were not available as live calls, and `node .gitnexus/run.cjs status` failed under the network sandbox. Therefore this PH-B2 verdict is based on frozen GitNexus facts plus direct source/evidence reads, not live graph queries.
