# Project overview — Layer5 evidence chain (Plan 1a)

## 模块位置

`backend/app/layer5_evidence/` — Round 3 Batch 5 Layer 5；上游 Layer3 `layer3_chains/`、Layer4 `layer4_markets/`（只读引用 snapshot/lineage 模式）。

## 现状（023A 已交付）

- `foundation.py` — evidence identity、provenance、manual-review、agent-text-not-fact-source
- `models.py` — `EvidenceFoundationRecord`、`InstrumentEvidenceRef`、`SourceProvenance`
- `lineage.py` — `Layer5LineageBuilder`（contract 字段集）
- `test_layer5_evidence_foundation.py` — 五字段 docstring + 业务断言

## 本任务增量

| 组件                                       | 说明                                                      |
| ------------------------------------------ | --------------------------------------------------------- |
| `instrument_registry.py`                   | contract `instrument_registry` 行校验与唯一性             |
| `evidence_models.py`（或扩展 `models.py`） | security_bar / event / financial / valuation 行类型       |
| `evidence_chain.py`                        | builder：组装 layer1–5 context 槽 + upstream snapshot ids |
| `test_layer5_evidence_chain.py`            | 全链 staged fixture 测试                                  |

## GitNexus 关注面

- `EvidenceFoundationValidator` — 023A 基线；chain builder 须复用而非分叉
- `Layer3SnapshotBuilder` / `MarketStructureBuilder` — upstream_snapshot_ids 引用模式
- blast radius：仅 `layer5_evidence/**`；禁止改 L3/L4 实现

## 合并轨

Wave D **Track B** — 与 Batch 01 协调包分轨合并（playbook §7.3）。
