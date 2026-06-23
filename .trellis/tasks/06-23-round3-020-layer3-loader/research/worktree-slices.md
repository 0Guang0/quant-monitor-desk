# Repair/Debt Lite / Wave-A Slice — 020 Layer3 loader

> 协调者锁定 · 见主仓 `.trellis/workspace/Guang/round3-wave-a-slice-plans.md`

## Source of truth

- audit / registry ID: formal task `020` / Batch 4
- base branch: `master` @ `61436a51`
- target branch: `feature/round3-020-layer3-loader`
- owner agent: `implement-agent-020`
- worktree: `../quant-monitor-desk-wt-020-layer3-loader`

## Boundary

- allowed: `backend/app/layer3_chains/**`, `tests/test_layer3_loader.py`, `tests/fixtures/layer3_*`, task dir
- forbidden: layer2/4/5 runtime, datasources/db/ops/validators, lineage contract write, registries, production DB
- production/data: staged-only; WriteManager if sandbox write

## Merge gate

见 slice plan §Verification；Audit 后 `audit_matrix.json`。
