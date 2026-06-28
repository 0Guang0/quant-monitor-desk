# Execute skill evaluation — R3H-02

Skills recorded in `execute-skill-reads.jsonl`:

- **trellis-execute:** Phase 0 boot; §9.0–9.8 RED/GREEN per `EXECUTION_INDEX.md` §1; evidence in `research/execute-evidence/`
- **test-driven-development:** Each slice RED FAIL → minimal GREEN PASS before next step
- **incremental-implementation:** Vertical order 9.0→9.8; full `pytest -q` after every GREEN
- **karpathy-guidelines:** Reuse `market_data`/`crypto_market` SSOT; mirror `fred_port` patterns; mock-first ports
- **testing-guidelines:** Five-field docstrings on all new tests; purpose unchanged across fixes

Ponytail: shared OHLCV normalizer; separate crypto_market; registry batch at 9.6 only; yahoo validation-only preserved.
