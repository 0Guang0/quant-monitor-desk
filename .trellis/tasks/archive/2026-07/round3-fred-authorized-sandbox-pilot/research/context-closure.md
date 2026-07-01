# Context closure — B01-FRED

## Upstream wiring

- `staged_pilot.py` / `live_pilot_constants.py` — FRED deferred note + disabled pilot source pattern
- `SourceRoutePlanner` + registry/capability YAML — fred `macro_series` domain (disabled-by-default)
- Layer1 axis specs + `R3D_model_input_whitelist.md` — P0 series SSOT (WL 未合并只读回退)
- `implement.jsonl` 51 entries + MASTER §9 vertical slices

## Deferred upstream

- `data_health.py` v2 profiles — **B01-DH2** (pilot-local `fred_evidence_validator` only)
- `specs/model_inputs/**` — **B01-WL**
- production clean write / production-live FRED claim
- registry 三件套 commit — coordinator Track A #3 merge gate

## Slice boundary

- sandbox/raw-only; `fred` disabled-by-default; caps ≤5 series / ≤100 rows / ≤10 calls
- `B2.5-O-05` **CLOSED (RE-DEFERRED)** — owner Batch 6 coordinator; phase live FRED primary; closure test `test_b250o05_reDeferred_closureRowClosed` + `test_fred_staged_semantics.py` (see `research/b01-fred-audit-closures.md`)
- `FRED-07` **CLOSED-SKIP-OPT-IN** — no `FRED_API_KEY` in default env; `authorization.yaml` present; closure test `test_fred07_liveFetch_closureClosedSkipOptIn_withoutApiKey`
