# R3FR-04: JQ2PTrade/EasyXT Round4 backtest adoption plan

## Goal

Rewrite Round4 backtest/review planning so the first implementation batch is executable with JQ2PTrade/EasyXT-informed QMD-owned slices — **planning/docs/contracts only**, no backend runtime in 3F-R.

## Acceptance criteria

- [x] **A** `B04_05_backtest_review_runtime.md` carries three-batch ceiling (A/B/C), slice A–E **Not done if**, and R3FR-04 landing detail
- [x] **B** `backtest_*` + `review_sandbox_contract.yaml` align with R3FR-04 reference paths and forbidden API semantics
- [x] **C** `tests/test_reference_adoption_guardrails.py` includes R3FR-04 closure + `test_jq2ptradeExecPatternNotCopied`
- [x] **D** `BATCH_3FR_TASK_CARD_MANIFEST.md` marks R3FR-04 Done; `loop_maintain.py` + guardrails pytest green

## Evidence

```bash
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run python scripts/loop_maintain.py
```

## Notes

- Track: **debt-lite** (planning-only; same posture as R3FR-01)
- Branch: `docs/round4-reference-backtest`
- No `backend/app/review/**` in this slice
