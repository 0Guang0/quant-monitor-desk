# Context closure — R3G-01

## Upstream wiring

- `staged_pilot.py` — compose pattern, `DEFAULT_PRODUCTION_DB`, `_staged_conflict_check_summary` (read-only)
- `fred_sandbox_pilot.py` — authorization YAML semantics
- `data_health_profiles` / `DataHealthService` — per-source DH (market_bar_p0, staged_pilot_v3, fred_sandbox_pilot)
- `WriteManager` + `DbValidationGate` — sandbox clean write on `security_bar_smoke_clean`
- `implement.jsonl` 40 entries + frozen §9 + EXECUTION_INDEX §1–§3

## Deferred upstream

- R3G-02 adversarial audit — consumes rehearsal report (out of scope)
- R3G-03 limited production entry — **not opened**
- L1 ingestion write allowlist expansion — **forbidden**

## Slice boundary

- sandbox DB only; `production_mutation_allowed: false`
- candidates: baostock / cninfo metadata / authorized fred (max 3 series, 120d)
- FRED artifact: `.audit-sandbox/round3g/fred_user_authorization.yaml`
