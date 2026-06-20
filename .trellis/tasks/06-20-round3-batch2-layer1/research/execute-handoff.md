# Execute Handoff — Round 3 Batch 2 Layer 1

> **用户已批准 Plan 冻结** · 下一会话 **直接 Execute**，勿重跑 Plan / 对抗审计。

## 状态

| 项                 | 值                                                                 |
| ------------------ | ------------------------------------------------------------------ |
| Task slug          | `06-20-round3-batch2-layer1`                                       |
| `task.json.status` | `in_progress`（`task.py start` 后）                                |
| Plan freeze        | `validate-plan-freeze` exit 0                                      |
| 前置 gate          | Batch 1 archived PASS；R2.6 contract + routing gates archived PASS |
| 工作分支（建议）   | `06-20-round3-batch2-layer1` off `master`                          |

## 开场（复制）

```text
进入 Execute。MUST Read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot（§0.3 implement.jsonl 全读 55 条 + integration-ledger）→ §8.x → §9/§10 → §11 Audit。勿 finish-work。
```

## 第一步（§8.0 Boot — 尚无业务代码）

1. **Read** `.cursor/skills/trellis-execute/SKILL.md` Phase 0
2. GitNexus `query` + 将改 symbol 的 `impact()` → `research/gitnexus-execute-summary.md`
3. L2 闭包 → `research/context-closure.md`
4. **Read 全文** `MASTER.plan.md` §0–§12；**Read `implement.jsonl` 每一条**（55 行）
5. Read `research/integration-ledger.md`；按 extract/for 补读 pointer 原稿
6. 跑 **§8.0 RED**（须 FAIL — `execute-boot.md` 尚不存在）：

```bash
uv run python -c "import sys; from pathlib import Path; p=Path('.trellis/tasks/06-20-round3-batch2-layer1/research/execute-boot.md'); sys.exit(0 if p.is_file() else 1)"
```

7. 写 `research/execute-boot.md`（含 `Phase 0 complete`）+ `execute-skill-reads.jsonl`
8. `uv sync --locked` + 基线 `uv run pytest -q` → `execute-evidence/8.0-*`
9. `python .trellis/scripts/task.py validate-execute-boot .trellis/tasks/06-20-round3-batch2-layer1`

## §8 顺序（Boot 后）

| 步  | 内容                                       | 测试设计                                          |
| --- | ------------------------------------------ | ------------------------------------------------- |
| 8.1 | migration `011_layer1_tables.sql`          | MASTER §8.1                                       |
| 8.2 | AxisSpecLoader + guardrails (017)          | `research/layer1-axis-loader-tests.md`            |
| 8.3 | AxisFeatureEngine + feature snapshot (018) | `research/layer1-feature-interpretation-tests.md` |
| 8.4 | AxisInterpretationEngine (018)             | 同上                                              |
| 8.5 | Lineage consumers + WriteManager           | `research/layer1-lineage-tests.md`                |
| 8.6 | Tier A/B final gates                       | MASTER §9–§10                                     |

## 实现落点

- `backend/app/layer1_axes/` — axis_loader, guardrails, feature_engine, interpretation, lineage
- `backend/app/db/migrations/011_layer1_tables.sql`
- `tests/test_layer1_axis_loader.py`, `tests/test_layer1_interpretation.py`

## 禁止

- 读 `AUDIT.plan.md`（Audit 专用）
- `docs/`/`specs/` 写运行时代码
- 跨 §8 步批量实现；跳过 RED
- Execute 期间 `trellis-check`（Audit A1 替代）

## 关键契约

- `specs/contracts/layer1_axis_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/**` + `configs/layer1_axes.yml`
- 写入经 `DuckDBWriteManager` + `validation_report_id`

## 基线参考

`docs/ROUND3_HANDOFF.md`：master 上约 362 tests · cov≥85 · production_gate green（Execute 8.0 须复验）。
