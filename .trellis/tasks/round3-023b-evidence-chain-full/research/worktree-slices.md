# Worktree slice — B01-023 full Layer5 evidence chain

> Branch: `feature/round3-023b-evidence-chain-full`  
> Worktree: `../quant-monitor-desk-wt-023-layer5`  
> Merge track: **Track B**（不得与 Batch 01 六卡混 PR）

## Boundary（playbook §2.5 / §2.6 / manifest Wave D）

| 类 | 路径 |
| --- | --- |
| **allowed** | `backend/app/layer5_evidence/**`、`specs/contracts/layer5_evidence_contract.yaml`、`tests/test_layer5_evidence_chain.py`、`tests/test_layer5_evidence_foundation.py`（回归）、`tests/fixtures/layer5_staged_evidence/**`（如需）、task dir / execute-evidence、`docs/adr/ADR-023-layer5-conflict-review-path.md` |
| **forbidden** | live fetch、`ops/staged_pilot.py` 主体、`storage/staged_evidence.py`、registry 三件套直接 commit、`layer3_chains/**` / `layer4_markets/**` 写（只读上游）、production DB mutation |
| **read-only 上游** | `backend/app/layer3_chains/**`、`backend/app/layer4_markets/**`、`backend/app/core/snapshot_lineage.py` |

## Verification（playbook §8.4）

```bash
uv sync --locked
uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q
uv run pytest -q && uv run ruff check . && uv run python -m compileall backend scripts tests
```

## Merge gate

- §16：`022` + L3/L4 集成稳定；全量 pytest 绿
- Track B 单独 integration/merge；不占 Batch 01 Audit 串行队列
- Audit A1–A8 + 对抗性零遗留后主会话提交
- registry 闭合：**主会话批处理**（本分支仅 proposed delta）
