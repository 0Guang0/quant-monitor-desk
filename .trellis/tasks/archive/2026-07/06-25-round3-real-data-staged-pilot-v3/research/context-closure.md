# Context closure — B01-SP3 staged pilot v3

## Upstream wiring

- v2 `staged_pilot.py` orchestration + `staged_pilot_fetch_ports.py` fetch ports
- B01-WL `specs/model_inputs/**` merged; WL loader drives v3 request set (not v2 hardcoded envelopes)
- `integration-ledger.md` + `context_pack.json` route ops/datasources/validators/storage authorities
- PROMPT_14 authorization + sandbox WriteManager path unchanged
- Reuse `validators/data_quality.py` and `validators/source_conflict.py` for AC-SP3-02..05

## Deferred upstream

- production clean write / sandbox rehearsal (`production_clean_write: false` in closeout)
- registry 三件套 direct commit (主会话 merge coordinator)
- FRED/TDX/QMT/Yahoo live production fetch
- `data_health.py` CLI (Batch 01 out-of-scope)

## Slice boundary

- staged-only; `production_live_readiness_claim: false` mandatory in closeout
- akshare validation-only; cninfo metadata-only; no PDF bulk
- evidence under `execute-evidence/`; registry output is **proposed delta** only
