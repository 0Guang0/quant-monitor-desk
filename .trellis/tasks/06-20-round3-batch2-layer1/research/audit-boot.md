# Audit Boot — 06-20-round3-batch2-layer1

> Execute 交接上下文；Audit **必读** 避免缺上下文。

## Execute 必读已读（对照 implement.jsonl + 8.0-boot-reads）

- `MASTER.plan.md` §0–§12、§2 AC 表
- `research/execute-boot.md` — AC 摘要、Red Flags、§10 命令
- `research/integration-ledger.md` — v3 pointer/inline 路由
- `research/execute-evidence/` — §8 RED/GREEN 全步证据
- `specs/contracts/layer1_axis_contract.yaml` — indicator 字段、forbidden terms、quality_flags
- `specs/contracts/snapshot_lineage_contract.yaml` — lineage 必填字段 + validation_tests
- `docs/modules/layer1_global_regime_panel.md` — §6 DDL、§7 窗口、§13 验收清单
- `backend/app/layer1_axes/` + `011_layer1_tables.sql` — 实现面
- Batch 1 + R2.6 gate audit.report — AC-PRE

## Execute 交接验证

- `validate-execute-handoff` → exit 0（2026-06-20）
- Tier B：`pytest -q`、cov≥85、ruff、production_gate、check_doc_links → PASS（见 `execute-evidence/8.6-final-gates.txt`）

## Audit 环境

- `AUDIT_PROD_ROOT`: `.audit-sandbox/r3b2-audit-prod-equiv`
- A5/A7/A8 sandbox：`QMD_DATA_ROOT=.audit-sandbox/r3b2-audit/data`
- 项目 DB 只读复跑：`data/duckdb/quant_monitor.duckdb`（hash 前后一致）

## Phase 7.pre complete
