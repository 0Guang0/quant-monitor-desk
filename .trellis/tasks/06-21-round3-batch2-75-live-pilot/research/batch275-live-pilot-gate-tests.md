# Batch 2.75 Live Pilot Gate — Test Design (Plan 5b)

> Full tracer names in MASTER §8 RED/GREEN columns. No full `def test_*` bodies in MASTER.

## File: `tests/test_batch275_live_pilot_gate.py`

| Test                                                        | Asserts                                             |
| ----------------------------------------------------------- | --------------------------------------------------- |
| `test_livePilot_phaseMinus1_registryReconciliationRequired` | Phase -1 registry read artifact required            |
| `test_livePilot_missingAuthorization_blocksBeforeFetch`     | No authorization path → no fetch                    |
| `test_livePilot_disabledSource_blocksBeforeFetch`           | e.g. `qmt_xtdata` without auth                      |
| `test_livePilot_routeNotReady_blocksBeforeFetch`            | `route_status != READY`                             |
| `test_livePilot_enforcesSandboxDataRoot`                    | writes only under pilot sandbox                     |
| `test_livePilot_firstPassIsRawOnly`                         | no clean table writes                               |
| `test_livePilot_productionDbRowCountsUnchanged`             | mock/copy prod DB counts stable                     |
| `test_livePilot_noFixtureFallbackSatisfiesEvidence`         | StubFetchPort/staged service rejected for live mode |
| `test_livePilot_phase4Conflict_inspectOrNoConflict`         | conflict report or explicit no-conflict             |
| `test_livePilot_phase4Validation_noCleanWriteByDefault`     | no clean write default                              |
| `test_livePilot_preview_includesResourceGuardDecision`      | guard snapshot in preview payload                   |

## Regression (always)

```bash
uv run pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q
```

## Phase-specific

| Phase | Command                                                                         |
| ----- | ------------------------------------------------------------------------------- |
| -1/0  | gate tests RED → GREEN                                                          |
| 1     | `test_livePilot_phase1Baseline_readOnly`                                        |
| 2     | `test_livePilot_phase2RouteMatrix_threeRequests`                                |
| 3     | `test_livePilot_phase3RawOnly_*` (`@pytest.mark.slow` + `@pytest.mark.network`) |
| 4     | `test_livePilot_phase4Validation_*` + `test_livePilot_phase4Conflict_*`         |
| 4.5   | smoke script exit 0 or documented skip                                          |
| 5     | registry alignment tests green                                                  |

## phase45_perf_budget.json schema

```json
{
  "owner": "batch275-execute",
  "phase": "4.5",
  "status": "PASS|RE_DEFERRED",
  "closure_test": "scripts/production_equivalent_smoke.py --data-root .audit-sandbox/batch275-perf-smoke",
  "elapsed_seconds": 0,
  "notes": ""
}
```

- Assert `route_status`, `source_used`, `content_hash`, row counts, file paths — not only `called_once`.
- Evidence JSON must include `authorization_evidence` path and per-request `pilot_request_id`.
