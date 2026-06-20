# Grill-Me Session — Round 3 Batch 2 Layer 1

> Phase 3 · 2026-06-20

## 质问与回答（摘要）

### Q1: 本批是否要实现全量 Layer1 数据抓取？

**A:** 否。`017`/`018` 范围是 spec loader + 快照引擎。生产抓取由 `data_sync_orchestrator` / 未来 `Layer1AxisUpdateJob` 承担；本批测试用 **fixture observations**，不默认 live FRED/QMT。

### Q2: axis 表不在 schema.sql / migrations 中，谁权威？

**A:** `layer1_global_regime_panel.md` §6 DDL + 新 migration `011_layer1_tables.sql`。`schema.sql` 后续 Round 可对齐；本批以 migration + contract test 为准。

### Q3: lineage consumer 具体交付什么？

**A:** 快照元数据对象实现 `snapshot_lineage_contract.yaml` 全部 `required_fields`；从 `validation_report`（含 `rule_version`, `source_fetch_ids_json`）或测试 stub 填充；`test_snapshotRejectsFutureInput` 等三名契约测试落地。

### Q4: 路径 `backend/layers/` vs `backend/app/layer1_axes/`？

**A:** 以 `MIGRATION_MAP.md` 为准；任务卡路径记为 **obsolete path**。

### Q5: 本批能否改 WriteManager？

**A:** 尽量避免。若 snapshot 写入需要新 `write_mode` 或 staging 表名，须最小 diff + impact 分析；优先复用现有 gate + staging 模式。

### Q6: INSUFFICIENT_HISTORY 如何验收？

**A:** 测试注入窗口不足 observation 序列 → `state_bucket=insufficient_history`，`z_score`/`percentile_rank` 为 NULL，quality_flags 含 `INSUFFICIENT_HISTORY`。

### Q7: 禁止动作语义如何验收？

**A:** interpretation 输出扫描 `layer1_axis_contract.yaml` `forbidden_output_terms`；命中则 `needs_human_review=true` 或拒绝写入（按设计 §10）。

## §7 Red Flags 增补

| Flag                         | 处置               |
| ---------------------------- | ------------------ |
| 在 Layer1 实现 live 全网抓取 | 停止 — 超出批范围  |
| 伪造 z-score 当历史不足      | AC-018-2 必须 FAIL |
| Layer2 回写 Layer1           | 测试阻断           |
| docs/specs 写 Python         | GLOBAL 边界        |

## 结论

范围清晰：migration + loader + feature + interpretation + lineage envelope。无用户决策待重开（D-09 已拍板）。
