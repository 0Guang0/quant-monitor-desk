# Worktree slice — 022 Layer4 market structure

> Branch: `feature/round3-022-layer4-market` @ `555fd33b`

## Boundary（MAP §2.2）

- **allowed:** `backend/app/layer4_markets/**`, `tests/test_layer4_market_structure.py`, `tests/fixtures/layer4_staged_market/**`（如需）, task dir / execute-evidence
- **forbidden:** `backend/app/ops/staged_pilot.py`, `mutation_proof.py`, `backend/app/storage/staged_evidence.py`, registry trio（`AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED`）
- **production/data:** staged-only；不得声称 production-live

## Verification（MAP §2.2）

```bash
uv run pytest tests/test_layer4_market_structure.py -q
uv run pytest tests/test_batch3_staged_downstream_gate.py -q
```

## Merge gate

Playbook §8.2 全行 + §6 通用清单；Audit PASS；C-20 Audit 串行完成后本分支 Audit。
