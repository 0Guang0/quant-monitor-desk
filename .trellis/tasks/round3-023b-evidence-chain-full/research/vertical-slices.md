# Vertical slices — 023b full Layer5 evidence chain (Plan 3.5 / to-issues)

> 冻结为 MASTER §8；每切片独立 RED/GREEN + `execute-evidence`。

| 序 | ID | Roadmap | 交付物（完标准） | 依赖 | AC |
| --- | --- | --- | --- | --- | --- |
| 0 | SLICE-BOOT | — | implement.jsonl 全读 + ledger；`test_layer5_evidence_chain.py` 骨架；基线 pytest | §16 gate | — |
| 1 | SLICE-REGISTRY | `R3D-023-01` | `instrument_registry.py` + registry 唯一性；延续 023A `InstrumentEvidenceRef` | SLICE-BOOT | AC-023-1 |
| 2 | SLICE-MODELS | `R3D-023-02` | bar/event/financial/valuation 行类型 + staged validator；no-future-data | SLICE-REGISTRY | AC-023-2 |
| 3 | SLICE-CHAIN | `R3D-023-03` | `evidence_chain.py` builder：L3/L4 upstream_snapshot_ids + layer context 槽 | SLICE-MODELS | AC-023-3 |
| 4 | SLICE-CONFLICT | `R3D-023-04` | `docs/adr/ADR-023-layer5-conflict-review-path.md` + severe→queued pytest | SLICE-CHAIN | AC-023-4 |
| 5 | SLICE-PORT | `R3D-023-05` | 条件：`EvidenceReadPort` Protocol + fake impl 测边界；或 ADR re-defer `R2-RISK-2` | SLICE-CHAIN | AC-023-5 |
| 6 | SLICE-GATES | — | contract 增补 + Tier A/B + playbook §8.4 + `validate-execute-handoff` | SLICE-CONFLICT, SLICE-PORT | AC-023-6 |

→ MASTER §8 序 0–6 ↔ §9.0–9.6（1:1）
