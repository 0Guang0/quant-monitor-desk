# Worktree slice — B-19 staged pilot v2

> 协调者锁定 · `feature/round3-real-data-staged-pilot-v2`

## Boundary

**Allowed**

- `backend/app/ops/staged_pilot.py`, `staged_pilot_fetch_ports.py`, `mutation_proof.py`
- `backend/app/datasources/**` — 仅 §8 RED 暴露的窄修复（须 evidence 注明路径）
- `backend/app/storage/**` — 同上
- `tests/test_staged_pilot.py`, `tests/test_vendor_fetch_e2e.py`, `tests/test_production_live_pilot_policy.py`
- `.trellis/tasks/06-24-round3-real-data-staged-pilot-v2/execute-evidence/**`

**Forbidden**

- `backend/app/layer2_sensors/**`, `layer3_chains/**`, `layer4/**`, `layer5/**`
- registry trio 大规模改写
- `data/duckdb/quant_monitor.duckdb` 直接写
- production-live 声称

**Merge gate:** MASTER §10 Tier A + §8.10 Tier B
