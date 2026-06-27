# Execute skill evaluation — R3H-01

Skills recorded in `execute-skill-reads.jsonl`:

- **trellis-execute:** Phase 0 boot; §9.0–9.8 RED/GREEN per `EXECUTION_INDEX.md` §1; evidence in `research/execute-evidence/`
- **test-driven-development:** Each slice RED FAIL → minimal GREEN PASS before next step
- **incremental-implementation:** Vertical order 9.0→9.8; full `pytest -q` after every GREEN
- **karpathy-guidelines:** Reuse `official_macro` SSOT; mirror `fred_port` / `us_treasury_port` patterns; no catch-all adapter
- **testing-guidelines:** Five-field docstrings on all new tests; purpose unchanged across fixes

Ponytail: one normalizer module; mock-first ports; registry batch only at 9.6.
