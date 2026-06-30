# R3-DCP-03 — Post-write inspect (E2 + F0)

## Summary

Close Wave 3 by binding **read-only post-incremental inspection** to the baostock product path: `DbInspector` row-count stability, `max(trade_date)` assertion, `market_bar_p0` health profile, and `qmd_ops db-inspect` CLI smoke.

## Acceptance criteria

See live card `R3_DCP_03_POST_WRITE_INSPECT.md` §5.

## Dependencies

- R3-DCP-01 CLOSED @ `5dc71c0b`
- R3-DCP-02 CLOSED @ `5d8d7b0f`

## Plan artifacts

- `research/plan-boot.md`
- `research/reference-adoption-dcp03.md`
- `research/architecture-dcp03.md`
- `DEBT.plan.md`

## Next gate

Plan-Audit → Execute per `DEBT.plan.md` S01–S03.
