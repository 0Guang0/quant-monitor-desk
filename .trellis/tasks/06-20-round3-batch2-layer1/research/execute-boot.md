# Execute Boot — 06-20-round3-batch2-layer1

## AC 摘要（来自 MASTER §2）

| ID              | 摘要                                         |
| --------------- | -------------------------------------------- |
| AC-PRE          | Batch1 + R2.6 gates PASS；基线 pytest green  |
| AC-017-1..8     | 五轴 loader + guardrails + migration 011     |
| AC-018-1..6     | feature/interpretation 快照 + no_future_data |
| AC-WRIT-1       | WriteManager + DbValidationGate 写入         |
| AC-RES-1        | ResourceGuard eco 在 feature engine          |
| AC-LINEAGE-1..4 | axis_snapshot_lineage + 契约三名测试         |
| AC-GATE         | §9–§10 Tier A/B green                        |

## §8 执行顺序

1. **8.0** Boot（本文件）→ 2. **8.1** migration 011 → 3. **8.2** AxisSpecLoader → 4. **8.3** FeatureEngine → 5. **8.4** Interpretation → 6. **8.5** Lineage+WM → 7. **8.6** Final gates

**模式:** inline（主会话 Execute）

## Red Flags（来自 MASTER §7）

- FORBIDDEN 指标不得进入 observation
- 历史不足不得伪造 z-score
- interpretation 禁止买卖信号词
- 禁止 as_of 之后数据
- 禁止绕过 WriteManager
- 禁止 docs/specs 写运行时代码
- 禁止无界全历史 rolling

## §10 验收命令清单

**Tier A（每步 GREEN）：**

```bash
uv sync --locked
uv run pytest tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py -q
uv run ruff check backend/app/layer1_axes tests/test_layer1_axis_loader.py tests/test_layer1_interpretation.py
```

**Tier B（§8.6）：**

```bash
uv sync --locked
uv run pytest -q
uv run pytest -q --cov=backend --cov-fail-under=85
uv run ruff check .
uv run ruff format --check .
uv run python scripts/production_gate.py
uv run python scripts/check_doc_links.py
uv run python -m compileall -q backend scripts tests
```

## Boot reads

- `implement.jsonl`: 55/55 条已读 → `execute-evidence/8.0-boot-reads.txt`
- `integration-ledger.md`: pointer 项按 extract/for 补读
- GitNexus: `research/gitnexus-execute-summary.md`
- L2 闭包: `research/context-closure.md`

## Phase 0 complete
