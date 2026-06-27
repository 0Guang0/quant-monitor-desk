# GitNexus Execute Boot Summary — R3H-01

## query: official macro FRED evidence normalizer live pilot promote

Top processes:

- `capture_phase3_raw_evidence` (live_pilot_phase3.py) — live FRED evidence capture
- `capture_raw_and_staging_evidence` (staged_pilot.py)
- `run_live_pilot_raw_only` (live_pilot_phase3.py)

Related tests: `test_round3g_limited_production_clean_write.py`, `test_fred_staged_semantics.py`

## impact() — index stale for anchor symbols

| Target                              | Result             |
| ----------------------------------- | ------------------ |
| `materialize_fred_promote_evidence` | NOT FOUND in index |
| `_fred_staging_rows`                | NOT FOUND in index |
| `live_evidence_bridge.py`           | NOT FOUND in index |

**Grep fallback blast radius (9.1 edit targets):**

- `materialize_fred_promote_evidence` → `scripts/r3g03_isolated_pilot_dry_run.py`, `tests/test_round3g_limited_production_clean_write.py`
- `_fred_staging_rows` → `rehearsal_loader.py` promote path via `fred_evidence.json`
- New `official_macro.py` — greenfield (no index entry yet)

**Risk预判 (frozen §4.3):** MEDIUM when touching bridge/loader/live_pilot in 9.1.

**Recommendation:** Run `node .gitnexus/run.cjs analyze` before 9.1 edits; re-run impact on `materialize_fred_promote_evidence` and `_fred_staging_rows`.
