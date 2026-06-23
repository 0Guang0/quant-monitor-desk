# Worktree slice — 021 Layer3 snapshot builder

> Branch: `feature/round3-021-layer3-snapshot`

## Boundary

- **allowed:** `backend/app/layer3_chains/**`, `tests/test_layer3_snapshot_builder.py`, `tests/fixtures/layer3_l5_staged_bars/**`, task dir
- **forbidden:** layer2/4/5 runtime, datasources live fetch, lineage contract write, `docs/AUDIT_DEFERRED_REGISTRY.md`, `docs/UNRESOLVED_ISSUES_REGISTRY.md`, production DB
- **production/data:** staged-only

## Merge gate

Tier A + batch3 gate + Audit PASS；§3.2 defer 边界未被越界关闭。
