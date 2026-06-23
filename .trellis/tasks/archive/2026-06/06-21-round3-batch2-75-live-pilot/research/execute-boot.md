# Execute Boot — round3-batch2-75-live-pilot

> Mode: **inline** (主会话 Execute) · Plan frozen · task.py start done

## AC 摘要（来自 MASTER §2）

| Cluster   | Key AC                                                                       |
| --------- | ---------------------------------------------------------------------------- |
| AC-PRE    | Batch 2.5 staged + policy tests green (17 passed baseline)                   |
| AC-PM\*   | Phase -1 registry reconciliation; no R2b–R2d sprint mix                      |
| AC-P0     | Authorization file wired; fail-closed; QMT/Yahoo/FRED not default            |
| AC-P1     | Read-only baseline + capability snapshot; zero mutation                      |
| AC-P2     | Three-request route preview; READY gate; no fixture fallback                 |
| AC-P3     | Sandbox raw-only fetch; production DB unchanged; FRED primary stays deferred |
| AC-P4     | Validation on raw; no clean write default; conflict inspect                  |
| AC-P45    | Perf smoke or re-defer with owner/phase/closure_test                         |
| AC-P5/REG | Single PILOT\_\* state; registry sync; Batch 3 handoff                       |
| AC-GATE   | §9–§10 full green before Audit handoff                                       |

## implement.jsonl 全读确认

Phase 0 Boot **已 Read `implement.jsonl` 每一条**（50 条 manifest；Execute 必读 48 条 + MASTER inline + trellis-execute）。  
Read log: `execute-evidence/8.0-boot-reads.txt`（48 paths，排除 MASTER + trellis-execute）。  
Integration routing: `research/integration-ledger.md`（v3 pointer/inline map）。

## §8 执行顺序

```text
8.0 Boot → 8.1 Phase -1 → 8.2 Phase 0 → 8.3 Phase 1 → 8.4 Phase 2
→ 8.5a HITL → 8.5b Phase 3 fetch → 8.6 Phase 4 → 8.7 Phase 4.5 → 8.8 Closeout
```

Vertical slices: VS-1..VS-8 per `research/vertical-slices.md`.  
Audit gates: PH-B0..PH-B6 serial.

## Red Flags（来自 MASTER §7）

- Network failure → `PILOT_FAIL_SOURCE`; **no** fixture/staged fallback
- Request 3 success ≠ FRED live PASS (AC-P3-5)
- Production DB row count change → immediate FAIL + stop
- Same PR ingestion R2b–R2d split → sprint violation

## §10 验收命令清单

| Tier | Command                                                                                                                                                                                       |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A    | `uv run pytest tests/test_batch275_live_pilot_gate.py tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q` |
| B    | `uv run pytest tests/test_datasource_service.py tests/test_source_route_planner.py tests/test_ops_db_inspector.py -q`                                                                         |
| C    | `uv run pytest -q`                                                                                                                                                                            |
| D    | `uv run ruff check .` + `uv run ruff format --check .`                                                                                                                                        |
| E    | `uv run python -m compileall -q backend scripts tests`                                                                                                                                        |
| F    | `uv run python scripts/production_gate.py` + `uv run python scripts/check_doc_links.py`                                                                                                       |

Sandbox: `.audit-sandbox/batch275-live-pilot/` · Prod-path copy: `.audit-sandbox/batch275-prod-equiv/`

## GitNexus

- `research/gitnexus-execute-summary.md` — impact all LOW
- `research/context-closure.md` — upstream closure

## Phase 0 complete
