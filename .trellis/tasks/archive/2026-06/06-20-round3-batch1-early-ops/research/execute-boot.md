# Execute Boot — 06-20-round3-batch1-early-ops

## AC 摘要（来自 MASTER §2）

| AC          | 摘要                                                 |
| ----------- | ---------------------------------------------------- |
| AC-PRE      | Round 2.6 gate archived PASS；基线 pytest green      |
| AC-CLI-1..5 | 只读 DbInspector + contract JSON shape + status 语义 |
| AC-DB-1,2   | 项目 data/ inspect 证据 + registry RESOLVED          |
| AC-DOC-1,2  | HANDOFF + EARLY_CLOSE_PLAN 文档更新                  |
| AC-E2E-1    | R3-PARTIAL-2 引用既有 E2E + full_load skeleton       |
| AC-BENCH-1  | production_equivalent_smoke 证据归档                 |
| AC-OPS-1    | R2.6-IMPL-8 保持 DEFERRED；无 --enable-qmt           |
| AC-GATE     | 全量 Tier A/B green                                  |

## §8 执行顺序

1. **8.0** Boot gate（本文件）
2. **8.1** DbInspector 核心 + tests
3. **8.2** `scripts/qmd_ops.py` transitional CLI
4. **8.3** Docs + registry + inspect JSON
5. **8.4** R3-PARTIAL-2 closure
6. **8.5** Prod-equivalent smoke 证据
7. **8.6** Final gates

## Red Flags（来自 MASTER §7）

- 禁止 writer/migration/network/QMT flags
- Phase A only — 无 source probe / data health
- scan_limited=true；eco profile 默认
- 每步 RED 先于 GREEN；禁止跨步批量编辑

## §10 验收命令清单

```bash
.venv/Scripts/python.exe -m pytest tests/test_ops_db_inspector.py -q
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe scripts/production_gate.py
.venv/Scripts/python.exe scripts/check_doc_links.py
```

## Phase 0 complete

Boot artifacts: `gitnexus-execute-summary.md`, `context-closure.md`, `execute-skill-reads.jsonl`, `research/execute-evidence/8.0-*`.

**implement.jsonl:** 全读 41 条（见 `research/execute-evidence/8.0-boot-reads.txt`）。
