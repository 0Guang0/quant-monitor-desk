# GitNexus Summary — R3-DCP-10 Plan Phase 1b

> **日期：** 2026-07-02  
> **repo：** quant-monitor-desk

## 1a Query — layer5 provenance

**命中：** `Layer5LineageBuilder.build` · `EvidenceFoundationValidator` · `test_layer5_evidence_foundation.py` · `cn_market_bundle_layer5_provenance` · Layer1/3 ingestion provenance 先例。

**结论：** Layer5 foundation/lineage **已实现**；缺口在 fetch→provenance **e2e 绑定**，非新 snapshot writer。

## 1b Impact — `Layer5LineageBuilder`

| 项 | 值 |
| --- | --- |
| target | `Layer5LineageBuilder.build` |
| direction | upstream |
| risk | **LOW** |
| direct callers | tests + 未来 evidence builder（尚无 production writer） |

**Execute 警告：** 若改 `SourceProvenance` dataclass → 影响 `foundation.py` / `lineage.py` / 全部 layer5 tests；优先 **extend helper** 而非改契约字段。

## 1b Impact — `bundle_layer5_provenance`

GitNexus 未索引 symbol 名；手工 trace：

| caller | 文件 |
| --- | --- |
| `cn_market_bundle_layer5_provenance` | `cn_market.py` |
| adapter replay tests | `tests/test_cn_market_*` |

**风险：** LOW — 扩展返回值不影响现有 caller（additive `source_dataset_ids`）。

## 建议 Execute 顺序

1. 扩展 `bundle_layer5_provenance`（schema_hash → dataset id）
2. 新增 `layer5_evidence/provenance.py` 或等价 helper（ponytail：单文件桥接）
3. e2e 测 — 不改 orchestrator 核心

## detect_changes 基线

Plan 阶段无代码变更；Execute 每切片 GREEN 后跑 `detect_changes({scope: "compare", base_ref: "master"})`。
