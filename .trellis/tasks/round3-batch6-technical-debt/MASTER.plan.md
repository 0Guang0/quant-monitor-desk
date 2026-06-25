# Batch 3F hygiene / perf / ingestion split (B3F-HYG)

> Playbook: `BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.7 · Roadmap: `R3F-HYG-01..13`  
> Branch: `chore/round3-batch6-technical-debt` · Worktree: `../quant-monitor-desk-wt-b3f-hyg`

## Scope

- R3F-HYG-06: production-equivalent smoke threshold artifact (`VR-PERF-001`)
- R3F-HYG-07: ingestion PR-R2b `sandbox_bootstrap.py`; R2c/R2d via existing `ingestion_commit.py`
- R3F-HYG-08: ResourceGuard regression (verify-only)
- R3F-HYG-10: `fetch_port` boundary verify-only (existing tests)
- R3F-HYG-04/11/12/13: **out of branch** — MIG / REG / CI owners

## Must not own

- migration 列（B3F-MIG）
- live source / production clean write
- orchestrator handler registry（B3F-BR）

## Verification (Playbook §8.6)

```bash
uv sync --locked --extra dev
uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit --write-artifact .audit-sandbox/r3b275-audit/production_equivalent_smoke_budget.json
uv run pytest tests/test_resource_guard.py tests/test_production_equivalent_smoke_budget.py tests/test_layer1_sandbox_bootstrap.py -q
uv run pytest tests/test_layer1_observation_ingestion.py -q
uv run pytest -q
```

---

## 8. 实现步骤

### 8.1 HYG-PERF — smoke budget artifact

| 字段 | 内容 |
|------|------|
| RED | `tests/test_production_equivalent_smoke_budget.py` FAIL（模块缺失） |
| GREEN | `perf_budget.py` + `production_equivalent_smoke_budget.yaml` + `--write-artifact` |
| 已执行 | [x] |

### 8.2 HYG-R2B — sandbox_bootstrap

| 字段 | 内容 |
|------|------|
| RED | `tests/test_layer1_sandbox_bootstrap.py` FAIL |
| GREEN | `sandbox_bootstrap.py` + `ingestion_evidence` 接线 + rollback plan R2b DONE |
| 已执行 | [x] |

### 8.3 HYG-VERIFY — §8.6 playbook 命令

| 字段 | 内容 |
|------|------|
| GREEN | smoke + resource_guard + layer1 ingestion 全绿 |
| 已执行 | [x] |

---

## 11. Execute 交接 DoD

- [x] §8.1–8.3 证据齐
- [x] `validate-execute-handoff` exit 0
- [x] registry 仅 proposed delta（主会话批处理）
- [x] 未改 migration 列 / live source

---

## 12. Execute Skill 冻结

| Skill | 绑定 | 已执行 |
|-------|------|--------|
| trellis-execute | Boot | [x] |
| test-driven-development | §8 RED | [x] |
| incremental-implementation | §8 SLICE | [x] |
| karpathy-guidelines | GREEN | [x] |
| testing-guidelines | 写测 | [x] |
| trellis-implement | Execute | [x] |
