# Execute Session Entry — Round 3 Batch 2.75

> **下一会话入口。** Plan 已冻结、对抗性审计已清零、`task.py start` 已完成。  
> **本提交为 Execute 前回滚点** — 业务代码（`live_pilot.py`、gate tests）尚未创建。

## 立即执行（Phase 0 Boot）

```text
1. MUST Read .cursor/skills/trellis-execute/SKILL.md
2. MUST Read MASTER.plan.md §0.3 + implement.jsonl 全表（50 条）+ integration-ledger.md
3. GitNexus impact() on symbols you will edit (service.py, new live_pilot.py)
4. 产出 research/execute-boot.md（含 Phase 0 complete）
5. 产出 research/execute-skill-reads.jsonl
6. python .trellis/scripts/task.py validate-execute-boot .trellis/tasks/06-21-round3-batch2-75-live-pilot
7. 进入 §8.0 → §8.1 → … → §8.8（严格 RED→GREEN，一步一勾）
```

## 任务路径

| 项              | 路径                                                     |
| --------------- | -------------------------------------------------------- |
| Task dir        | `.trellis/tasks/06-21-round3-batch2-75-live-pilot`       |
| MASTER          | `MASTER.plan.md`                                         |
| Tests design    | `research/batch275-live-pilot-gate-tests.md`             |
| Vertical slices | `research/vertical-slices.md`                            |
| Authorization   | `docs/quality/batch275_user_authorization_2026-06-21.md` |
| Evidence dir    | `execute-evidence/`（本任务目录下）                      |

## AC-PRE 基线（提交前已绿）

```bash
uv sync --locked
uv run pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py tests/test_round3_audit_registry_alignment.py -q
```

结果：17 passed（2026-06-21 前置会话记录）。

## §8 第一步 RED 提示

| 步  | RED 要点                                                           |
| --- | ------------------------------------------------------------------ |
| 8.0 | `research/execute-boot.md` 不存在 → fail                           |
| 8.1 | `test_livePilot_phaseMinus1_registryReconciliationRequired` → fail |
| 8.2 | `test_livePilot_missingAuthorization_blocksBeforeFetch` → fail     |

## 硬约束（勿违反）

- 禁止复用 Batch 2.5 `ingestion.py` / staged fixture 作为 live 证据
- 禁止写 production `quant_monitor.duckdb`
- §8.5a HITL 先于首次网络 fetch
- 同 sprint 禁止 ingestion R2b–R2d
- 勿 `finish-work` — 交接 Audit PH-B0–B6

## 回滚

若 Execute 造成重大破坏，回滚至本提交（Plan 冻结点）：

```bash
git log -1 --oneline   # 应见 plan freeze commit
git restore --source=<that-commit> -- backend/ tests/ execute-evidence/
```
