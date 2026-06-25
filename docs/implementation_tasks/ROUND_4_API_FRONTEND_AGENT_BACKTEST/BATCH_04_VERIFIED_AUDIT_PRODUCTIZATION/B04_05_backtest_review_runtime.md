# B04_05 — Backtest and Review Runtime

> Owns: `VR-BT-001`.  
> Roadmap: Round 4.5.  
> Suggested branch: `feature/round4-backtest-review-runtime`.  
> Parallel: can run after Layer5/schema status is clear; do not mix with production write work.

---

## Goal

Move backtest/review from docs/schema-only capability to a minimal read-only runtime with ResourceGuard and no-action semantics.

## Scope

- Implement minimal scenario registry/loader and read-only review runner.
- Support 1–2 narrow event-study or evidence-chain-review scenarios.
- Write traceable `backtest_run_log` / `backtest_report` only through sanctioned paths.
- Reserved backtest types return `DEFERRED_BACKTEST_TYPE`.
- Add no-lookahead, window-boundary, no-action, and ResourceGuard tests.

## Forbidden scope

- No trading advice.
- No order simulation claiming live trading readiness.
- No broad historical scan.
- No direct DB write outside approved backtest/report writer.

## Gates

```bash
uv sync --locked
uv run pytest tests/test_backtest_review.py tests/test_no_action_semantics.py -q
uv run ruff check backend/app tests
```

## Done criteria

- `VR-BT-001` resolved or precisely re-deferred.
- At least one backtest/review type has runtime + tests + report artifact.
- Unimplemented types are visibly deferred, not shown as runnable.
