# 016F — Define Production-Equivalent Scale Benchmark

## Scope

Design/test-plan only. Do not change code.

## Inputs

- `scripts/production_equivalent_smoke.py`
- `docs/implementation_tasks/ROUND3_EARLY_CLOSE_PLAN.md`
- `docs/ops/data_sync_quick_reference.md`
- `docs/ops/db_inspect_cli.md`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`

## Required design updates

1. Define fixture-scale or snapshot-scale datasets for Round3 early verification.
2. Include SourceRoutePlan + capability + ResourceGuard in benchmark path.
3. Record equivalent items and non-equivalent items.
4. Use temporary DB / disposable resources only.
5. Preserve no-pollution cleanup rules.

## Future implementation tasks

- Extend `scripts/production_equivalent_smoke.py` to output scale metrics.
- Add benchmark thresholds for shard latency and memory/disk guard.
- Add tests only after user approves code/test changes.

## Acceptance commands

```bash
python scripts/production_equivalent_smoke.py
python -m pytest tests/test_resource_guard.py tests/test_vendor_fetch_e2e.py -q
```

## Residual risk

Real QMT/Yahoo/vendor latency is not covered without user authorization or a read-only staging/sandbox source.
